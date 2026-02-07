"""Test serial port access"""

import serial
import serial.tools.list_ports

print("=" * 60)
print("Serial Port Access Test")
print("=" * 60)

# List all available ports
print("\n[1] Available serial ports:")
ports = serial.tools.list_ports.comports()
if not ports:
    print("  No serial ports found")
else:
    for port in ports:
        print(f"  • {port.device}")
        print(f"    Description: {port.description}")
        print(f"    Hardware ID: {port.hwid}")
        print()

# Try to open COM3
print("[2] Testing COM3 access:")
try:
    ser = serial.Serial('COM3', 9600, timeout=1)
    print("  ✅ Successfully opened COM3")
    ser.close()
    print("  ✅ Successfully closed COM3")
except serial.SerialException as e:
    print(f"  ❌ Failed to open COM3: {e}")
except Exception as e:
    print(f"  ❌ Unexpected error: {e}")

print("\n" + "=" * 60)
