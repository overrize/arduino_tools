"""Test Wokwi integration in full workflow"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from arduino_mcp_server.models import ProjectConfig, Component
from arduino_mcp_server.code_generator import CodeGenerator
from arduino_mcp_server.server import parse_led_blink_intent


def test_wokwi_workflow():
    """Test the complete workflow with Wokwi generation"""
    
    print("🧪 Testing Wokwi Workflow Integration\n")
    
    # Test 1: Parse intent
    print("Test 1: Parsing user intent...")
    user_input = "用 Pico 做一个 LED 闪烁，25 号引脚，每 2 秒闪一次"
    config = parse_led_blink_intent(user_input)
    
    assert config.board_fqbn == "arduino:mbed_rp2040:pico"
    assert len(config.components) == 1
    assert config.components[0].pin == 25
    assert config.blink_interval == 2000
    print("✅ Intent parsed correctly")
    print(f"   Board: {config.board_fqbn}")
    print(f"   Pin: {config.components[0].pin}")
    print(f"   Interval: {config.blink_interval}ms\n")
    
    # Test 2: Generate code with Wokwi
    print("Test 2: Generating code with Wokwi files...")
    output_dir = Path("./test_output/wokwi_workflow_test")
    generator = CodeGenerator(output_dir)
    sketch_dir = generator.generate_led_blink(config, "pico_led_test", include_wokwi=True)
    
    # Verify files exist
    ino_file = sketch_dir / "pico_led_test.ino"
    diagram_file = sketch_dir / "diagram.json"
    toml_file = sketch_dir / "wokwi.toml"
    
    assert ino_file.exists(), "Arduino sketch not generated"
    assert diagram_file.exists(), "Wokwi diagram.json not generated"
    assert toml_file.exists(), "Wokwi wokwi.toml not generated"
    
    print("✅ All files generated:")
    print(f"   • {ino_file.name}")
    print(f"   • {diagram_file.name}")
    print(f"   • {toml_file.name}\n")
    
    # Test 3: Verify diagram.json content
    print("Test 3: Verifying diagram.json content...")
    import json
    with open(diagram_file, 'r', encoding='utf-8') as f:
        diagram = json.load(f)
    
    # Check board type
    board_part = next((p for p in diagram['parts'] if p['id'] == 'mcu'), None)
    assert board_part is not None, "Board not found in diagram"
    assert board_part['type'] == 'board-pi-pico', f"Wrong board type: {board_part['type']}"
    
    # Check LED
    led_part = next((p for p in diagram['parts'] if 'led' in p['id']), None)
    assert led_part is not None, "LED not found in diagram"
    assert led_part['type'] == 'wokwi-led', "Wrong LED type"
    
    # Check resistor
    resistor_part = next((p for p in diagram['parts'] if 'r' in p['id']), None)
    assert resistor_part is not None, "Resistor not found in diagram"
    assert resistor_part['attrs']['value'] == '220', "Wrong resistor value"
    
    # Check connections
    assert len(diagram['connections']) >= 3, "Not enough connections"
    
    print("✅ Diagram.json structure verified:")
    print(f"   • Board: {board_part['type']}")
    print(f"   • LED: {led_part['type']}")
    print(f"   • Resistor: {resistor_part['attrs']['value']}Ω")
    print(f"   • Connections: {len(diagram['connections'])}\n")
    
    # Test 4: Verify wokwi.toml
    print("Test 4: Verifying wokwi.toml...")
    toml_content = toml_file.read_text(encoding='utf-8')
    assert '[wokwi]' in toml_content, "Missing [wokwi] section"
    assert 'version = 1' in toml_content, "Missing version"
    print("✅ wokwi.toml verified\n")
    
    # Test 5: Verify Arduino code
    print("Test 5: Verifying Arduino code...")
    ino_content = ino_file.read_text(encoding='utf-8')
    assert 'const int LED_PIN = 25;' in ino_content, "Wrong LED pin"
    assert 'delay(2000);' in ino_content, "Wrong interval"
    assert 'pinMode(LED_PIN, OUTPUT);' in ino_content, "Missing pinMode"
    print("✅ Arduino code verified\n")
    
    print("=" * 60)
    print("🎉 All tests passed!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("   1. Open the project in VS Code:")
    print(f"      cd {sketch_dir}")
    print("   2. Open diagram.json")
    print("   3. Press F1 → 'Wokwi: Start Simulator'")
    print("   4. See the LED blinking in simulation!")
    print("\n💡 Or test in Kiro with:")
    print("   '用 Pico 做一个 LED 闪烁，25 号引脚'")


if __name__ == "__main__":
    try:
        test_wokwi_workflow()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
