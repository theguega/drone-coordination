from mavsdk import System

from .base_commander import BaseCommander


class MAVSDKCommander(BaseCommander):
    def __init__(self, address: str):
        super().__init__(address)
        self.drone = System()

    async def connect(self) -> None:
        await self.drone.connect(system_address=self.address)
        print(f"[MAVSDK] Connected to {self.address}")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                break

    async def disconnect(self) -> None:
        print(f"[MAVSDK] Disconnected from {self.address}")

    async def get_position(self) -> tuple:
        async for pos in self.drone.telemetry.position():
            return pos.latitude_deg, pos.longitude_deg, pos.absolute_altitude_m

    async def goto_position(
        self, latitude: float, longitude: float, altitude: float
    ) -> None:
        await self.drone.action.goto_location(latitude, longitude, altitude, 0.0)

    async def land(self) -> None:
        await self.drone.action.land()
