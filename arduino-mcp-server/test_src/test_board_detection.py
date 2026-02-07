"""Test board detection with verification"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arduino_mcp_server.arduino_cli import ArduinoCLI


def test_board_detection():
    """Test board detection with and without verification"""
    cli = ArduinoCLI()
    
    print("=" * 60)
    print("Arduino Board Detection Test")
    print("=" * 60)
    
    # Check CLI installation
    print("\n1. Checking arduino-cli installation...")
    if not cli.check_installation():
        print("❌ arduino-cli not found!")
        return
    print("✅ arduino-cli is installed")
    
    # Test without verification
    print("\n2. Detecting boards (without verification)...")
    boards = cli.detect_boards(verify_connection=False)
    print(f"Found {len(boards)} port(s):")
    for board in boards:
        print(f"  • Port: {board.port}")
        if board.name:
            print(f"    Name: {board.name}")
        if board.fqbn:
            print(f"    FQBN: {board.fqbn}")
    
    # Test with verification
    print("\n3. Detecting boards (with verification)...")
    boards = cli.detect_boards(verify_connection=True)
    print(f"Found {len(boards)} accessible board(s):")
    for board in boards:
        print(f"  ✅ Port: {board.port}")
        if board.name:
            print(f"     Name: {board.name}")
        if board.fqbn:
            print(f"     FQBN: {board.fqbn}")
    
    # Test specific board detection
    print("\n4. Testing specific board detection...")
    for board_type in ["pico", "uno", "nano"]:
        print(f"\nLooking for {board_type}...")
        board = cli.detect_board_by_type(board_type)
        if board:
            print(f"  ✅ Found {board_type}:")
            print(f"     Port: {board.port}")
            if board.name:
                print(f"     Name: {board.name}")
            if board.fqbn:
                print(f"     FQBN: {board.fqbn}")
        else:
            print(f"  ❌ No {board_type} board found")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_board_detection()
