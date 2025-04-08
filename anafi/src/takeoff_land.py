import olympe
import os
import time

DRONE_IP = os.environ.get("ARSDK_DEVICE_IP", "192.168.42.1")


from olympe.messages.ardrone3.PilotingState import FlyingStateChanged
from olympe.messages.ardrone3.Piloting import TakeOff, Landing

def test_takeoff():
    drone = olympe.Drone(DRONE_IP)
    drone.connect()

    # Wait until the drone is landed (ready for takeoff)
    if not drone(FlyingStateChanged(state="landed")).wait().success():
        print("Drone is not in landed state. Aborting.")
        drone.disconnect()
        return

    # Attempt to take off
    if not drone(TakeOff()).wait().success():
        print("Takeoff failed!")
        drone.disconnect()
        return

    time.sleep(3)  # Hover for a few seconds

    # Land the drone
    if not drone(Landing()).wait().success():
        print("Landing failed!")

    drone.disconnect()


if __name__ == "__main__":
    test_takeoff()
