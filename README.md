# VTOL and FPV Drone Coordination

## Overview

This project implements a collaborative mission scenario between two drones using MAVSDK in Python:

1.  **Primary Drone (VTOL):** A VTOL aircraft with a Pixhawk flight controller, connected via a serial port. Initially manually flown via QGroundControl, it carries the support drone.
2.  **Support Drone (FPV):** A small FPV-style drone based on Raspberry Pi + Navio2, equipped with a camera and AprilTag detection capabilities. Connected via UDP.

**Mission Scenario:**

1.  **Deployment:** The VTOL pilot manually releases the FPV drone mid-air using a remote-controlled mechanism. The FPV drone must power up, initialize, arm, and stabilize automatically.
2.  **Tracking:** Once stable, the FPV drone follows the VTOL drone, maintaining a configured distance and altitude offset. A safety distance prevents collisions.
3.  **Manual Control & Targeting:** Upon pilot command (e.g., VTOL entering HOLD mode), the VTOL stabilizes. The script stops commanding the FPV, allowing the pilot to take manual control via QGroundControl to inspect an area and detect an AprilTag.
4.  **Target Validation & Transmission:** When the AprilTag is detected by a local script on the FPV drone, its estimated GPS coordinates (latitude, longitude) are sent to this coordination script via ZeroMQ.
5.  **Final Positioning:** The script commands the FPV drone to move to a safe standoff position. Then, it commands the VTOL drone to position itself accurately above the received target coordinates.

## Hardware Requirements

*   **VTOL Drone:**
    *   VTOL Airframe
    *   Pixhawk Flight Controller (or ArduPilot/PX4 compatible)
    *   RC Receiver
    *   GPS, Barometer, IMU, etc.
    *   Release Mechanism (e.g., electromagnet) controllable via Pixhawk/RC.
    *   Serial connection interface (to the computer running the script or via companion computer/network adapter).
*   **FPV Support Drone:**
    *   Lightweight Airframe (FPV style)
    *   Raspberry Pi (3B+ or newer recommended)
    *   Navio2 (or similar RPi flight controller HAT)
    *   Motors, ESCs, Propellers
    *   GPS, Barometer, IMU (via Navio2 or external)
    *   Raspberry Pi Camera
    *   Battery
    *   WiFi Module or other data link (for UDP connection).
*   **Ground Station:**
    *   Computer running this Python script.
    *   QGroundControl for initial VTOL piloting and manual FPV control.
    *   RC Transmitter for the pilot.

## Software Requirements

*   **Python:** Version 3.7+
*   **MAVSDK-Python:** Library for drone communication.
*   **ZeroMQ (pyzmq):** For coordinate communication from FPV to coordinator.
    ```bash
    pip install mavsdk asyncio argparse pyzmq
    ```
*   **Drone Firmware:**
    *   ArduPilot (recommended for consistency) or PX4 configured on both flight controllers.
    *   MAVLink parameters configured for Serial (VTOL) and UDP (FPV) connections. Ensure different `SYSID` for each drone.
    *   **Crucial:** The FPV drone's firmware must be configured to **auto-arm and enter a stabilized flight mode** (e.g., `LOITER` or `POSCTL`) upon boot/power-up after release.
*   **AprilTag Detection Script:** A separate script ( **not provided here** ) must run on the FPV drone's Raspberry Pi. It must:
    *   Access the camera stream.
    *   Detect AprilTags.
    *   Estimate/Calculate the GPS coordinates of the detected tag.
    *   **Transmit these coordinates (latitude, longitude) to the `drone_coordinator.py` script via ZeroMQ.** (See "AprilTag Integration..." section).
*   **(Optional) MAVSDK Server:** May be needed if the script isn't run directly on a companion computer connected to the drones. The current script assumes a direct MAVSDK-Python connection.

## Configuration

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```
2.  **Install Python Dependencies:**
    ```bash
    pip install mavsdk asyncio argparse pyzmq
    ```
3.  **Configure Drones:**
    *   Set MAVLink parameters on each drone (via QGroundControl/Mission Planner) to match the connection addresses used. Ensure different `SYSID`s.
    *   Configure the VTOL's release mechanism and link it to an RC switch.
    *   Configure the FPV drone for automatic arming and stabilization on startup.
4.  **Set Up AprilTag Script:** Implement your detection script on the FPV drone and its ZeroMQ communication logic to send coordinates.

## Execution

Run the main script `drone_coordinator.py` from the command line, optionally overriding default parameters:

```bash
python drone_coordinator.py \
    --vtol-addr "serial:///dev/ttyUSB0:57600" \
    --fpv-addr "udp://:14541" \
    --follow-alt-offset 5.0 \
    --follow-dist 25.0 \
    --safety-dist 12.0 \
    --zmq-bind-addr "tcp://*:5556" \
    --zmq-timeout 300
