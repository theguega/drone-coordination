#!/usr/bin/env python3

import asyncio
import argparse
import math
import time
import json # Pour parser les données ZMQ
import zmq # Import ZMQ
import zmq.asyncio # Import le support asyncio pour ZMQ
from mavsdk import System
from mavsdk.action import ActionError
from mavsdk.telemetry import PositionVelocityNed, PositionInfo, PositionBody, PositionNed
from mavsdk.offboard import OffboardError, PositionNedYaw

# region --- Helper Functions for Geo Calculations ---
# ... (les fonctions get_distance_metres, get_bearing_degrees, get_location_metres restent inchangées) ...
def get_distance_metres(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS coordinates in meters using Haversine formula.
    Approximation, good for short distances.
    """
    R = 6371e3  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) * math.sin(delta_phi / 2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) * math.sin(delta_lambda / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def get_bearing_degrees(lat1, lon1, lat2, lon2):
    """ Calculate bearing between two points in degrees. """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dLon = lon2 - lon1
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    return bearing

def get_location_metres(lat, lon, bearing_deg, distance_m):
    """
    Calculate destination point given start point, bearing (degrees) and distance (meters).
    """
    R = 6371e3  # Earth radius in meters
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg)
    angular_distance = distance_m / R

    lat2 = math.asin(math.sin(lat_rad) * math.cos(angular_distance) +
                     math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing_rad))
    lon2 = lon_rad + math.atan2(math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat_rad),
                               math.cos(angular_distance) - math.sin(lat_rad) * math.sin(lat2))

    return math.degrees(lat2), math.degrees(lon2)
# endregion

class DroneCoordinator:
    # Ajout de zmq_bind_addr et zmq_timeout
    def __init__(self, vtol_address, fpv_address, follow_alt_offset, follow_dist, safety_dist, zmq_bind_addr, zmq_timeout):
        self.vtol_address = vtol_address
        self.fpv_address = fpv_address
        self.follow_alt_offset = follow_alt_offset
        self.follow_dist = follow_dist
        self.safety_dist = safety_dist
        self.zmq_bind_addr = zmq_bind_addr # Adresse sur laquelle le script écoute
        self.zmq_timeout = zmq_timeout # Timeout pour la réception ZMQ

        self.vtol_drone = System(mavsdk_server_address='localhost', port=50050)
        self.fpv_drone = System(mavsdk_server_address='localhost', port=50051)

        self.target_coords = None
        self.fpv_manual_takeover_requested = False

        # Initialiser le contexte ZMQ pour asyncio
        self.zmq_context = zmq.asyncio.Context()


    async def connect_drones(self):
        # ... (inchangé) ...
        """ Connects to both drones concurrently. """
        print("--- Connecting to Drones ---")
        connect_vtol = self.vtol_drone.connect(system_address=self.vtol_address)
        connect_fpv = self.fpv_drone.connect(system_address=self.fpv_address)

        try:
            # Wait for VTOL connection first - it's the primary system
            print(f"Connecting to VTOL drone at {self.vtol_address}...")
            await asyncio.wait_for(connect_vtol, timeout=15)
            print("VTOL Drone Connected!")
        except asyncio.TimeoutError:
            print(f"Error: Connection to VTOL drone ({self.vtol_address}) timed out!")
            return False

        print("Waiting for FPV drone release and connection...")
        # The FPV drone might only become available after physical release
        # Retry connecting for a while
        for attempt in range(10): # Try for ~50 seconds
             try:
                 print(f"Connecting to FPV drone at {self.fpv_address} (attempt {attempt+1})...")
                 # We don't use wait_for here, connect() itself might handle some internal timeout/retries
                 # If it fails quickly, we retry. If it hangs, the outer logic might need adjustment.
                 await self.fpv_drone.connect(system_address=self.fpv_address) # Re-call connect inside loop
                 # Check health after potential connection
                 async for state in self.fpv_drone.core.connection_state():
                      if state.is_connected:
                           print("FPV Drone Connected!")
                           return True # Both connected
                      else:
                           print("FPV not connected yet...")
                           await asyncio.sleep(2) # Wait before next check/attempt
             except Exception as e: # Catch potential exceptions during connect call
                 print(f"Error connecting to FPV on attempt {attempt+1}: {e}")

             print("Waiting 5 seconds before next FPV connection attempt...")
             await asyncio.sleep(5)


        print(f"Error: Could not connect to FPV drone ({self.fpv_address}) after multiple attempts.")
        return False

    async def wait_for_fpv_stabilization(self):
        # ... (inchangé) ...
        """ Waits until the FPV drone reports being stable (e.g., in Hold mode). """
        print("--- Waiting for FPV Drone to Stabilize After Release ---")
        required_mode = "HOLD" # Or LOITER, POSITION, etc. depending on FPV drone's autopilot config
        stabilized = False
        async for flight_mode in self.fpv_drone.telemetry.flight_mode():
             print(f"FPV Drone current mode: {flight_mode}")
             # Also check if it has a valid position lock and some altitude
             try:
                pos = await asyncio.wait_for(asyncio.ensure_future(self.get_position(self.fpv_drone)), timeout=1.0)
                if pos and pos.relative_altitude_m > 1.0: # Check if above 1m
                    # Convert enum to string for comparison
                    mode_str = str(flight_mode)
                    # Handle potential variations like "POSITION_CONTROL" vs "POSITION"
                    if required_mode in mode_str.upper():
                        print(f"FPV Drone stabilized in {flight_mode} mode at {pos.relative_altitude_m:.1f}m altitude.")
                        stabilized = True
                        break
                    else:
                         print(f"FPV Drone has position but is in {flight_mode} mode. Waiting for {required_mode}...")
                else:
                    print("FPV Drone waiting for valid position and altitude > 1m...")
             except asyncio.TimeoutError:
                print("Waiting for FPV position data...")
             except Exception as e:
                print(f"Error getting FPV position/mode: {e}")

             await asyncio.sleep(1)

        if not stabilized:
             print("Error: FPV Drone did not stabilize in the expected mode.")
             return False
        return True

    async def get_position(self, drone):
        # ... (inchangé) ...
        """ Safely fetches the current position (lat, lon, relative_alt). """
        try:
            # Get position once, requires drone to be actively streaming telemetry
            position = await asyncio.wait_for(
                asyncio.ensure_future(self._get_latest_position(drone)),
                timeout=2.0 # Timeout if no position received quickly
            )
            return position
        except asyncio.TimeoutError:
            print(f"Timeout waiting for position data from a drone.")
            return None
        except Exception as e:
            print(f"Error getting position: {e}")
            return None

    async def _get_latest_position(self, drone):
         """Helper to get the very next position update"""
         async for position in drone.telemetry.position():
              return position # Return the first one received


    async def run_follow_mode(self):
        # ... (inchangé - la logique de suivi reste la même) ...
        """ Manages the FPV drone following the VTOL drone. """
        print("--- Starting Follow Mode ---")
        in_safety_hold = False

        while not self.fpv_manual_takeover_requested:
            try:
                # Use asyncio.gather to fetch positions concurrently
                vtol_pos_task = asyncio.ensure_future(self.get_position(self.vtol_drone))
                fpv_pos_task = asyncio.ensure_future(self.get_position(self.fpv_drone))

                # Wait for both tasks to complete
                await asyncio.gather(vtol_pos_task, fpv_pos_task)

                vtol_pos = vtol_pos_task.result()
                fpv_pos = fpv_pos_task.result()


                if not vtol_pos or not fpv_pos:
                    print("Warning: Could not get position data for one or both drones. Skipping follow iteration.")
                    await asyncio.sleep(1)
                    continue

                # Calculate distance
                current_distance = get_distance_metres(vtol_pos.latitude_deg, vtol_pos.longitude_deg,
                                                       fpv_pos.latitude_deg, fpv_pos.longitude_deg)
                print(f"Distance between drones: {current_distance:.1f} m")

                # Safety Check
                if current_distance < self.safety_dist:
                    if not in_safety_hold:
                        print(f"WARNING: Drones too close ({current_distance:.1f}m < {self.safety_dist}m)! FPV drone entering safety hold.")
                        # Command FPV drone to hold position
                        try:
                            await self.fpv_drone.action.hold()
                            in_safety_hold = True
                        except ActionError as e:
                            print(f"Error commanding FPV drone to hold: {e}")
                    else:
                        # Already holding, just print a reminder
                         print(f"INFO: Still in safety hold distance ({current_distance:.1f}m). Manual intervention likely needed.")
                    # In safety hold, we stop sending goto commands and wait
                    await asyncio.sleep(2) # Check less frequently when holding
                    # TODO: Add logic here for manual override or automatic recovery if possible/desired
                    continue # Skip the rest of the loop while in safety hold
                else:
                    # If we were in safety hold but are now clear, allow movement again
                    if in_safety_hold:
                        print(f"INFO: Distance ({current_distance:.1f}m) now greater than safety distance ({self.safety_dist}m). Resuming follow.")
                        in_safety_hold = False
                        # May need to explicitly set mode back to OFFBOARD or GUIDED if hold changed it permanently
                        # For now, assume goto_location works if not actively holding

                # Calculate target position for FPV drone
                # Simple approach: Maintain position 'follow_dist' meters BEHIND the VTOL
                # Get VTOL's heading/velocity if available? Or just use bearing from FPV to VTOL?
                # Let's try maintaining a fixed offset relative to VTOL's current position.
                # Bearing from VTOL to FPV
                bearing_vtol_to_fpv = get_bearing_degrees(vtol_pos.latitude_deg, vtol_pos.longitude_deg,
                                                          fpv_pos.latitude_deg, fpv_pos.longitude_deg)

                # Target bearing: opposite direction (e.g., 180 degrees from current bearing)
                # This makes the FPV drone stay roughly at the same relative angle
                # A better approach might use VTOL's velocity vector if available (requires PositionVelocityNed)
                target_bearing = (bearing_vtol_to_fpv + 180) % 360 # Stay behind/opposite side

                target_lat, target_lon = get_location_metres(vtol_pos.latitude_deg, vtol_pos.longitude_deg,
                                                             target_bearing, self.follow_dist)

                target_alt = vtol_pos.relative_altitude_m + self.follow_alt_offset

                print(f"Commanding FPV to: Lat={target_lat:.6f}, Lon={target_lon:.6f}, Alt={target_alt:.1f}m")

                # Command FPV drone to move
                try:
                    await self.fpv_drone.action.goto_location(target_lat, target_lon, target_alt, 0) # Yaw = 0 (North) for simplicity
                except ActionError as e:
                    print(f"Error sending goto_location command to FPV drone: {e}")

                # --- Check for manual takeover signal ---
                # Example: Monitor VTOL flight mode
                try:
                    async for fm in self.vtol_drone.telemetry.flight_mode():
                         # Convert enum to string for comparison
                         mode_str = str(fm)
                         # Check if mode is HOLD or LOITER (common modes for pilot intervention)
                         if "HOLD" in mode_str.upper() or "LOITER" in mode_str.upper():
                             print(f"VTOL entered {fm} mode. Assuming pilot requests manual FPV control.")
                             self.fpv_manual_takeover_requested = True
                             break # Exit flight mode monitoring for this iteration
                         # Add short sleep to prevent tight loop if mode doesn't change
                         # await asyncio.sleep(0.1) # Removed: Causes delays if mode doesn't change immediately
                         break # Only check mode once per follow loop iteration
                except Exception as e:
                     print(f"Error checking VTOL flight mode: {e}")


            except Exception as e:
                print(f"Error in follow loop: {e}")
                # Decide if we should break or continue
                await asyncio.sleep(1) # Wait before retrying

            await asyncio.sleep(0.5) # Loop frequency

        print("--- Exiting Follow Mode ---")


    async def wait_for_manual_control_phase(self):
        # ... (inchangé jusqu'à l'appel de listen_for_apriltag_coords) ...
        """ Handles the transition to manual FPV control and waits for target coords. """
        print("--- Manual Control Phase ---")
        print("Stabilizing VTOL drone...")
        try:
            await self.vtol_drone.action.hold()
            print("VTOL drone is holding position.")
        except ActionError as e:
            print(f"Error commanding VTOL to hold: {e}")
            # Potentially critical error, may need to abort

        print("\n***********************************************************")
        print(" PILOT: You can now connect QGroundControl to the FPV drone")
        print(f"        Use UDP address: {self.fpv_address}")
        print("        Fly the FPV drone manually to identify the target.")
        print("***********************************************************\n")
        print("Script is now waiting for target coordinates from FPV drone via ZeroMQ...")

        # --- Appel de la fonction ZMQ ---
        self.target_coords = await self.listen_for_apriltag_coords_zmq()

        if self.target_coords:
            print(f"--- Target Coordinates Received via ZMQ: Lat={self.target_coords[0]}, Lon={self.target_coords[1]} ---")
            return True
        else:
            print("--- Failed to receive target coordinates via ZMQ (Timeout or Error) ---")
            return False

    # Nouvelle fonction pour écouter ZMQ
    async def listen_for_apriltag_coords_zmq(self):
        """
        Listens for AprilTag coordinates (lat, lon) sent via ZeroMQ PUSH/PULL.
        Binds a PULL socket and waits for a JSON message.
        """
        pull_socket = self.zmq_context.socket(zmq.PULL)
        try:
            print(f"Binding ZMQ PULL socket to {self.zmq_bind_addr}...")
            pull_socket.bind(self.zmq_bind_addr)
            print(f"Waiting for coordinates message... (Timeout: {self.zmq_timeout} seconds)")

            # Attend un message avec un timeout
            message_str = await asyncio.wait_for(
                pull_socket.recv_string(),
                timeout=self.zmq_timeout
            )

            print(f"Received ZMQ message: {message_str}")

            # Essayer de parser le JSON
            try:
                data = json.loads(message_str)
                if "latitude" in data and "longitude" in data:
                    lat = float(data["latitude"])
                    lon = float(data["longitude"])
                    # Validation basique des coordonnées (optionnel mais recommandé)
                    if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                         print("Coordinates parsed successfully.")
                         return (lat, lon)
                    else:
                         print("Error: Parsed coordinates out of valid range.")
                         return None
                else:
                    print("Error: Received JSON does not contain 'latitude' and 'longitude' keys.")
                    return None
            except json.JSONDecodeError:
                print("Error: Received message is not valid JSON.")
                return None
            except (TypeError, ValueError) as e:
                 print(f"Error parsing coordinate values: {e}")
                 return None

        except asyncio.TimeoutError:
            print(f"Error: Timeout ({self.zmq_timeout}s) waiting for ZMQ message on {self.zmq_bind_addr}")
            return None
        except zmq.ZMQError as e:
            print(f"ZMQ Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error while waiting for ZMQ message: {e}")
            return None
        finally:
            print("Closing ZMQ socket.")
            pull_socket.close()


    async def execute_final_positioning(self):
        # ... (inchangé) ...
         """ Commands drones for the final approach and positioning. """
         if not self.target_coords:
             print("Error: Cannot execute final positioning without target coordinates.")
             return

         target_lat, target_lon = self.target_coords

         print("--- Executing Final Positioning ---")

         # 1. Command FPV drone to clear the area
         print("Commanding FPV drone to move to a safe offset position...")
         try:
             fpv_current_pos = await self.get_position(self.fpv_drone)
             if fpv_current_pos:
                  # Move it 50m North (bearing 0) from its current location, maintain altitude
                  clear_lat, clear_lon = get_location_metres(fpv_current_pos.latitude_deg,
                                                            fpv_current_pos.longitude_deg,
                                                            0, 50) # 50 meters North
                  clear_alt = fpv_current_pos.relative_altitude_m
                  print(f"Sending FPV drone to clear zone: Lat={clear_lat:.6f}, Lon={clear_lon:.6f}, Alt={clear_alt:.1f}m")
                  await self.fpv_drone.action.goto_location(clear_lat, clear_lon, clear_alt, 0)
                  # We might want to wait here until it reaches the clear zone or for a timeout
                  await asyncio.sleep(10) # Give it some time to move
                  print("FPV drone clear command sent.")
             else:
                  print("Warning: Could not get FPV drone position to calculate clearing path. Skipping FPV move.")

         except ActionError as e:
             print(f"Error sending FPV drone to clear zone: {e}")
         except Exception as e:
             print(f"Unexpected error during FPV clearing: {e}")


         # 2. Command VTOL drone to position over the target
         print(f"Commanding VTOL drone to position over target: Lat={target_lat}, Lon={target_lon}")
         try:
             # Determine target altitude for VTOL (e.g., its current altitude or a standard mission alt)
             vtol_current_pos = await self.get_position(self.vtol_drone)
             target_alt_vtol = 15.0 # Default target altitude for VTOL over target
             if vtol_current_pos:
                 target_alt_vtol = vtol_current_pos.relative_altitude_m # Or maintain current alt
             else:
                  print(f"Warning: Could not get VTOL current altitude, using default {target_alt_vtol}m")


             print(f"VTOL target: Lat={target_lat:.6f}, Lon={target_lon:.6f}, Alt={target_alt_vtol:.1f}m")
             await self.vtol_drone.action.goto_location(target_lat, target_lon, target_alt_vtol, 0) # Yaw North
             print("VTOL positioning command sent. Monitoring arrival (basic)...")

             # Basic monitoring loop (could be more sophisticated)
             while True:
                  vtol_pos = await self.get_position(self.vtol_drone)
                  if not vtol_pos:
                       await asyncio.sleep(1)
                       continue

                  dist_to_target = get_distance_metres(vtol_pos.latitude_deg, vtol_pos.longitude_deg,
                                                      target_lat, target_lon)
                  print(f"VTOL distance to target: {dist_to_target:.1f}m")
                  if dist_to_target < 2.0: # Consider arrived if within 2 meters
                       print("VTOL has reached the target position.")
                       await self.vtol_drone.action.hold() # Hold position upon arrival
                       break
                  await asyncio.sleep(1)

         except ActionError as e:
             print(f"Error commanding VTOL to target position: {e}")
         except Exception as e:
              print(f"Unexpected error during VTOL positioning: {e}")

    async def run(self):
        """ Main execution flow """
        try:
            if not await self.connect_drones():
                return # Exit if connection fails

            if not await self.wait_for_fpv_stabilization():
                print("Aborting mission due to FPV stabilization failure.")
                return

            await self.run_follow_mode()

            if self.fpv_manual_takeover_requested:
                if await self.wait_for_manual_control_phase():
                    await self.execute_final_positioning()
                else:
                    print("Mission aborted after manual control phase (No coords received or error).")
            else:
                print("Follow mode ended unexpectedly (not by manual request). Mission aborted.")

            print("--- Mission Scenario Completed (or Aborted) ---")

        finally:
            # Assurer la fermeture du contexte ZMQ à la fin du programme
            print("Terminating ZMQ context.")
            self.zmq_context.term()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coordinate VTOL and FPV drones for a deployment and targeting mission.")
    parser.add_argument('--vtol-addr', type=str, default="serial:///dev/ttyAMA0:57600",
                        help="MAVSDK connection address for the VTOL drone")
    parser.add_argument('--fpv-addr', type=str, default="udp://:14541",
                        help="MAVSDK connection address for the FPV drone")
    parser.add_argument('--follow-alt-offset', type=float, default=5.0,
                        help="Altitude difference (meters) FPV drone maintains ABOVE VTOL drone.")
    parser.add_argument('--follow-dist', type=float, default=20.0,
                        help="Target follow distance (meters) between drones.")
    parser.add_argument('--safety-dist', type=float, default=10.0,
                        help="Minimum safety distance (meters). FPV stops if closer.")
    # Nouvel argument pour l'adresse ZMQ
    parser.add_argument('--zmq-bind-addr', type=str, default="tcp://*:5556",
                        help="ZeroMQ address for this script to BIND to (PULL socket). FPV drone should connect to this.")
    # Nouvel argument pour le timeout ZMQ
    parser.add_argument('--zmq-timeout', type=float, default=300.0,
                        help="Timeout in seconds to wait for the ZMQ message with coordinates.")


    args = parser.parse_args()

    # Input validation
    if args.safety_dist >= args.follow_dist:
        print("Error: Safety distance must be less than follow distance.")
        exit(1)
    if args.follow_alt_offset <= 0:
        print("Warning: Follow altitude offset should ideally be positive for FPV above VTOL.")

    coordinator = DroneCoordinator(
        vtol_address=args.vtol_addr,
        fpv_address=args.fpv_addr,
        follow_alt_offset=args.follow_alt_offset,
        follow_dist=args.follow_dist,
        safety_dist=args.safety_dist,
        zmq_bind_addr=args.zmq_bind_addr, # Passer l'adresse ZMQ
        zmq_timeout=args.zmq_timeout   # Passer le timeout ZMQ
    )

    # Run the asyncio event loop
    asyncio.run(coordinator.run())
