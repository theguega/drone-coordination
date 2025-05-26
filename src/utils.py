import asyncio
import logging
from typing import Optional, Tuple

from geographiclib.geodesic import Geodesic

from controller import MyController

# Configuration constants with default values
DEFAULT_FOLLOW_DIST_M = 5.0  # Target follow distance in meters
DEFAULT_MIN_DIST_M = 2.0  # Minimum safe distance before stopping follower
DEFAULT_MAX_DIST_M = 30.0  # Maximum distance before limiting follower movement
DEFAULT_ALT_OFFSET_M = 2.0  # Altitude offset from leader
DEFAULT_RETRY_DELAY = 0.5  # Delay before retrying after communication failure
DEFAULT_TIMEOUT = 2.0  # Timeout for position requests

# Set up logging
logger = logging.getLogger()


class PositionData:
    """Store drone position data with validity tracking"""

    def __init__(self, lat: float = 0.0, lon: float = 0.0, alt: float = 0.0):
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.timestamp = asyncio.get_event_loop().time()

    @property
    def is_valid(self) -> bool:
        """Check if position data is recent (< 3 seconds old)"""
        now = asyncio.get_event_loop().time()
        return now - self.timestamp < 3.0


def compute_follow_point(
    leader_lat: float,
    leader_lon: float,
    follower_lat: float,
    follower_lon: float,
    distance: float,
) -> Tuple[float, float]:
    """
    Compute target latitude/longitude at `distance` meters from leader,
    along the line toward the follower.

    Args:
        leader_lat: Leader drone latitude in degrees
        leader_lon: Leader drone longitude in degrees
        follower_lat: Follower drone latitude in degrees
        follower_lon: Follower drone longitude in degrees
        distance: Target distance in meters

    Returns:
        Tuple of (target_latitude, target_longitude) in degrees
    """
    # Use the WGS84 ellipsoid parameters
    geod = Geodesic(6378137, 1 / 298.257223563)  # WGS84 parameters (a=semi-major axis, f=flattening)
    inv = geod.Inverse(leader_lat, leader_lon, follower_lat, follower_lon)
    bearing = inv["azi1"]
    dest = geod.Direct(leader_lat, leader_lon, bearing, distance)
    return dest["lat2"], dest["lon2"]


async def safe_get_position(drone_commander, timeout: float = DEFAULT_TIMEOUT) -> Optional[Tuple[float, float, float]]:
    """
    Safely get drone position with timeout handling

    Returns:
        Tuple of (latitude, longitude, altitude) or None if request fails
    """
    try:
        position_task = asyncio.create_task(drone_commander.get_position())
        return await asyncio.wait_for(position_task, timeout=timeout)
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"Failed to get position: {e}")
        return None


