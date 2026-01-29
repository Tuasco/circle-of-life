# Circle of Life

A multi-process ecosystem simulation in Python involving predators, preys, and grass, demonstrating various Inter-Process Communication (IPC) mechanisms.

## Overview

This project simulates a biological ecosystem where:
- **Preys** eat grass to survive.
- **Predators** eat preys to survive.
- **Grass** grows over time.
- **Events** (like droughts) can occur, affecting the ecosystem.

The core of the project is to demonstrate robust IPC and concurrency handling in Python on a Linux environment.

## Architecture

The simulation is built upon a multi-process architecture:

1.  **Display Process (`src/display.py`)**:
    - Acts as the main entry point and user interface (CLI).
    - Spawns the Environment process.
    - Communicates with the Environment via **POSIX Message Queues**.

2.  **Environment Process (`src/env_manager.py`)**:
    - The central "server" of the simulation.
    - Manages the state of the world (grass levels, population tracking).
    - Allocates resources (Shared Memory blocks) and IDs.
    - Listens for new individuals via **Sockets**.
    - Handles periodic events (growth, drought) using **Signals** and timers.

3.  **Individual Processes (`src/individual.py`)**:
    - Represent a single entity (Prey or Predator).
    - Connect to the Environment via **Sockets** to join the simulation.
    - Communicate their state (energy, survival status) and read the world state via **Shared Memory**.

## IPC Mechanisms Used

- **POSIX Message Queues**: For structured command/control communication between the Display and Environment processes.
- **Shared Memory (`/dev/shm`)**: For high-performance, low-latency state sharing between Individuals and the Environment.
- **Semaphores**: For synchronizing access to shared resources.
- **Sockets (TCP/IP)**: For the initial "handshake" and dynamic connection of new processes (Individuals) to the Environment.
- **Signals**: Used for handling asynchronous events like droughts (`SIGALRM`) and graceful shutdowns (`SIGINT`).

## Requirements

- **OS**: Linux (Required for POSIX IPC support).
- **Python**: 3.8+
- **Dependencies**:
    - `posix_ipc`

## Installation

1.  Clone the repository.
2.  Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the simulation using the main display script:

```bash
python src/display.py
```

### Commands

The simulation features a CLI shell ("Honishell") that accepts the following commands:

*   **Add Individuals**:
    *   `add prey [count]` - Add *n* preys.
    *   `add predator [count]` - Add *n* predators.
    *   `add all [count]` - Add *n* of each type.
    *   `add grass [value]` - Add grass value.

*   **List Status**:
    *   `list prey` - List prey population.
    *   `list predator` - List predator population.
    *   `list all` - List all populations.
    *   `list grass` - Show current grass level.

*   **Delete Individuals**:
    *   `delete prey [count]` - Remove *n* preys.
    *   `delete predator [count]` - Remove *n* predators.
    *   `delete all [count]` - Remove *n* of each type.

*   **Control**:
    *   `help` or `?` - Show help.
    *   `quit`, `exit`, or `stop` - Gracefully stop the simulation and clean up resources.

## Project Structure

*   `src/display.py`: Main entry point and UI logic.
*   `src/env_manager.py`: Core simulation logic and state management.
*   `src/individual.py`: Logic for Prey and Predator processes.
*   `src/parser.py`: Command parsing logic for the CLI.
*   `src/message_queue.py`: Wrapper for POSIX message queue operations.
*   `src/CONSTS.py`: Global constants (population limits, IPC names, etc.).

## Authors

*   INSA TC3 PPC Project Team
