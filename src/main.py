import argparse
import asyncio
import signal
import traceback

from commanders.mavsdk_commander import MAVSDKCommander
from commanders.olympe_commander import OlympeCommander
from utils import follow_loop, manual_control


async def show_help():
    print("Help: Use the following commands:")
    print("/takeoff_follower - Follower drone takeoff")
    print("/follow - Start following logic")
    print("/prepare_for_release - Prepare follower to be dropped from the leader drone")
    print("/control_follower - Control follower drone with RC")
    print("/help - Show this help message")
    print("Ctrl-C to exit")


async def handle_command(command, leader, follower):
    """Match the command and call the appropriate function."""
    match command:
        case "/takeoff_follower":
            print("takeoff_follower")
        case "/follow":
            print("Starting follow loop...")
            try:
                await follow_loop(leader, follower)
            except Exception as e:
                print(f"Error in follow loop: {e}")
                traceback.print_exc()
        case "/prepare_for_release":
            print(("Preparing follower to be bropped from the leader drone..."))
            try:
                await follower.prepare_for_release()
            except Exception as e:
                print(f"Error preparing drone for drop: {e}")
                traceback.print_exc()
        case "/control_follower":
            try:
                await manual_control(follower)
            except Exception as e:
                print(f"Error in manual control: {e}")
                traceback.print_exc()
        case "/help":
            await show_help()
        case _:
            print(f"Unknown command: {command}")


async def listen_for_commands(leader, follower):
    """Wait for commands asynchronously using signals."""
    loop = asyncio.get_event_loop()

    def on_signal_received(signum, frame):
        """Handles the SIGUSR1 signal and triggers command input."""
        print("Command received. Please enter your command:")

    # Corrected signal handler: passing `signum` and `frame` parameters
    loop.add_signal_handler(signal.SIGUSR1, on_signal_received, signal.SIGUSR1, None)

    try:
        while True:
            command = input("Enter command (/help for list of commands): ")
            await handle_command(command, leader, follower)
    except KeyboardInterrupt:
        print("\nCtrl-C detected. Exiting gracefully...")
        return
    except Exception as e:
        print(f"\nError in command processing: {e}")
        traceback.print_exc()
        return


async def cleanup(leader, follower):
    """Clean up resources and disconnect from drones."""
    print("Cleaning up resources...")
    tasks = []

    if leader:
        tasks.append(leader.disconnect())
    if follower:
        tasks.append(follower.disconnect())

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    print("Cleanup completed.")


# Main entry point
async def run():
    parser = argparse.ArgumentParser(description="Follow-me between two drones")

    # Require that --mavsdk_drone is used, even if the address is not specified
    parser.add_argument(
        "--mavsdk_drone",
        help="MAVSDK connection string (default: udp://:14540)",
        nargs="?",
        const="udp://:14540",
        default=None,
    )

    # Either --olympe_drone or --bebop_drone must be provided, but their values are optional
    parser.add_argument(
        "--olympe_drone",
        help="Parrot Olympe IP (optional)",
        nargs="?",
        const="10.202.0.1",
        default=None,
    )

    args = parser.parse_args()

    # Enforce --mavsdk_drone must be specified (even without a value)
    if args.mavsdk_drone is None:
        parser.error("--mavsdk_drone must be specified (address is optional)")

    # Enforce at least one of --olympe_drone or --bebop_drone must be provided
    if args.olympe_drone is None and args.bebop_drone is None:
        parser.error(
            "At least one of --olympe_drone or --bebop_drone must be specified (addresses are optional)"
        )

    leader = None
    follower = None

    if args.mavsdk_drone:
        leader = MAVSDKCommander(args.mavsdk_drone)
        print("Using MAVSDK commander as leader with address", args.mavsdk_drone)
    if args.olympe_drone:
        follower = OlympeCommander(args.olympe_drone)
        print("Using Olympe commander as follower with address", args.olympe_drone)
    else:
        raise ValueError("No drone specified")

    if leader and follower:
        try:
            task = asyncio.gather(leader.connect(), follower.connect())
            await task
        except Exception as e:
            print(f"Error connecting to drones: {e}")
            await cleanup(leader, follower)
            return

    try:
        await listen_for_commands(leader, follower)
    finally:
        await cleanup(leader, follower)


def signal_handler(sig, frame):
    """Handle external signals like SIGTERM."""
    print(f"\nReceived signal {sig}. Exiting gracefully...")
    # This will raise a KeyboardInterrupt in the main thread
    raise KeyboardInterrupt()


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Program terminated by user.")
    except Exception as e:
        print(f"Unhandled exception: {e}")
        traceback.print_exc()
