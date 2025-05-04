import time
from typing import Tuple

import olympe
from olympe.messages.ardrone3.Piloting import PCMD, Landing, Takeoff, UserTakeOff, moveTo
from olympe.messages.ardrone3.PilotingState import PositionChanged

MAX_RETRY = 1

olympe.log.update_config({"loggers": {"olympe": {"level": "ERROR"}}})

from .base_commander import BaseCommander

# check documentation for takeoff not from the ground
# command message olympe.messages.ardrone3.Piloting.UserTakeOff(state, _timeout=10, _no_expect=False, _float_tol=(1e-07, 1e-09))

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

    async def takeoff(self) -> None:
        self.drone(Takeoff()).wait().success()

    async def prepare_for_drop(self) -> None:
        self.drone(UserTakeOff()).wait().success()

    async def set_camera_angle(self, angle: float) -> None:
        raise NotImplementedError("set_camera_angle not implemented for OlympeCommander")

    async def set_pcmds(self, roll: float, pitch: float, yaw: float, gaz: float) -> None:
        """
        Input :
        roll : float
        pitch : float
        yaw : float
        gaz : float

        They are expressed as joytsitck values in the range [-100, 100]

        Olympe documentation:

        Parameters:

        flag (u8) – Boolean flag: 1 if the roll and pitch values should be taken in consideration. 0 otherwise

        roll (i8) – Roll angle as signed percentage. On copters: Roll angle expressed as signed percentage of the max pitch/roll setting, in range [-100, 100] -100 corresponds to a roll angle of max pitch/roll to the left (drone will fly left) 100 corresponds to a roll angle of max pitch/roll to the right (drone will fly right) This value may be clamped if necessary, in order to respect the maximum supported physical tilt of the copter. On fixed wings: Roll angle expressed as signed percentage of the physical max roll of the wing, in range [-100, 100] Negative value makes the plane fly to the left Positive value makes the plane fly to the right

        pitch (i8) – Pitch angle as signed percentage. On copters: Expressed as signed percentage of the max pitch/roll setting, in range [-100, 100] -100 corresponds to a pitch angle of max pitch/roll towards sky (drone will fly backward) 100 corresponds to a pitch angle of max pitch/roll towards ground (drone will fly forward) This value may be clamped if necessary, in order to respect the maximum supported physical tilt of the copter. On fixed wings: Expressed as signed percentage of the physical max pitch of the wing, in range [-100, 100] Negative value makes the plane fly in direction of the sky Positive value makes the plane fly in direction of the ground

        yaw (i8) – Yaw rotation speed as signed percentage. On copters: Expressed as signed percentage of the max yaw rotation speed setting, in range [-100, 100]. -100 corresponds to a counter-clockwise rotation of max yaw rotation speed 100 corresponds to a clockwise rotation of max yaw rotation speed This value may be clamped if necessary, in order to respect the maximum supported physical tilt of the copter. On fixed wings: Giving more than a fixed value (75% for the moment) triggers a circle. Positive value will trigger a clockwise circling Negative value will trigger a counter-clockwise circling

        gaz (i8) – Throttle as signed percentage. On copters: Expressed as signed percentage of the max vertical speed setting, in range [-100, 100] -100 corresponds to a max vertical speed towards ground 100 corresponds to a max vertical speed towards sky This value may be clamped if necessary, in order to respect the maximum supported physical tilt of the copter. During the landing phase, putting some positive gaz will cancel the land. On fixed wings: Expressed as signed percentage of the physical max throttle, in range [-100, 100] Negative value makes the plane fly slower Positive value makes the plane fly faster
        """

        self.drone(PCMD(1, roll, pitch, yaw, gaz)).wait().success()
