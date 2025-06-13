import logging
from typing import Tuple

from mavsdk import System

from .base_commander import BaseCommander

MAX_CONNECTION_ATTEMPTS = 3
CONNECTION_TIMEOUT = 10  # seconds
JOYSTICK_DEADZONE = 0.1
UPDATE_RATE = 0.05  # seconds (20 Hz)
MAX_VELOCITY = 5.0  # m/s

logger = logging.getLogger()


class MAVSDKCommander(BaseCommander):
    def __init__(self, address: str):
        super().__init__(address)
        self.drone = System()
        self.connection_string = address

    async def connect(self) -> None:
        """Connect to the drone with multiple retry attempts.

        Returns:
            bool: True if connection successful, False otherwise
        """
        logger.debug(f"Attempting to connect to drone at {self.connection_string}")
        try:
            await self.drone.connect(system_address=self.connection_string)
            logger.debug(f"Connected to drone at {self.connection_string}")
            async for state in self.drone.core.connection_state():
                if state.is_connected:
                    logger.debug("-- Connected to drone with MAVSDK!")
                    break
            logger.debug("Waiting for drone to have a global position estimate...")
            async for health in self.drone.telemetry.health():
                if health.is_global_position_ok and health.is_home_position_ok:
                    logger.debug("-- Global position estimate OK")
                    break
        except Exception as e:
            logger.error(f"Error connecting to drone: {e}")

    async def disconnect(self) -> None:
        raise NotImplementedError("not implemented for MAVSDKCommander")

    async def get_position(self) -> Tuple[float, float, float]:
        lat = lon = alt = 500.0  # fallback dummy values
        async for pos in self.drone.telemetry.position():
            lat = pos.latitude_deg
            lon = pos.longitude_deg
            alt = pos.absolute_altitude_m
            break
        return (lat, lon, alt)

    async def goto_position(self, latitude: float, longitude: float, altitude: float) -> None:
        raise NotImplementedError("not implemented for MAVSDKCommander")

    async def land(self) -> None:
        raise NotImplementedError("not implemented for MAVSDKCommander")

    async def takeoff(self) -> None:
        raise NotImplementedError("not implemented for MAVSDKCommander")

    async def prepare_for_drop(self) -> None:
        raise NotImplementedError("not implemented for MAVSDKCommander")

    async def set_camera_angle(self, angle: float) -> None:
        raise NotImplementedError("not implemented for MAVSDKCommander")

    async def set_pcmds(self, roll: int, pitch: int, yaw: int, gaz: int) -> None:
        raise NotImplementedError("not implemented for MAVSDKCommander")
