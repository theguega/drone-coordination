import asyncio
import sys
from typing import Tuple

from mavsdk import System

from .base_commander import BaseCommander

MAX_RETRY = 5
CONNECTION_TIMEOUT = 2


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

                await self.drone.action.arm()
                print("VTOL Armed")
                return

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
