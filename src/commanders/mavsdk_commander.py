import asyncio
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

    async def connect(self) -> None:
        """Connect to the drone with multiple retry attempts.

        Returns:
            bool: True if connection successful, False otherwise
        """
        logger.debug(f"Attempting to connect to drone at {self.connection_string}")

        for attempt in range(1, MAX_CONNECTION_ATTEMPTS + 1):
            try:
                logger.debug(f"Connection attempt {attempt}/{MAX_CONNECTION_ATTEMPTS}")
                await self.drone.connect(system_address=self.connection_string)

                # Wait for connection with timeout
                connection_task = asyncio.create_task(self.wait_for_connection())
                try:
                    await asyncio.wait_for(connection_task, timeout=CONNECTION_TIMEOUT)
                    logger.debug("Successfully connected to the drone!")
                    return True
                except asyncio.TimeoutError:
                    logger.warning(f"Connection attempt {attempt} timed out after {CONNECTION_TIMEOUT} seconds")
                    continue

            except Exception as e:
                logger.error(f"Connection attempt {attempt} failed: {e}")
                await asyncio.sleep(1)

        logger.error(f"Failed to connect after {MAX_CONNECTION_ATTEMPTS} attempts")

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

    async def set_pcmds(self, roll: float, pitch: float, yaw: float, gaz: float) -> None:
        raise NotImplementedError("not implemented for MAVSDKCommander")
