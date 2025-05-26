import asyncio
import threading

from commanders.mavsdk_commander import JOYSTICK_DEADZONE
from commanders.olympe_commander import OlympeCommander
from pyPS4Controller.controller import Controller

# Constants
JOYSTICK_DEADZONE = 500
JOYSTICK_SATURATION = 32767
UPDATE_DEADZONE = 2

# Background asyncio loop
background_loop = asyncio.new_event_loop()


def run_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=run_background_loop, args=(background_loop,), daemon=True).start()


# Decorator for joystick deadzone
def apply_joystick_deadzone(function):
    def wrapper(self, value):
        if abs(value) > JOYSTICK_DEADZONE:
            return function(self, value)
        else:
            return function(self, 0)

    return wrapper


class MyController(Controller):
    def __init__(self, drone: OlympeCommander, **kwargs):
        Controller.__init__(self, **kwargs)
        self.commander = drone
        self.current_pcmd = {"roll": 0, "pitch": 0, "yaw": 0, "gaz": 0}

    def _send_pcmds(self):
        asyncio.run_coroutine_threadsafe(self.commander.set_pcmds(self.current_pcmd.get("roll"), self.current_pcmd.get("pitch"), self.current_pcmd.get("yaw"), self.current_pcmd.get("gaz")), background_loop)

    def on_x_press(self):
        asyncio.run_coroutine_threadsafe(self.commander.takeoff(), background_loop)

    def on_x_release(self):
        # print("on_x_release")
        pass

    def on_triangle_press(self):
        print("on_triangle_press")

    def on_triangle_release(self):
        print("on_triangle_release")

    def on_circle_press(self):
        asyncio.run_coroutine_threadsafe(self.commander.land(), background_loop)

    def on_circle_release(self):
        # print("on_circle_release")
        pass

    def on_square_press(self):
        asyncio.run_coroutine_threadsafe(self.commander.prepare_for_drop(), background_loop)

    def on_square_release(self):
        print("on_square_release")

    def on_L1_press(self):
        print("on_L1_press")

    def on_L1_release(self):
        print("on_L1_release")

    def on_L2_press(self, value):
        # print("on_L2_press: {}".format(value))
        pass

    def on_L2_release(self):
        # print("on_L2_release")
        pass

    def on_R1_press(self):
        print("on_R1_press")

    def on_R1_release(self):
        print("on_R1_release")

    def on_R2_press(self, value):
        # print("on_R2_press: {}".format(value))
        pass

    def on_R2_release(self):
        # print("on_R2_release")
        pass

    def on_up_arrow_press(self):
        print("on_up_arrow_press")

    def on_up_down_arrow_release(self):
        print("on_up_down_arrow_release")

    def on_down_arrow_press(self):
        print("on_down_arrow_press")

    def on_left_arrow_press(self):
        print("on_left_arrow_press")

    def on_left_right_arrow_release(self):
        print("on_left_right_arrow_release")

    def on_right_arrow_press(self):
        print("on_right_arrow_press")

    @apply_joystick_deadzone
    def on_L3_up(self, value):
        value = -(value / JOYSTICK_SATURATION) * 100
        if abs(self.current_pcmd["gaz"] - value) > UPDATE_DEADZONE or value == 0:
            self.current_pcmd["gaz"] = int(value)
            self._send_pcmds()

    @apply_joystick_deadzone
    def on_L3_down(self, value):
        value = -(value / JOYSTICK_SATURATION) * 100
        if abs(self.current_pcmd["gaz"] - value) > UPDATE_DEADZONE or value == 0:
            self.current_pcmd["gaz"] = int(value)
            self._send_pcmds()

    @apply_joystick_deadzone
    def on_L3_left(self, value):
        value = (value / JOYSTICK_SATURATION) * 100
        if abs(self.current_pcmd["yaw"] - value) > UPDATE_DEADZONE or value == 0:
            self.current_pcmd["yaw"] = int(value)
            self._send_pcmds()

    @apply_joystick_deadzone
    def on_L3_right(self, value):
        value = (value / JOYSTICK_SATURATION) * 100
        if abs(self.current_pcmd["yaw"] - value) > UPDATE_DEADZONE or value == 0:
            self.current_pcmd["yaw"] = int(value)
            self._send_pcmds()

    def on_L3_y_at_rest(self):
        self.current_pcmd["gaz"] = 0
        self._send_pcmds()

    def on_L3_x_at_rest(self):
        self.current_pcmd["yaw"] = 0
        self._send_pcmds()

    def on_L3_press(self):
        print("on_L3_press")

    def on_L3_release(self):
        print("on_L3_release")

    @apply_joystick_deadzone
    def on_R3_up(self, value):
        value = -(value / JOYSTICK_SATURATION) * 100
        if abs(self.current_pcmd["pitch"] - value) > UPDATE_DEADZONE or value == 0:
            self.current_pcmd["pitch"] = int(value)
            self._send_pcmds()

    @apply_joystick_deadzone
    def on_R3_down(self, value):
        value = -(value / JOYSTICK_SATURATION) * 100
        if abs(self.current_pcmd["pitch"] - value) > UPDATE_DEADZONE or value == 0:
            self.current_pcmd["pitch"] = int(value)
            self._send_pcmds()

    @apply_joystick_deadzone
    def on_R3_left(self, value):
        value = (value / JOYSTICK_SATURATION) * 100
        if abs(self.current_pcmd["roll"] - value) > UPDATE_DEADZONE or value == 0:
            self.current_pcmd["roll"] = int(value)
            self._send_pcmds()

    @apply_joystick_deadzone
    def on_R3_right(self, value):
        value = (value / JOYSTICK_SATURATION) * 100
        if abs(self.current_pcmd["roll"] - value) > UPDATE_DEADZONE or value == 0:
            self.current_pcmd["roll"] = int(value)
            self._send_pcmds()

    def on_R3_y_at_rest(self):
        self.current_pcmd["pitch"] = 0
        self._send_pcmds()

    def on_R3_x_at_rest(self):
        self.current_pcmd["roll"] = 0
        self._send_pcmds()

    def on_R3_press(self):
        print("on_R3_press")

    def on_R3_release(self):
        print("on_R3_release")

    def on_options_press(self):
        print("on_options_press")

    def on_options_release(self):
        print("on_options_release")

    def on_share_press(self):
        print("on_share_press")

    def on_share_release(self):
        print("on_share_release")

    def on_playstation_button_press(self):
        print("on_playstation_button_press")

    def on_playstation_button_release(self):
        print("on_playstation_button_release")