async def follow_loop(
    leader_commander,
    follower_commander,
    interval: float = 1.0,
    min_dist: float = DEFAULT_MIN_DIST_M,
    follow_dist: float = DEFAULT_FOLLOW_DIST_M,
    max_dist: float = DEFAULT_MAX_DIST_M,
    alt_offset: float = DEFAULT_ALT_OFFSET_M,
) -> None:
    """
    Continuously compute and send follow-me commands to maintain specified distance.
    If drones come too close, the follower will stop moving.

    Args:
        leader_commander: Commander object for the leader drone (must provide get_position method)
        follower_commander: Commander object for the follower drone (must provide goto_position and set_pcmds methods)
        interval: Update interval in seconds
        min_dist: Minimum safe distance before stopping follower (meters)
        follow_dist: Target follow distance (meters)
        max_dist: Maximum distance limit (meters)
        alt_offset: Height offset from leader (meters)
    """
    # Create single geodesic calculator for repeated use
    geod = Geodesic(6378137, 1 / 298.257223563)  # WGS84 parameters

    # Smoothing variables
    target_position = PositionData()

    try:
        consecutive_failures = 0

        while True:
            # Retrieve positions with timeout handling
            leader_position = await safe_get_position(leader_commander)
            follower_position = await safe_get_position(follower_commander)

            # Check if both position fetches were successful
            if leader_position is None or follower_position is None:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    logger.warning("Multiple consecutive position failures - stopping follower")
                    await follower_commander.set_pcmds(0, 0, 0, 0)
                    await asyncio.sleep(DEFAULT_RETRY_DELAY)
                    continue
                else:
                    await asyncio.sleep(DEFAULT_RETRY_DELAY)
                    continue

            consecutive_failures = 0
            lead_lat, lead_lon, lead_alt = leader_position
            foll_lat, foll_lon, foll_alt = follower_position

            # Compute separation distance
            geodesic_result = geod.Inverse(lead_lat, lead_lon, foll_lat, foll_lon)
            separation_distance = geodesic_result["s12"]
            bearing = geodesic_result["azi1"]

            # Check if drones are too close
            if separation_distance < min_dist:
                logger.info(f"Too close ({separation_distance:.1f}m < {min_dist}m) - stopping follower")
                await follower_commander.set_pcmds(0, 0, 0, 0)
                await asyncio.sleep(interval)
                continue

            # Determine follow distance based on current separation
            actual_follow_dist = min(follow_dist, max(0, separation_distance - min_dist))
            if separation_distance > max_dist:
                logger.warning(f"Exceeded maximum distance ({separation_distance:.1f}m > {max_dist}m)")
                # Use maximum allowed distance to prevent further separation
                actual_follow_dist = max(0, separation_distance - max_dist / 2)

            # Compute target follow point and desired altitude
            tgt_lat, tgt_lon = compute_follow_point(lead_lat, lead_lon, foll_lat, foll_lon, actual_follow_dist)
            tgt_alt = lead_alt + alt_offset

            # Apply simple smoothing (weight: 30% previous target, 70% new target)
            if target_position.is_valid:
                smooth_lat = 0.3 * target_position.lat + 0.7 * tgt_lat
                smooth_lon = 0.3 * target_position.lon + 0.7 * tgt_lon
                smooth_alt = 0.3 * target_position.alt + 0.7 * tgt_alt
            else:
                smooth_lat, smooth_lon, smooth_alt = tgt_lat, tgt_lon, tgt_alt

            # Update target position for next iteration
            target_position = PositionData(smooth_lat, smooth_lon, smooth_alt)

            logger.info(f"Moving follower to {smooth_lat:.6f}, {smooth_lon:.6f}, alt {smooth_alt:.1f}m (separation: {separation_distance:.1f}m, bearing: {bearing:.1f}°)")

            # Send command
            try:
                await follower_commander.goto_position(smooth_lat, smooth_lon, smooth_alt)
            except Exception as cmd_error:
                logger.error(f"Failed to send goto command: {cmd_error}")

            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        logger.info("Follow loop cancelled - stopping follower")
        await follower_commander.set_pcmds(0, 0, 0, 0)
    except KeyboardInterrupt:
        logger.info("Follow loop interrupted - stopping follower")
        await follower_commander.set_pcmds(0, 0, 0, 0)
    except Exception as e:
        logger.error(f"Error in follow loop: {e}")
        try:
            await follower_commander.set_pcmds(0, 0, 0, 0)
        except Exception as stop_error:
            logger.error(f"Error stopping follower after exception: {stop_error}")


async def manual_control(follower) -> None:
    """Continuously read PS4 controller commands and send them to the drone."""
    try:
        controller = MyController(drone=follower, interface="/dev/input/js1", connecting_using_ds4drv=False)
        controller.listen()
    except asyncio.CancelledError:
        logger.warning("Manual control loop cancelled – stopping both drones by sending pcmds")
        await follower.set_pcmds(0, 0, 0, 0)
    except KeyboardInterrupt:
        logger.warning("Manual control loop interrupted – stopping both drones by sending pcmds")
        await follower.set_pcmds(0, 0, 0, 0)
    except Exception as e:
        logger.error(f"Error in manual control loop: {e}")
        await follower.set_pcmds(0, 0, 0, 0)
