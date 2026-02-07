"""Full workflow test with actual hardware"""

from pathlib import Path
from src.arduino_mcp_server.models import ProjectConfig, Component
from src.arduino_mcp_server.code_generator import CodeGenerator
from src.arduino_mcp_server.arduino_cli import ArduinoCLI


def test_full_workflow():
    """Test complete workflow with LED blink"""
    print("=" * 60)
    print("Arduino MCP Server - Full Workflow Test")
    print("=" * 60)
    
    # Initialize
    cli = ArduinoCLI()
    
    # Step 1: Check installation
    print("\n[Step 1] Checking arduino-cli installation...")
    if not cli.check_installation():
        print("❌ arduino-cli not found")
        return False
    print("✅ arduino-cli is installed")
    
    # Step 2: Detect boards
    print("\n[Step 2] Detecting boards...")
    boards = cli.detect_boards()
    if not boards:
        print("⚠️  No boards detected. Please connect an Arduino board.")
        return False
    
    print(f"✅ Found {len(boards)} board(s):")
    for board in boards:
        print(f"  • Port: {board.port}")
        if board.fqbn:
            print(f"    FQBN: {board.fqbn}")
        if board.name:
            print(f"    Name: {board.name}")
    
    # Step 3: Create project
    print("\n[Step 3] Creating LED blink project...")
    config = ProjectConfig(
        board_fqbn="arduino:avr:uno",
        components=[
            Component(type="led", name="LED", pin=13, mode="OUTPUT")
        ],
        blink_interval=1000,
        serial_enabled=True
    )
    
    generator = CodeGenerator(Path("./test_output"))
    sketch_dir = generator.generate_led_blink(config, "full_test_blink")
    print(f"✅ Project created at: {sketch_dir}")
    
    # Step 4: Compile
    print("\n[Step 4] Compiling...")
    compile_result = cli.compile_sketch(sketch_dir, config.board_fqbn)
    if not compile_result.success:
        print(f"❌ Compilation failed:")
        print(compile_result.output)
        return False
    print("✅ Compilation successful")
    
    # Step 5: Upload
    print("\n[Step 5] Uploading to board...")
    print(f"Using port: {boards[0].port}")
    upload_result = cli.upload_sketch(sketch_dir, config.board_fqbn, boards[0].port)
    if not upload_result.success:
        print(f"❌ Upload failed:")
        print(upload_result.message)
        return False
    print(f"✅ Upload successful to {upload_result.port}")
    
    # Step 6: Monitor (optional)
    print("\n[Step 6] Monitoring serial output (5 seconds)...")
    try:
        lines = cli.monitor_serial(boards[0].port, 9600, 5)
        if lines:
            print("Serial output:")
            for line in lines[:10]:
                print(f"  {line}")
        else:
            print("⚠️  No serial output (this is OK)")
    except Exception as e:
        print(f"⚠️  Serial monitoring error: {e}")
    
    # Success!
    print("\n" + "=" * 60)
    print("🎉 Full workflow test completed successfully!")
    print("=" * 60)
    print("\nYour LED should be blinking now!")
    print("Check the Arduino board - the LED on pin 13 should be flashing.")
    
    return True


if __name__ == "__main__":
    success = test_full_workflow()
    exit(0 if success else 1)
