import time
from typing import Tuple

import olympe
from olympe.messages.ardrone3.Piloting import Landing, moveTo
from olympe.messages.ardrone3.PilotingState import PositionChanged

MAX_RETRY = 1

olympe.log.update_config({"loggers": {"olympe": {"level": "ERROR"}}})

from .base_commander import BaseCommander


class OlympeCommander(BaseCommander):
    def __init__(self, address: str):
        super().__init__(address)
        self.drone = olympe.Drone(self.address)

    async def connect(self) -> None:
        for attempt in range(1, MAX_RETRY + 1):
            print(f"[Olympe] Attempting to connect to {self.address} (Attempt {attempt}/{MAX_RETRY})")
            if self.drone.connect():
                print(f"[Olympe] Connected to {self.address}")
                return
            else:
                print(f"[Olympe] Connection attempt {attempt} failed.")
                time.sleep(2)
        raise TimeoutError(f"[OLympe] Failed to connect to {self.address} after {MAX_RETRY} attempts.")

    async def disconnect(self) -> None:
        self.drone.disconnect()
        print(f"[Olympe] Disconnected from {self.address}")

    async def get_position(self) -> Tuple[float, float, float]:
        state = self.drone.get_state(PositionChanged)
        lat = state.args["latitude"]
        lon = state.args["longitude"]
        alt = state.args["altitude"]
        return (float(lat), float(lon), float(alt))

    async def goto_position(self, latitude: float, longitude: float, altitude: float) -> None:
        self.drone(moveTo(latitude, longitude, altitude, 0.0)).wait().success()

    async def land(self) -> None:
        self.drone(Landing()).wait().success()
