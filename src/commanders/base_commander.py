import abc
from typing import Tuple


class BaseCommander(abc.ABC):
    """
    Abstract base class defining the commander interface.
    """

    def __init__(self, address: str):
        self.address = address

    @abc.abstractmethod
    async def connect(self) -> None:
        """Establish connection to the drone."""
        pass

    @abc.abstractmethod
    async def takeoff(self) -> None:
        """Takeoff the drone."""
        pass

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Terminate connection to the drone."""
        pass

    @abc.abstractmethod
    async def get_position(self) -> Tuple[float, float, float]:
        """
        Retrieve current (latitude, longitude, altitude).
        """
        pass

    @abc.abstractmethod
    async def goto_position(
        self, latitude: float, longitude: float, altitude: float
    ) -> None:
        """
        Command drone to fly to specified GPS position.
        """
        pass

    @abc.abstractmethod
    async def land(self) -> None:
        """
        Land the drone safely.
        """
        pass

    @abc.abstractmethod
    async def prepare_for_drop(self) -> None:
        """Prepare the drone to be dropped from a fixed height and takeoff."""
        pass

    @abc.abstractmethod
    async def set_camera_angle(self, angle: float) -> None:
        """
        Set camera angle in degrees (-90 to 90) with -90 being straight down.
        """
        pass

    @abc.abstractmethod
    async def set_pcmds(
        self, roll: float, pitch: float, yaw: float, gaz: float
    ) -> None:
        """
        Set the drone's pitch/roll/yaw/gaz commands.
        """
        pass
