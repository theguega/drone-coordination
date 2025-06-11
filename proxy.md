## PC1 (Windows - USB + QGroundControl)

**Step 1: Install MAVProxy on Windows**
```cmd
pip install MAVProxy
```

**Step 2: Run MAVProxy to share the USB connection**
```cmd
mavproxy.py --master=COM3 --out=udp:127.0.0.1:14550 --out=tcpout:0.0.0.0:5760
```
*Replace `COM3` with your actual COM port*

This command:
- Reads from your USB telemetry on COM3
- Outputs to local UDP port 14550 (for QGroundControl)
- Creates a TCP server on port 5760 (for PC2 to connect)

**Step 3: Configure QGroundControl**
- In QGroundControl: **Application Settings → Comm Links**
- Add new connection: **UDP**, port **14550**
- Connect QGroundControl to this local UDP connection

## PC2 (Linux - MAVSDK Python)

**Your Python MAVSDK code:**
```python
import asyncio
from mavsdk import System

async def main():
    drone = System()
    # Connect to PC1's MAVProxy TCP server
    await drone.connect("tcp://PC1_IP_ADDRESS:5760")

    # Now you can get telemetry
    async for position in drone.telemetry.position():
        print(f"Lat: {position.latitude_deg}, Lon: {position.longitude_deg}")

if __name__ == "__main__":
    asyncio.run(main())
```

Replace `PC1_IP_ADDRESS` with PC1's actual IP address (e.g., `192.168.1.100`).

## Network Setup

**Find PC1's IP address:**
```cmd
# On PC1 (Windows)
ipconfig
```

**Test the connection from PC2:**
```bash
# On PC2 (Linux) - test if port is reachable
telnet PC1_IP_ADDRESS 5760
```

**Windows Firewall (PC1):**
- Open Windows Defender Firewall
- Add inbound rule for port 5760 (TCP)
- Or temporarily disable firewall for testing

## Complete Example

**PC1 (Windows) Command:**
```cmd
mavproxy.py --master=COM3 --out=udp:127.0.0.1:14550 --out=tcpout:0.0.0.0:5760
```

**PC2 (Linux) Python:**
```python
await drone.connect("tcp://192.168.1.100:5760")  # Use PC1's actual IP
```
