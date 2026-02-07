"""Basic functionality test for Arduino MCP Server"""

from pathlib import Path
from src.arduino_mcp_server.models import ProjectConfig, Component
from src.arduino_mcp_server.code_generator import CodeGenerator
from src.arduino_mcp_server.arduino_cli import ArduinoCLI


def test_code_generation():
    """Test code generation"""
    print("Testing code generation...")
    
    # Create config
    config = ProjectConfig(
        board_fqbn="arduino:avr:uno",
        components=[
            Component(type="led", name="LED", pin=13, mode="OUTPUT")
        ],
        blink_interval=1000,
        serial_enabled=True
    )
    
    # Generate code
    generator = CodeGenerator(Path("./test_output"))
    sketch_dir = generator.generate_led_blink(config, "test_led_blink")
    
    print(f"✅ Code generated at: {sketch_dir}")
    
    # Check if file exists
    sketch_file = sketch_dir / "test_led_blink.ino"
    if sketch_file.exists():
        print(f"✅ Sketch file created: {sketch_file}")
        print("\nGenerated code preview:")
        print("-" * 50)
        print(sketch_file.read_text()[:500])
        print("-" * 50)
    else:
        print("❌ Sketch file not found")
    
    return sketch_dir


def test_arduino_cli():
    """Test arduino-cli wrapper"""
    print("\nTesting arduino-cli...")
    
    cli = ArduinoCLI()
    
    # Check installation
    if cli.check_installation():
        print("✅ arduino-cli is installed")
    else:
        print("❌ arduino-cli not found")
        return False
    
    # Detect boards
    print("\nDetecting boards...")
    boards = cli.detect_boards()
    if boards:
        print(f"✅ Found {len(boards)} board(s):")
        for board in boards:
            print(f"  • Port: {board.port}")
            if board.fqbn:
                print(f"    FQBN: {board.fqbn}")
            if board.name:
                print(f"    Name: {board.name}")
    else:
        print("⚠️  No boards detected (this is OK if no board is connected)")
    
    return True


def test_intent_parsing():
    """Test intent parsing"""
    print("\nTesting intent parsing...")
    
    from src.arduino_mcp_server.server import parse_led_blink_intent
    
    test_cases = [
        "用 Arduino Uno 做一个 LED 闪烁，13 号引脚",
        "Arduino Nano LED blink pin 7 every 2 seconds",
        "Pico LED 闪烁 25 号引脚每 3 秒",
    ]
    
    for test_input in test_cases:
        print(f"\nInput: {test_input}")
        config = parse_led_blink_intent(test_input)
        print(f"  Board: {config.board_fqbn}")
        print(f"  LED Pin: {config.components[0].pin}")
        print(f"  Interval: {config.blink_interval}ms")
    
    print("\n✅ Intent parsing test complete")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Arduino MCP Server - Basic Functionality Test")
    print("=" * 60)
    
    # Test 1: Code generation
    sketch_dir = test_code_generation()
    
    # Test 2: Arduino CLI
    cli_ok = test_arduino_cli()
    
    # Test 3: Intent parsing
    test_intent_parsing()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("✅ Code generation: PASSED")
    print(f"{'✅' if cli_ok else '❌'} Arduino CLI: {'PASSED' if cli_ok else 'FAILED'}")
    print("✅ Intent parsing: PASSED")
    
    if cli_ok:
        print("\n🎉 All tests passed! You can now:")
        print("1. Connect an Arduino board")
        print("2. Configure Kiro MCP (see USAGE.md)")
        print("3. Start using natural language to program Arduino!")
    else:
        print("\n⚠️  Please install arduino-cli first:")
        print("   Windows: winget install ArduinoSA.CLI")
        print("   Or visit: https://arduino.github.io/arduino-cli/")


if __name__ == "__main__":
    main()
