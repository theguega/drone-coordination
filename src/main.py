import argparse
import asyncio

from commanders.bebop_commander import BebopCommander
from commanders.mavsdk_commander import MAVSDKCommander
from commanders.olympe_commander import OlympeCommander
from follow_logic import follow_loop
from src.ui import UI


async def run_follow_logic(args):
    # Instantiate commanders
    leader = MAVSDKCommander(args.mavsdk_drone)
    if args.olympe_drone:
        follower = OlympeCommander(args.olympe_drone)
    elif args.bebop_drone:
        follower = BebopCommander(args.bebop_drone)
    else:
        raise ValueError("Must specify either --olympe_drone or --bebop_drone")

    # Connect to both drones
    await asyncio.gather(leader.connect(), follower.connect())

    # Run follow-me behavior
    await follow_loop(leader, follower)

    # Disconnect
    await asyncio.gather(leader.disconnect(), follower.disconnect())


async def run():
    parser = argparse.ArgumentParser(description="Follow-me between two drones")
    parser.add_argument(
        "--mavsdk_drone", required=True, help="MAVSDK connection string"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--olympe_drone", help="Parrot Olympe IP")
    group.add_argument("--bebop_drone", help="Parrot Bebop IP (future)")
    args = parser.parse_args()

    # Run the UI
    drone_type_options = ["Bebop", "Mavsdk", "Olympe"]
    ui = UI(drone_type_options)

    def start_follow_logic():
        asyncio.create_task(run_follow_logic(args))

    ui.button1.configure(command=start_follow_logic)  # Assign follow logic to button1

    ui.mainloop()


if __name__ == "__main__":
    asyncio.run(run())
