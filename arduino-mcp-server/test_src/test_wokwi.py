"""Test Wokwi diagram generation"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arduino_mcp_server.models import ProjectConfig, Component
from arduino_mcp_server.code_generator import CodeGenerator

def test_wokwi_generation():
    """Test Wokwi diagram generation"""
    print("=" * 60)
    print("Wokwi Diagram Generation Test")
    print("=" * 60)
    
    # Test 1: Pico LED Blink
    print("\n[Test 1] Generating Pico LED Blink with Wokwi...")
    config = ProjectConfig(
        board_fqbn="arduino:mbed_rp2040:pico",
        components=[
            Component(type="led", name="LED", pin=25, mode="OUTPUT")
        ],
        blink_interval=1000,
        serial_enabled=True
    )
    
    generator = CodeGenerator(Path("./test_output"))
    sketch_dir = generator.generate_led_blink(config, "pico_wokwi_test", include_wokwi=True)
    
    print(f"✅ Project generated at: {sketch_dir}")
    
    # Check files
    diagram_file = sketch_dir / "diagram.json"
    toml_file = sketch_dir / "wokwi.toml"
    ino_file = sketch_dir / "pico_wokwi_test.ino"
    
    if diagram_file.exists():
        print(f"✅ diagram.json created")
        with open(diagram_file, 'r') as f:
            diagram = json.load(f)
            print(f"   Parts: {len(diagram['parts'])}")
            print(f"   Connections: {len(diagram['connections'])}")
            
            # Show diagram content
            print("\n   Diagram preview:")
            print(json.dumps(diagram, indent=2)[:500] + "...")
    else:
        print("❌ diagram.json not found")
    
    if toml_file.exists():
        print(f"\n✅ wokwi.toml created")
        print(f"   Content:")
        print("   " + toml_file.read_text().replace("\n", "\n   "))
    else:
        print("❌ wokwi.toml not found")
    
    if ino_file.exists():
        print(f"\n✅ {ino_file.name} created")
    else:
        print("❌ .ino file not found")
    
    # Test 2: Arduino Uno LED Blink
    print("\n" + "=" * 60)
    print("[Test 2] Generating Arduino Uno LED Blink with Wokwi...")
    config2 = ProjectConfig(
        board_fqbn="arduino:avr:uno",
        components=[
            Component(type="led", name="LED", pin=13, mode="OUTPUT")
        ],
        blink_interval=500,
        serial_enabled=True
    )
    
    sketch_dir2 = generator.generate_led_blink(config2, "uno_wokwi_test", include_wokwi=True)
    print(f"✅ Project generated at: {sketch_dir2}")
    
    diagram_file2 = sketch_dir2 / "diagram.json"
    if diagram_file2.exists():
        with open(diagram_file2, 'r') as f:
            diagram2 = json.load(f)
            print(f"   Board type: {diagram2['parts'][0]['type']}")
            print(f"   Parts: {len(diagram2['parts'])}")
    
    print("\n" + "=" * 60)
    print("🎉 Wokwi generation test complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Open VS Code")
    print("2. Install Wokwi extension")
    print("3. Open the generated project folder")
    print("4. Open diagram.json")
    print("5. Press F1 and type 'Wokwi: Start Simulator'")

if __name__ == "__main__":
    test_wokwi_generation()
