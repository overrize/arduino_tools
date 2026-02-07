"""Test serial monitoring for Pico"""

import serial
import time

def monitor_pico_serial():
    """Monitor serial output from Pico"""
    print("=" * 60)
    print("Raspberry Pi Pico - Serial Monitor")
    print("=" * 60)
    
    port = "COM7"  # Pico port
    baud_rate = 9600
    
    print(f"\nConnecting to {port} at {baud_rate} baud...")
    
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"✅ Connected to {port}")
        print("\nSerial output (press Ctrl+C to stop):")
        print("-" * 60)
        
        line_count = 0
        while line_count < 20:  # Read 20 lines
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"[{time.strftime('%H:%M:%S')}] {line}")
                    line_count += 1
            time.sleep(0.1)
        
        print("-" * 60)
        print(f"\n✅ Received {line_count} lines")
        ser.close()
        
    except serial.SerialException as e:
        print(f"❌ Failed to connect: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring stopped by user")
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    monitor_pico_serial()
