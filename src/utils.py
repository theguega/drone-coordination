import asyncio
import traceback
from typing import Tuple

import inputs
from geographiclib.geodesic import Geodesic

from commanders.mavsdk_commander import MAVSDKCommander
from commanders.olympe_commander import OlympeCommander

DEBUG = True

# Follow-me constants
MIN_DIST_M = 10.0
FOLLOW_DIST_M = 20.0
ALT_OFFSET_M = 2.0


def compute_follow_point(
    leader_lat: float,
    leader_lon: float,
    follower_lat: float,
    follower_lon: float,
    distance: float,
) -> Tuple[float, float]:
    """
    Compute target latitude/longitude at `distance` meters from leader,
    along the line toward the follower.
    """
    # Use the WGS84 ellipsoid parameters
    geod = Geodesic(6378137, 1 / 298.257223563)  # WGS84 parameters (a=semi-major axis, f=flattening)
    inv = geod.Inverse(leader_lat, leader_lon, follower_lat, follower_lon)
    bearing = inv["azi1"]
    dest = geod.Direct(leader_lat, leader_lon, bearing, distance)
    return dest["lat2"], dest["lon2"]


async def follow_loop(leader: MAVSDKCommander, follower: OlympeCommander, interval: float = 1.0) -> None:
    """
    Continuously compute and send follow-me commands
    until drones come closer than MIN_DIST, then land follower.
    """
    # Use the WGS84 ellipsoid parameters
    geod = Geodesic(6378137, 1 / 298.257223563)  # WGS84 parameters (a=semi-major axis, f=flattening)
    try:
        while True:
            # Retrieve positions
            lead_lat, lead_lon, lead_alt = await leader.get_position()
            foll_lat, foll_lon, _ = await follower.get_position()

            # Compute separation
            sep = geod.Inverse(lead_lat, lead_lon, foll_lat, foll_lon)["s12"]
            if sep < MIN_DIST_M:
                print(f"Too close ({sep:.1f}m < {MIN_DIST_M}m) – landing follower.")
                await follower.land()
                break

            # Compute target follow point and desired altitude
            tgt_lat, tgt_lon = compute_follow_point(lead_lat, lead_lon, foll_lat, foll_lon, FOLLOW_DIST_M)
            tgt_alt = lead_alt + ALT_OFFSET_M
            print(f"Moving follower to {tgt_lat:.6f}, {tgt_lon:.6f}, alt {tgt_alt:.1f}m")

            # Send command
            await follower.goto_position(tgt_lat, tgt_lon, tgt_alt)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        print("Follow loop cancelled – stopping both drones by sending pcmds")
        try:
            await follower.set_pcmds(0, 0, 0, 0)
        except Exception as e:
            print(f"Error stopping drones: {e}")
    except KeyboardInterrupt:
        print("Follow loop cancelled – stopping both drones by sending pcmds")
        try:
            await follower.set_pcmds(0, 0, 0, 0)
        except Exception as e:
            print(f"Error stopping drones: {e}")
    except Exception as e:
        print(f"Error in follow loop: {e}")
        traceback.print_exc()
        try:
            await follower.land()
        except Exception as land_error:
            print(f"Error landing follower after exception: {land_error}")


async def manual_control(drone: OlympeCommander) -> None:
    """
    Continuously read PS4 controller commands and send them to the drone.
    Only sends commands when values are updated.
    Implements a deadzone to prevent drift when joysticks are near center.
    Focuses only on joystick inputs.
    """
    print("PS4 manual control started. Press Ctrl-C to stop.")
    try:
        # Initialize joystick
        joysticks = inputs.devices.gamepads
        if not joysticks:
            print("No gamepad detected. Please connect one.")
            return
        joystick = joysticks[0]
        print(f"Using joystick: {joystick}")

        # Store current state of controls
        control_state = {"roll": 0.0, "pitch": 0.0, "yaw": 0.0, "throttle": 0.0}
        previous_state = control_state.copy()

        # Define deadzone - adjust this value as needed
        DEADZONE = 0.01

        def apply_deadzone(value):
            """Apply deadzone to prevent drift when joystick is near center"""
            if abs(value) < DEADZONE:
                return 0.0
            # Smooth out the transition from deadzone to full range
            adjusted_value = (abs(value) - DEADZONE) / (1.0 - DEADZONE)
            return adjusted_value if value > 0 else -adjusted_value

        while True:
            events = joystick.read()

            for event in events:
                print(f"code : {event.code}, state : {event.state}\n")

            updated = False

            for event in events:
                # Only process joystick events (ignore buttons)
                if event.code == "ABS_X":  # Left stick horizontal - Roll
                    value = event.state / 32768.0  # Normalize to -1.0 to 1.0
                    control_state["roll"] = apply_deadzone(value)
                    updated = True

                elif event.code == "ABS_Y":  # Left stick vertical - Pitch
                    value = -event.state / 32768.0  # Normalize and invert
                    control_state["pitch"] = apply_deadzone(value)
                    updated = True

                elif event.code == "ABS_RX":  # Right stick horizontal - Yaw
                    value = event.state / 32768.0  # Normalize
                    control_state["yaw"] = apply_deadzone(value)
                    updated = True

                elif event.code == "ABS_RY":  # Right stick vertical - Throttle
                    value = -event.state / 32768.0  # Normalize and invert
                    # For throttle, we map from -1,1 to 0,1 range
                    normalized_value = (value + 1.0) / 2.0
                    control_state["throttle"] = apply_deadzone(normalized_value * 2.0) / 2.0 if normalized_value < 0.5 else normalized_value
                    updated = True

            # Check if any values have changed significantly from previous state
            if updated and any(abs(control_state[key] - previous_state[key]) > 0.01 for key in control_state):
                await drone.set_pcmds(control_state["roll"], control_state["pitch"], control_state["yaw"], control_state["throttle"])
                print(control_state)
                previous_state = control_state.copy()

            await asyncio.sleep(0.01)

    except Exception as e:
        print(f"Error in manual control: {e}")
    finally:
        # Ensure drone stops if control is interrupted
        await drone.set_pcmds(0.0, 0.0, 0.0, 0.0)
        print("Manual control terminated.")
