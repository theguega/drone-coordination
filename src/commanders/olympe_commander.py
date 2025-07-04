import asyncio
import logging
from typing import Tuple

import olympe
from olympe.messages.ardrone3.Piloting import PCMD, Emergency, Landing, TakeOff, UserTakeOff, moveTo
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged, PositionChanged

MAX_RETRY = 3
TIME_OUT_DROP = 15

olympe.log.update_config({"loggers": {"olympe": {"level": "ERROR"}}})
logger = logging.getLogger()

from .base_commander import BaseCommander


class OlympeCommander(BaseCommander):
    def __init__(self, address: str):
        super().__init__(address)
        self.drone = olympe.Drone(self.address)

        self.in_the_air = False

    async def connect(self) -> None:
        for attempt in range(1, MAX_RETRY + 1):
            logger.debug(f"[Olympe] Attempting to connect to {self.address} (Attempt {attempt}/{MAX_RETRY})")
            if self.drone.connect():
                logger.debug(f"[Olympe] Connected to {self.address}")
                return
            else:
                logger.debug(f"[Olympe] Connection attempt {attempt} failed.")
                await asyncio.sleep(2)

        raise TimeoutError(f"[OLympe] Failed to connect to {self.address} after {MAX_RETRY} attempts.")

    async def disconnect(self) -> None:
        self.drone.disconnect()
        logger.debug(f"[Olympe] Disconnected from {self.address}")

    async def get_position(self) -> Tuple[float, float, float]:
        state = self.drone.get_state(PositionChanged)
        lat = state.args["latitude"]
        lon = state.args["longitude"]
        alt = state.args["altitude"]
        return (float(lat), float(lon), float(alt))

    async def goto_position(self, latitude: float, longitude: float, altitude: float) -> None:
        self.drone(moveTo(latitude, longitude, altitude, 0.0)).wait().success()

    async def land(self) -> None:
        try:
            assert self.drone(Landing()).wait().success()
            self.in_the_air = False
            logger.info("[Olympe] Landing successful")
        except Exception:
            logger.error("[Olympe] Landing failed")

    async def takeoff(self) -> None:
        try:
            assert self.drone(TakeOff()).wait().success()
            self.in_the_air = True
            logger.info("[Olympe] Takeoff successful")
        except Exception as e:
            logger.error(f"[Olympe] Takeoff failed : {e}")

    async def prepare_for_drop(self) -> None:
        try:
            dropping_procedure = self.drone(UserTakeOff(1) >> FlyingStateChanged(state="hovering", _timeout=TIME_OUT_DROP)).wait()
            if dropping_procedure.success():
                logger.info("[Olympe] Drone has been released")
                self.in_the_air = True
            else:
                logger.error("[Olympe] Dropping procedure timed out, canceling it")
                self.drone(UserTakeOff(0)).wait().success()
        except Exception as e:
            logger.error(f"[Olympe] Prepare for drop failed {e}")

    async def set_camera_angle(self, angle: float) -> None:
        raise NotImplementedError("set_camera_angle not implemented for OlympeCommander")

    async def set_pcmds(self, roll: int | None, pitch: int | None, yaw: int | None, gaz: int | None) -> None:
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
        if not self.in_the_air:
            return

        if roll is None or pitch is None or yaw is None or gaz is None:
            return
        else:
            try:
                assert self.drone(PCMD(1, roll, pitch, yaw, gaz, 0)).wait().success()
            except Exception as e:
                logger.error(f"[Olympe] PCMD failed {e}")

    async def emergency(self) -> None:
        """
        /! DO NOT CALL THIS FUNCTION IF YOU ARE NOT SURE OF WHAT YOU ARE DOING /!

        Cut out the motors. This cuts immediatly the motors. The drone will fall. This command is sent on a dedicated high priority buffer which will infinitely retry to send it if the command is not delivered.
        """
        self.drone(Emergency())