```

**Command-Line Arguments:**

*   `--vtol-addr`: MAVSDK connection string for the VTOL. Default: `serial:///dev/ttyAMA0:57600`
*   `--fpv-addr`: MAVSDK connection string for the FPV drone. Default: `udp://:14541`
*   `--follow-alt-offset` (meters): Altitude the FPV maintains *above* the VTOL during tracking. Default: `5.0`.
*   `--follow-dist` (meters): Target horizontal distance FPV maintains from VTOL during tracking. Default: `20.0`.
*   `--safety-dist` (meters): If horizontal distance < this value, FPV enters HOLD mode. Must be less than `follow-dist`. Default: `10.0`.
*   `--zmq-bind-addr`: ZeroMQ address for this script to BIND to (PULL socket). The FPV script must CONNECT to this. Use `*` to listen on all network interfaces. Default: `tcp://*:5556`.
*   `--zmq-timeout` (seconds): Max time to wait for the ZMQ coordinate message during the manual control phase. Default: `300.0` (5 minutes).

## Operational Workflow

1.  Start the `drone_coordinator.py` script with appropriate arguments.
2.  The script attempts to connect to the VTOL drone.
3.  The pilot takes off and flies the VTOL manually via QGroundControl to the mission area.
4.  When ready, the pilot activates the release mechanism via RC. The FPV drone is dropped.
5.  The FPV drone powers on, boots its system, auto-arms, and stabilizes (via internal configuration).
6.  The `drone_coordinator.py` script detects the FPV drone's connection (retrying periodically).
7.  Once the FPV is connected and stabilized (verified mode: HOLD/POSCTL), the script enters `FOLLOWING` mode.
8.  The script continuously calculates the target position for the FPV (based on VTOL position, `follow-dist`, `follow-alt-offset`) and sends `goto_location` commands, while checking the `safety-dist`.
9.  When the pilot wants manual FPV control for targeting:
    *   The pilot switches the VTOL to `HOLD` mode (or another agreed-upon trigger).
    *   The script detects this, stops sending `goto_location` to the FPV, and commands the VTOL to hold position.
    *   The script prints a message indicating the pilot can now connect QGroundControl to the FPV drone via its UDP address.
10. The pilot connects QGC to the FPV and flies manually to locate and validate the target with the AprilTag.
11. The AprilTag detection script on the FPV sends the validated target coordinates (latitude, longitude) via ZeroMQ to the `drone_coordinator.py` script.
12. The `drone_coordinator.py` script receives the coordinates.
13. The script commands the FPV to move to a safe, clear standoff position.
14. The script commands the VTOL to fly to the received GPS coordinates and hold position above the target.
15. The script finishes or indicates mission completion.

## AprilTag Integration and Coordinate Transmission via ZeroMQ

This script uses **ZeroMQ (PUSH/PULL pattern)** to receive the GPS coordinates of the target detected by the FPV drone.

*   **This Script (Coordinator):**
    *   Creates a ZMQ **PULL** socket.
    *   **Binds** to the address specified by `--zmq-bind-addr`.
    *   Waits to receive a message during the `wait_for_manual_control_phase`.
    *   Expects a single **JSON string** message containing `"latitude"` and `"longitude"` keys. Example:
        ```json
        {"latitude": 48.8584, "longitude": 2.2945}
        ```
    *   A timeout (`--zmq-timeout`) prevents indefinite waiting.

*   **Script on FPV Drone (You need to create this):**
    *   Must use ZeroMQ (e.g., `pyzmq` library for Python).
    *   Must create a ZMQ **PUSH** socket.
    *   Must **connect** to the IP address of the machine running `drone_coordinator.py` and the specified port (e.g., `tcp://<COORDINATOR_IP>:5556`).
    *   After detecting and validating the AprilTag, it must format the coordinates (latitude, longitude) into the JSON string format shown above.
    *   Must send this JSON string via the PUSH socket.

This approach decouples the FPV's detection/sending logic from the coordinator's receiving/mission logic.

## Hardware Choices for Support Drone

A detailed discussion comparing hardware options for the small support drone (custom FPV vs. commercial options like Parrot Anafi) can be found in a separate document:

[See Hardware Choices README](./HARDWARE_CHOICES.md) (*Link needs creation*)

## Limitations and Future Improvements

*   **Error Handling:** Basic error handling. Robust systems need more specific exceptions, timeouts, clear error states, and recovery strategies.
*   **State Machine:** A formal state machine would improve clarity and management of complex flows.
*   **Manual Takeover Trigger:** Using VTOL mode (`HOLD`) is simple but could be more explicit (e.g., dedicated MAVLink parameter).
*   **AprilTag Implementation:** The detection script and coordinate estimation logic on the FPV drone must be provided.
*   **Command Confirmation:** The script sends commands but doesn't always rigorously verify execution (except for final VTOL positioning).
*   **Connection Loss:** Handling temporary or permanent drone disconnections during the mission.
*   **Testing:** Thorough unit, integration, and simulation (SITL/HITL) testing is essential before real flights.

---
