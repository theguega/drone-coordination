import olympe
from olympe.messages.ardrone3.Piloting import Landing, moveTo
from olympe.messages.ardrone3.PilotingState import positionChanged

from .base_commander import BaseCommander


class OlympeCommander(BaseCommander):
    def __init__(self, address: str):
        super().__init__(address)
        self.drone = olympe.Drone(self.address)

    async def connect(self) -> None:
        self.drone.connect()
        print(f"[Olympe] Connected to {self.address}")

    async def disconnect(self) -> None:
        self.drone.disconnect()
        print(f"[Olympe] Disconnected from {self.address}")

    async def get_position(self) -> tuple:
        # Subscribe and fetch a single positionChanged message
        self.drone.subscribe(positionChanged())
        state = self.drone.get_state(positionChanged)
        self.drone.unsubscribe(positionChanged)
        lat = state.args["latitude"]
        lon = state.args["longitude"]
        alt = state.args["altitude"]
        return lat, lon, alt

    async def goto_position(
        self, latitude: float, longitude: float, altitude: float
    ) -> None:
        # moveTo(latitude, longitude, altitude, heading)
        self.drone(moveTo(latitude, longitude, altitude, 0.0)).wait().success()

    async def land(self) -> None:
        self.drone(Landing()).wait().success()
