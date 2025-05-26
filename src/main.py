import argparse
import asyncio
import logging
import signal
import traceback

from commanders.mavsdk_commander import MAVSDKCommander
from commanders.olympe_commander import OlympeCommander
from utils import follow_loop, manual_control

# Define terminal color codes
TERMINAL_COLORS_CODE = {
    "DEBUG": "\033[1;34m",
    "INFO": "\033[1;32m",
    "WARNING": "\033[1;33m",
    "ERROR": "\033[1;31m",
    "RESET": "\033[0m",
}


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_message = super().format(record)
        log_level = record.levelname
        color_code = TERMINAL_COLORS_CODE.get(log_level, TERMINAL_COLORS_CODE["RESET"])
        return f"{color_code}{log_message}{TERMINAL_COLORS_CODE['RESET']}"


# Configure the logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create a handler for stderr
stderr_handler = logging.StreamHandler()
stderr_handler.setFormatter(ColoredFormatter("%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

# Create a handler for the file
file_handler = logging.FileHandler("drone-coordination.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

# Add both handlers to the logger
logger.addHandler(stderr_handler)
logger.addHandler(file_handler)


async def show_help():
    print("Help: Use the following commands:")
    print("/takeoff_follower - Follower drone takeoff")
    print("/follow - Start following logic")
    print("/prepare_for_drop - Prepare follower to be dropped from the leader drone")
    print("/manual - Control follower drone with RC")
    print("/help - Show this help message")
    print("/exit - Exit")
    print("Ctrl-C to exit")


async def handle_command(command, leader, follower):
    """Match the command and call the appropriate function."""
    match command:
        case "/takeoff_follower":
            logger.debug("takeoff_follower")
        case "/follow":
            logger.info("Starting follow loop...")
            await follow_loop(leader, follower)
        case "/prepare_for_drop":
            logger.debug(("Preparing follower to be dropped from the leader drone..."))
            await follower.prepare_for_drop()
        case "/manual":
            logger.debug("Starting manual control loop...")
            await manual_control(follower)
        case "/exit":
            logger.warning("Exiting...")
            raise KeyboardInterrupt()
        case "/help":
            await show_help()
        case _:
            logger.error(f"Unknown command: {command}")


async def listen_for_commands(leader, follower):
    """Wait for commands asynchronously using signals."""
    # loop = asyncio.get_event_loop()

    # def on_signal_received(signum, frame):
    #     """Handles the SIGUSR1 signal and triggers command input."""
    #     print("Command received. Please enter your command:")

    # # Corrected signal handler: passing `signum` and `frame` parameters
    # loop.add_signal_handler(signal.SIGUSR1, on_signal_received, signal.SIGUSR1, None)

    try:
        while True:
            command = input("Enter command (/help for list of commands): ")
            await handle_command(command, leader, follower)
    except KeyboardInterrupt:
        logger.warning("\nCtrl-C detected. Exiting gracefully...")
        return
    except Exception as e:
        logger.error(f"\nError in command processing: {e}")
        traceback.print_exc()
        return


async def cleanup(leader, follower):
    """Clean up resources and disconnect from drones."""
    logger.info("Cleaning up resources...")
    tasks = []

    if follower:
        tasks.append(follower.set_pcmds(0, 0, 0, 0))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    logger.debug("Cleanup completed.")


# Main entry point
async def run():
    parser = argparse.ArgumentParser(description="Follow-me between two drones")

    # Require that --mavsdk_drone is used, even if the address is not specified
    parser.add_argument(
        "--mavsdk_drone",
        help="MAVSDK connection string (default: udp://:14550)",
        nargs="?",
        const="udp://:14550",
        default=None,
    )

    # Either --olympe_drone or --bebop_drone must be provided, but their values are optional
    parser.add_argument(
        "--olympe_drone",
        help="Parrot Olympe IP (optional)",
        nargs="?",
        const="192.168.42.1",
        default=None,
    )

    args = parser.parse_args()

    # Enforce --mavsdk_drone must be specified (even without a value)
    if args.mavsdk_drone is None:
        parser.error("--mavsdk_drone must be specified (address is optional)")

    # Enforce at least one of --olympe_drone or --bebop_drone must be provided
    if args.olympe_drone is None and args.bebop_drone is None:
        parser.error("At least one of --olympe_drone or --bebop_drone must be specified (addresses are optional)")

    leader = None
    follower = None

    if args.mavsdk_drone:
        leader = MAVSDKCommander(args.mavsdk_drone)
        logger.debug(f"Using MAVSDK commander as leader with address {args.mavsdk_drone}")
    if args.olympe_drone:
        follower = OlympeCommander(args.olympe_drone)
        logger.debug(f"Using Olympe commander as follower with address {args.olympe_drone}")
    else:
        raise ValueError("No drone specified")

    if leader and follower:
        try:
            task = asyncio.gather(follower.connect())
            await task
        except Exception as e:
            logger.error(f"Error connecting to drones: {e}")
            await cleanup(leader, follower)
            return

    try:
        await listen_for_commands(leader, follower)
    finally:
        await cleanup(leader, follower)


def signal_handler(sig, frame):
    """Handle external signals like SIGTERM."""
    logger.warning(f"\nReceived signal {sig}. Exiting gracefully...")
    # This will raise a KeyboardInterrupt in the main thread
    raise KeyboardInterrupt()


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.warning("Program terminated by user.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        traceback.print_exc()
