import pygame
import asyncio
import websockets
import json
import sys
import time
from typing import Dict, Any, Optional

import numpy as np

# Import the DroneClient class (ensure correct relative import)
from optimizer import DroneClient

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

class DroneSimulation:
    def __init__(self, drone_client):
        """Initialize the simulation environment."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Drone Simulation")
        self.clock = pygame.time.Clock()
        self.client = drone_client  # Instance of DroneClient
        self.running = True
        self.x = SCREEN_WIDTH // 2  # Initial x position
        self.y = SCREEN_HEIGHT // 2  # Initial y position
        self.telemetry = {}
        self.uri = "ws://localhost:8765"  # Add server URI

        # Font setup
        self.font_large = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

    def draw_drone(self, x, y):
        """Draw the drone as a rectangle on the screen."""
        pygame.draw.rect(self.screen, BLUE, pygame.Rect(int(x) - 10, int(y) - 5, 20, 10))

    def display_game_data(self, telemetry):
        """Display telemetry data in a game-like manner."""
        # Battery Level
        battery = float(telemetry.get("battery", 100))
        battery_color = GREEN if battery > 50 else YELLOW if battery > 20 else RED
        battery_text = self.font_large.render(f"Battery: {battery:.1f}%", True, battery_color)
        self.screen.blit(battery_text, (20, 20))

        # Sensor Status
        sensor_status = telemetry.get("sensor_status", "GREEN")
        sensor_color = GREEN if sensor_status == "GREEN" else YELLOW if sensor_status == "YELLOW" else RED
        sensor_text = self.font_large.render(f"Sensor: {sensor_status}", True, sensor_color)
        self.screen.blit(sensor_text, (20, 60))

        # Gyroscope (Example - display only X component)
        gyro = telemetry.get("gyroscope", [0, 0, 0])
        gyro_x = gyro[0] if isinstance(gyro, list) and len(gyro) == 3 else 0
        gyro_text = self.font_small.render(f"Gyro X: {gyro_x:.2f}", True, WHITE)
        self.screen.blit(gyro_text, (20, 100))

        # Wind and Dust
        wind = float(telemetry.get("wind_speed", 0))
        dust = float(telemetry.get("dust_level", 0))
        wind_text = self.font_small.render(f"Wind: {wind:.2f}", True, WHITE)
        dust_text = self.font_small.render(f"Dust: {dust:.2f}", True, WHITE)
        self.screen.blit(wind_text, (20, 130))
        self.screen.blit(dust_text, (20, 160))

        # Iterations and Total X
        iterations = telemetry.get("iterations", 0)
        x_position = float(telemetry.get("x_position", 0))
        iter_text = self.font_large.render(f"Iterations: {iterations}", True, WHITE)
        x_text = self.font_large.render(f"Total X: {x_position:.2f}", True, WHITE)
        self.screen.blit(iter_text, (SCREEN_WIDTH - 250, 20))
        self.screen.blit(x_text, (SCREEN_WIDTH - 250, 60))


    async def run(self):
        """Run the main simulation loop."""
        try:
            async with websockets.connect(self.uri) as websocket:
                print("Connected to WebSocket server")

                # Initialize the simulation using DroneClient's simulation method
                simulation_task = asyncio.create_task(self.client.simulation(websocket))

                while self.running:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False

                    # Clear the screen
                    self.screen.fill(BLACK)

                    # Get telemetry data from the client
                    if self.client.telemetry:
                        self.telemetry = self.client.telemetry

                    telemetry = self.telemetry or {
                        "x_position": self.x,
                        "y_position": self.y,
                        "battery": 100,
                        "altitude": 0,
                        "speed": 0,
                        "gyroscope": [0, 0, 0],  # Ensure gyroscope is always present
                        "wind_speed": 0,
                        "dust_level": 0,
                        "iterations": 0
                    }

                    # Update the drone's position based on telemetry
                    x_position = float(telemetry.get("x_position", self.x))
                    y_position = float(telemetry.get("y_position", self.y))
                    self.x = SCREEN_WIDTH // 2 + x_position  # Center the drone's X position
                    self.y = SCREEN_HEIGHT - y_position  # Invert y for screen coordinates

                    # Draw the drone
                    self.draw_drone(self.x, self.y)

                    # Display telemetry data
                    self.display_game_data(telemetry)

                    # Update the display
                    pygame.display.flip()

                    # Cap the frame rate
                    self.clock.tick(30)
 # Log the event
                pygame.quit()

                # Cancel the simulation task
                simulation_task.cancel()
                try:
                    await simulation_task  # Await to handle any exceptions
                except asyncio.CancelledError:
                    print("Simulation task cancelled.")

        except websockets.exceptions.ConnectionRefusedError as e:
            print(f"Connection refused. Ensure the server is running at {self.uri}")
        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            pygame.quit()


# Main entry point
if __name__ == "__main__":
    # Configure logging for the main script

    # Create a DroneClient instance
    drone_client = DroneClient()

    # Create and run the simulation
    simulation = DroneSimulation(drone_client)
    asyncio.run(simulation.run())

