# filepath: /Users/trishit_debsharma/Documents/Code/Mechatronic/software_round2/drone_simulator/client.py
import asyncio
import json
import sys
import websockets
import time
from typing import Dict, Any, Optional
import logging
import numpy as np  # Import numpy

basealtitude = 150

class DroneClient:
    def __init__(self, uri: str = "ws://localhost:8765"):
        """Initialize the client."""
        self.uri = uri
        self.connection_id = None
        self.telemetry = None
        self.metrics = None
        self.start_time = time.time()
        self.command_count = 0
    async def connect(self) -> None:
        """Connect to the WebSocket server."""
        print(f"Attempting to connect to {self.uri}...")
        print("Make sure the server is running (python run_server.py)")

        try:
            # Configure ping_interval and ping_timeout properly
            async with websockets.connect(
                self.uri,
                ping_interval=20,
                ping_timeout=10,   # Wait 10 seconds for pong response
                close_timeout=5    # Wait 5 seconds for close to complete
            ) as websocket:
                # Receive welcome message
                response = await websocket.recv()
                data = json.loads(response)
                self.connection_id = data.get("connection_id")
                print(f"Connected with ID: {self.connection_id}")
                print(f"Server says: {data['message']}")
                await self.simulation(websocket)        

        except websockets.exceptions.ConnectionClosedError as e:
            print("\nThe connection was closed unexpectedly. Possible reasons:")
            print("- Server crashed or restarted")
            print("- Network issues causing ping timeout")
            print("- Server closed the connection due to inactivity")
            print(f"Error details: {e}")
    
    async def send_command(self, websocket, speed: int, altitude: int, movement: str) -> Optional[Dict[str, Any]]:
        """Send a command to the drone server and return the response."""
        try:
            data = {
                "speed": speed,
                "altitude": altitude,
                "movement": movement
            }
            self.command_count += 1
            data["command_count"] = self.command_count          
            
            await websocket.send(json.dumps(data))
            
            response = await websocket.recv()
            response_data = json.loads(response)
            
            # Check if the drone has crashed
            if response_data.get("status") == "crashed":
                crash_message = response_data.get('message', 'Unknown crash')
                
                print(f"\n*** DRONE CRASHED: {crash_message} ***")
                print("Connection will be terminated.")
                
                # Update metrics one last time
                if "metrics" in response_data:
                    self.metrics = response_data["metrics"]
                
                # Show final telemetry
                if "final_telemetry" in response_data:
                    self.telemetry = response_data["final_telemetry"]
                    self.display_status()
                
                print("\nFinal Flight Statistics:")
                print(f"Total distance traveled: {self.metrics.get('total_distance', 0)}")
                print(f"Successful flight iterations: {self.metrics.get('iterations', 0)}")
                print("\nConnection terminated due to crash")
                
                # Return None to indicate a crash occurred
                return None
            
            return response_data
            
        except websockets.exceptions.ConnectionClosed as e:          
            raise
            
        except Exception as e:
            return None

    def parse_telemetry(self, telemetry_str):
        # Parse the telemetry string format from the server
        # Format: X-{x}-Y-{y}-BAT-{bat}-GYR-[gx,gy,gz]-WIND-{wind}-DUST-{dust}-SENS-{status}
        parts = telemetry_str.split('-')
        telemetry = {}

        for i in range(0, len(parts), 2):
            if i+1 < len(parts):
                key = parts[i]
                value = parts[i+1]

                if key == 'X':
                    telemetry['x_position'] = float(value)
                elif key == 'Y':
                    telemetry['y_position'] = float(value)
                elif key == 'BAT':
                    telemetry['battery'] = float(value)
                elif key == 'GYR':
                    gyr_values = value.strip('[]').split(',')
                    try:
                        telemetry['gyroscope'] = [float(v) for v in gyr_values if v.strip()]
                    except ValueError:
                        telemetry['gyroscope'] = [0.0, 0.0, 0.0]
                elif key == 'WIND':
                    telemetry['wind_speed'] = float(value)
                elif key == 'DUST':
                    telemetry['dust_level'] = float(value)
                elif key == 'SENS':
                    telemetry['sensor_status'] = value

        return telemetry

    async def get_optimal_action(self):
        """Determine the optimal action based on the current telemetry data."""

        if not self.telemetry:
            print("No telemetry data available for optimization.")
            return None

        # Extract telemetry data
        battery = float(self.telemetry.get("battery", 100))
        altitude = float(self.telemetry.get("y_position", 0))
        sensor_status = self.telemetry.get("sensor_status", "GREEN")

        # Default action
        action = {
            'speed': 5,
            'altitude_change': 150,
            'movement': 'fwd'
        }

        # Optimization logic based on sensor status
        if sensor_status == "GREEN":
            if altitude < basealtitude:
                action['altitude_change'] = min(5, basealtitude - altitude)  # Climb to optimal altitude
            elif altitude > basealtitude:
                action['altitude_change'] = max(-5, basealtitude - altitude)  # Descend to optimal altitude

            if battery > 70:
                action['speed'] = 5  # Faster when battery is high
            elif battery > 40:
                action['speed'] = 3  # Moderate speed for mid battery
            else:
                action['speed'] = 1  # Conserve battery when low


        elif sensor_status == "YELLOW":
            if altitude > 50:
                action['altitude_change'] = -10  # Descend faster
            elif altitude > 30:
                action['altitude_change'] = -5  # Descend moderately

            if battery > 60:
                action['speed'] = 3
            else:
                action['speed'] = 1

        elif sensor_status == "RED":
            if altitude > 2.5:
                action['altitude_change'] = -0.1  # Careful descent
            elif altitude < 1.5:
                action['altitude_change'] = 0.2  # Careful ascent

            if battery > 50:
                action['speed'] = 2
            else:
                action['speed'] = 1

        # Battery conservation override
        if battery < 20:
            action['speed'] = 1  # Reduce speed
            if sensor_status == "GREEN":
                if altitude < basealtitude:
                    action['altitude_change'] = min(3, basealtitude - altitude)
                elif altitude > basealtitude:
                    action['altitude_change'] = max(-3, basealtitude - altitude)

        return action
    async def simulation(self, websocket):
        """Automate the drone flight simulation."""
        print("Starting simulation...")
        # Send the initial command to set the drone's starting parameters
        data = await self.send_command(websocket, 5, basealtitude, 'fwd')

        if data and "telemetry" in data:
            self.telemetry = self.parse_telemetry(data["telemetry"])
            print(f"Telemetry updated: {self.telemetry}")
        else:
            print("Failed to retrieve initial telemetry.")
            return

        while True:
            # Get the optimal action based on telemetry data
            action = await self.get_optimal_action()
            if not action:
                print("No optimal action determined. Ending simulation.")
                break

            # Send the optimized command to the server
            data = await self.send_command(
                websocket,
                speed=action['speed'],
                altitude=action['altitude_change'],
                movement=action['movement']
            )
            # Update telemetry data
            if data and data["status"] == "success" and "telemetry" in data:
                self.telemetry = self.parse_telemetry(data["telemetry"])
                print(f"Telemetry updated: {self.telemetry}")
                print(f"Iteration: {self.command_count}")
            else:
                print("Simulation ended due to crash or error.")
                break

if __name__ == "__main__":
    client = DroneClient()

    asyncio.run(client.connect())
