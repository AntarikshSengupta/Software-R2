# Software-R2
Repo containing project for Software R2 c=selection for JU Mechatronics Club
# Drone Optimization and Simulation

This repository contains an extended drone client and a drone simulation environment for visualization and testing of drone control strategies.

## Repository Structure

- **optimizer.py**  
  Contains an extended version of the drone client with additional methods for telemetry parsing, action optimization, and simulation control. Key methods include:  
  - `parse_telemetry` — Processes incoming telemetry data from the drone.  
  - `get_optimal_action` — Computes the best action to take based on current telemetry.  
  - `simulation` — Runs a simulation loop integrating the drone client logic.

- **simulator.py**  
  Implements the `DroneSimulation` class using Pygame for visualizing the drone’s movements and environment. This provides a graphical interface to observe drone behavior during simulations.

## Features

- Real-time telemetry parsing and processing.  
- Algorithmic determination of optimal drone actions.  
- Interactive simulation environment with Pygame visualization.  
- Modular design allowing easy extension and integration.

  

## Usage

- **Run the drone client with optimization:**  
Execute the `optimizer.py` script to start the drone client with extended capabilities.

- **Run the simulation visualization:**  
Run `simulator.py` to launch the Pygame window and visualize drone movements.


