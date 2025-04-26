import os

import olympe

DRONE_IP = os.environ.get("ARSDK_DEVICE_IP", "192.168.42.1")


def test_physical_drone():
    drone = olympe.Drone(DRONE_IP)
    drone.connect()
    drone.disconnect()


if __name__ == "__main__":
    test_physical_drone()
