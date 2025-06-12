# 🚁 VTOL and FPV Drone Coordination

A sophisticated drone coordination system that enables autonomous following behavior between two drones, with support for both MAVSDK and Parrot Olympe protocols. This project implements a leader-follower architecture where one drone can autonomously follow another, with additional features for manual control and special operations.

## ✨ Features

- 🤖 Autonomous following behavior between drones
- 🎮 Manual control support via RC
- 🛩️ Support for both MAVSDK and Parrot Olympe protocols
- 📊 Comprehensive logging system with colored output
- 🐳 Docker support for cross-platform compatibility
- 🔄 Real-time command processing and drone control

## 🛠️ Prerequisites

### For MacOS
- Docker

### For Linux
- UV (Python virtual environment manager)

## 🚀 Getting Started

### Using Docker (Recommended for MacOS)

```bash
# Build the Docker container
./drone-coordination.sh build

# Run the application
./drone-coordination.sh run
```

### Direct Installation (Linux)

```bash
# Create and activate virtual environment using UV
uv venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

## 🎯 Usage

The application provides several commands for controlling the drones:

- `/takeoff_follower` - Initiates takeoff for the follower drone
- `/follow` - Starts the autonomous following behavior
- `/prepare_for_drop` - Prepares the follower drone for being dropped from the leader
- `/manual` - Enables manual control of the follower drone
- `/help` - Displays available commands
- `/exit` - Exits the application

## 🔧 Configuration

The application supports various connection options:

```bash
# Basic usage with default addresses
python src/main.py --mavsdk_drone --olympe_drone

# Custom connection addresses
python src/main.py --mavsdk_drone udp://:14551 --olympe_drone 192.168.42.1
```

## 📦 Dependencies

- parrot-olympe==7.7.5
- geographiclib>=2.0
- mavsdk==2.8.4

## 📝 Logging

The application maintains detailed logs in `drone-coordination.log` with colored output in the terminal for better visibility of different log levels.

## 👥 Author

- **Theo Guegan** - [theo.guegan@etu.utc.fr](mailto:theo.guegan@etu.utc.fr)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
