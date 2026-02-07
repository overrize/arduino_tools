"""Test port manager functionality"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arduino_mcp_server.port_manager import PortManager

def test_port_manager():
    """Test port management"""
    print("=" * 60)
    print("Port Manager Test")
    print("=" * 60)
    
    manager = PortManager()
    
    # Test 1: Find port users
    print("\n[Test 1] Finding processes using COM7...")
    users = manager.find_port_users("COM7")
    if users:
        print(f"Found {len(users)} process(es):")
        for user in users:
            print(f"  • {user['name']} (PID: {user['pid']})")
    else:
        print("  No processes found using COM7")
    
    # Test 2: Check port availability
    print("\n[Test 2] Checking if COM7 is available...")
    if manager.is_port_available("COM7"):
        print("  ✅ COM7 is available")
    else:
        print("  ⚠️  COM7 is busy")
    
    # Test 3: Prepare port (if busy)
    if users:
        print("\n[Test 3] Preparing COM7 for upload...")
        response = input("  Close processes using COM7? (y/n): ")
        if response.lower() == 'y':
            if manager.prepare_port_for_upload("COM7"):
                print("  ✅ COM7 is ready")
            else:
                print("  ❌ Failed to prepare COM7")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_port_manager()
