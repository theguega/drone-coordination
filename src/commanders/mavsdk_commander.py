import asyncio
from typing import Tuple

from mavsdk import System

from .base_commander import BaseCommander

MAX_RETRY = 5
CONNECTION_TIMEOUT = 2
TAKEOFF_ALTITUDE = 5


class MAVSDKCommander(BaseCommander):
    def __init__(self, address: str):
        super().__init__(address)
        self.drone = System()

    async def connect(self) -> None:
        for attempt in range(1, MAX_RETRY + 1):
            print(f"[MAVSDK] Attempting to connect to {self.address} (Attempt {attempt}/{MAX_RETRY})")
            try:
                await asyncio.wait_for(self.drone.connect(system_address=self.address), timeout=CONNECTION_TIMEOUT)

                # Wait for drone to report connected state
                async for state in self.drone.core.connection_state():
                    if state.is_connected:
                        print(f"[MAVSDK] Connected to {self.address}")
                        break

                # Wait for global position OK
                async for health in self.drone.telemetry.health():
                    if health.is_global_position_ok:
                        print("[MAVSDK] Global position OK")
                        break

                print("[MAVSDK] VTOL connected")

            except (asyncio.TimeoutError, Exception) as e:
                print(f"[MAVSDK] Connection attempt {attempt} failed: {e}")
                await asyncio.sleep(2)

        print(f"[MAVSDK] Failed to connect to {self.address} after {MAX_RETRY} attempts.")
        raise ConnectionError(f"Failed to connect to {self.address} after {MAX_RETRY} attempts")

    async def disconnect(self) -> None:
        try:
            # Ensure the drone is disarmed before disconnecting
            try:
                await self.drone.action.disarm()
                print(f"[MAVSDK] Disarmed drone at {self.address}")
            except Exception as e:
                print(f"[MAVSDK] Error disarming drone: {e}")

            # Land the drone if it's still flying
            try:
                await self.land()
                print(f"[MAVSDK] Landed drone at {self.address}")
            except Exception as e:
                print(f"[MAVSDK] Error landing drone: {e}")

            # MAVSDK doesn't have an explicit disconnect method
            # The connection will be closed when the drone object is garbage collected
            print(f"[MAVSDK] Disconnected from {self.address}")
        except Exception as e:
            print(f"[MAVSDK] Error during disconnect: {e}")

    async def get_position(self) -> Tuple[float, float, float]:
        lat = lon = alt = 500.0  # fallback dummy values
        async for pos in self.drone.telemetry.position():
            lat = pos.latitude_deg
            lon = pos.longitude_deg
            alt = pos.absolute_altitude_m
            break
        return (lat, lon, alt)

    async def goto_position(self, latitude: float, longitude: float, altitude: float) -> None:
        await self.drone.action.goto_location(latitude, longitude, altitude, 0.0)

    async def land(self) -> None:
        await self.drone.action.land()

    async def takeoff(self) -> None:
        await self.drone.action.arm()

        await self.drone.manual_control.set_manual_control_input(float(0), float(0), float(0.5), float(0))

        await self.drone.action.set_takeoff_altitude(float(TAKEOFF_ALTITUDE))
        await self.drone.action.takeoff()

    async def prepare_for_drop(self) -> None:
        raise NotImplementedError("prepare_for_drop not implemented for MAVSDKCommander")

    async def set_camera_angle(self, angle: float) -> None:
        raise NotImplementedError("set_camera_angle not implemented for MAVSDKCommander")

    async def set_pcmds(self, roll: float, pitch: float, yaw: float, gaz: float) -> None:
        """
        Input :
        roll : float
        pitch : float
        yaw : float
        gaz : float

        They are expressed as joytsitck values in the range [-100, 100]

        MAVSDK documentation:
        Set manual control input

        The manual control input needs to be sent at a rate high enough to prevent triggering of RC loss, a good minimum rate is 10 Hz.

        Parameters:

                x (float) – value between -1. to 1. negative -> backwards, positive -> forwards

                y (float) – value between -1. to 1. negative -> left, positive -> right

                z (float) – value between -1. to 1. negative -> down, positive -> up (usually for now, for multicopter 0 to 1 is expected)

                r (float) – value between -1. to 1. negative -> turn anti-clockwise (towards the left), positive -> turn clockwise (towards the right)

        Raises:

            ManualControlError – If the request fails. The error contains the reason for the failure.
        """

        y = float(roll) / 100.0
        x = float(pitch) / 100.0
        r = float(yaw) / 100.0
        z = float(gaz) / 100.0 / 2.0 + 0.5

        await self.drone.manual_control.set_manual_control_input(x, y, z, r)
