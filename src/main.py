import argparse
import asyncio

from commanders.mavsdk_commander import MAVSDKCommander
from commanders.olympe_commander import OlympeCommander

# from commanders.bebop_commander import BebopCommander
from follow_logic import follow_loop


async def run():
    parser = argparse.ArgumentParser(description="Follow-me between two drones")
    parser.add_argument(
        "--mavsdk_drone", required=True, help="MAVSDK connection string"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--olympe_drone", help="Parrot Olympe IP")
    group.add_argument("--bebop_drone", help="Parrot Bebop IP (future)")
    args = parser.parse_args()

    # Instantiate commanders
    leader = MAVSDKCommander(args.mavsdk_drone)
    if args.olympe_drone:
        follower = OlympeCommander(args.olympe_drone)
    else:
        # from commanders.bebop_commander import BebopCommander
        # follower = BebopCommander(args.bebop_drone)
        pass

    # Connect to both drones
    await asyncio.gather(leader.connect(), follower.connect())

    # Run follow-me behavior
    await follow_loop(leader, follower)

    # Disconnect
    await asyncio.gather(leader.disconnect(), follower.disconnect())


if __name__ == "__main__":
    asyncio.run(run())
