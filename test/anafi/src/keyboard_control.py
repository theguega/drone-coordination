import olympe
import time
import keyboard

DRONE_IP = "192.168.42.79"

def keyboard_control():
    drone = olympe.Drone(DRONE_IP)
    try:
        drone.connect(timeout=10)
        print("Drone connected successfully!")

        print("Keyboard bindings:")
        print("  - z: Move forward")
        print("  - s: Move backward")
        print("  - q: Move left")
        print("  - d: Move right")
        print("  - a: Rotate left")
        print("  - e: Rotate right")
        print("  - space: Takeoff")
        print("  - l: Land")
        print("  - p: Emergency stop")
        print("  - h: Hold position")

        while True:
            if keyboard.is_pressed('z'):
                drone.forward(0.5)
            elif keyboard.is_pressed('s'):
                drone.backward(0.5)
            elif keyboard.is_pressed('q'):
                drone.left(0.5)
            elif keyboard.is_pressed('d'):
                drone.right(0.5)
            elif keyboard.is_pressed('a'):
                drone.rotate_left(30)
            elif keyboard.is_pressed('e'):
                drone.rotate_right(30)
            elif keyboard.is_pressed('space'):
                drone.takeoff()
            elif keyboard.is_pressed('l'):
                drone.land()
            elif keyboard.is_pressed('p'):
                drone.emergency()
            elif keyboard.is_pressed('h'):
                drone.hover()
            elif keyboard.is_pressed('esc'):
                break

            time.sleep(0.1)

    except olympe.exceptions.OlympeTimeout as e:
        print(f"Error: Drone connection timeout: {e}")
    finally:
        drone.disconnect()
        print("Drone disconnected.")

if __name__ == "__main__":
    keyboard_control()
