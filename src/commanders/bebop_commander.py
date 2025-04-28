import asyncio
from typing import Tuple

import roslaunch
import rospy
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import Empty


class BebopCommander(BaseCommander):
    """
    A commander that wraps the bebop_autonomy ROS driver.
    """

    def __init__(self, address: str, namespace: str = "bebop"):
        super().__init__(address)
        self.namespace = namespace
        self.launch = None
        self.takeoff_pub = None
        self.land_pub = None

    async def connect(self) -> None:
        """
        1. Set the drone IP via ROS parameter.
        2. Initialize ROS node.
        3. Launch the bebop_driver node.
        4. Publish a takeoff command.
        """
        # 1. Set IP parameter so the ROS driver knows where to connect :contentReference[oaicite:3]{index=3}
        rospy.set_param(f"/{self.namespace}/ip", self.address)

        # 2. Initialize ROS (only once)
        if not rospy.core.is_initialized:
            rospy.init_node(f"{self.namespace}_commander", anonymous=True)

        # 3. Launch the ROS driver via roslaunch API
        uuid = roslaunch.rlutil.get_or_generate_uuid(None, False)
        roslaunch.configure_logging(uuid)
        launch_files = [
            "bebop_driver/bebop_node.launch",
            f"ip:={self.address}",
            f"namespace:={self.namespace}",
        ]
        self.launch = roslaunch.parent.ROSLaunchParent(uuid, launch_files)
        self.launch.start()  # this returns immediately :contentReference[oaicite:4]{index=4}

        # 4. Prepare publishers for takeoff and land
        ns = f"/{self.namespace}"
        self.takeoff_pub = rospy.Publisher(f"{ns}/takeoff", Empty, queue_size=1)
        self.land_pub = rospy.Publisher(f"{ns}/land", Empty, queue_size=1)

        # Give driver a moment to start up
        await asyncio.sleep(2.0)
        # Send the takeoff command
        self.takeoff_pub.publish(
            Empty()
        )  # takes off the drone :contentReference[oaicite:5]{index=5}

    async def disconnect(self) -> None:
        """
        Shutdown the ROS driver. Optionally land first.
        """
        # Land if still flying
        if self.land_pub:
            self.land_pub.publish(
                Empty()
            )  # lands the drone :contentReference[oaicite:6]{index=6}
            await asyncio.sleep(2.0)

        # Shutdown the launch file
        if self.launch:
            self.launch.shutdown()

    async def get_position(self) -> Tuple[float, float, float]:
        """
        Wait for one NavSatFix message and return (lat, lon, alt).
        """
        topic = f"/{self.namespace}/fix"
        msg: NavSatFix = rospy.wait_for_message(
            topic, NavSatFix, timeout=5.0
        )  # GPS fix :contentReference[oaicite:7]{index=7}
        return msg.latitude, msg.longitude, msg.altitude

    async def goto_position(
        self, latitude: float, longitude: float, altitude: float
    ) -> None:
        """
        Stub: bebop_autonomy does not support waypoint navigation natively.
        To implement, consider publishing velocity commands to /<ns>/cmd_vel
        or using the onboard flight-plan API (autoflight/start, etc.). :contentReference[oaicite:8]{index=8}
        """
        raise NotImplementedError(
            "Waypoint navigation requires a custom controller or use of the Bebop's flight-plan API."
        )

    async def land(self) -> None:
        """
        Land the drone immediately.
        """
        if self.land_pub:
            self.land_pub.publish(
                Empty()
            )  # lands the drone :contentReference[oaicite:9]{index=9}
