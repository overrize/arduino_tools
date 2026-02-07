"""Stability test for Arduino MCP Server"""

import sys
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arduino_mcp_server.models import ProjectConfig, Component
from arduino_mcp_server.code_generator import CodeGenerator
from arduino_mcp_server.arduino_cli import ArduinoCLI

print("=" * 60)
print("Arduino MCP Server - Stability Test")
print("=" * 60)

# Test 1: Check arduino-cli
print("\n📋 Test 1: Check arduino-cli installation")
cli = ArduinoCLI()
if cli.check_installation():
    print("✅ arduino-cli is installed")
else:
    print("❌ arduino-cli not found")
    sys.exit(1)

# Test 2: Create project with correct structure
print("\n📋 Test 2: Create project structure")
output_dir = Path("./test_output/stability_test")
if output_dir.exists():
    shutil.rmtree(output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

config = ProjectConfig(
    board_fqbn="arduino:avr:uno",
    components=[
        Component(type="led", name="LED", pin=13, mode="OUTPUT")
    ],
    blink_interval=1000
)

generator = CodeGenerator(output_dir)
project_dir = generator.generate_led_blink(config, "stability_test", include_wokwi=True)

print(f"✅ Project created at: {project_dir}")

# Test 3: Verify directory structure
print("\n📋 Test 3: Verify directory structure")
expected_structure = {
    "stability_test.ino": "file",
    "docs": "dir",
    "simulation": "dir",
    "simulation/diagram.json": "file",
    "simulation/wokwi.toml": "file",
    "build": "dir"
}

all_ok = True
for path_str, expected_type in expected_structure.items():
    path = project_dir / path_str
    exists = path.exists()
    
    if not exists:
        print(f"❌ Missing: {path_str}")
        all_ok = False
    elif expected_type == "file" and not path.is_file():
        print(f"❌ Not a file: {path_str}")
        all_ok = False
    elif expected_type == "dir" and not path.is_dir():
        print(f"❌ Not a directory: {path_str}")
        all_ok = False
    else:
        print(f"✅ {path_str}")

if not all_ok:
    print("\n❌ Structure verification failed")
    sys.exit(1)

# Test 4: Verify wokwi.toml content
print("\n📋 Test 4: Verify wokwi.toml content")
toml_path = project_dir / "simulation" / "wokwi.toml"
toml_content = toml_path.read_text()

if "../build/stability_test.ino.hex" in toml_content:
    print("✅ Firmware path is correct")
else:
    print("❌ Firmware path is incorrect")
    print(f"Content:\n{toml_content}")
    all_ok = False

# Test 5: Compile sketch
print("\n📋 Test 5: Compile sketch")
compile_result = cli.compile_sketch(project_dir, config.board_fqbn)

if compile_result.success:
    print("✅ Compilation successful")
    print(f"   Build path: {compile_result.build_path}")
    
    # Check if build artifacts exist
    build_path = Path(compile_result.build_path)
    hex_file = build_path / "stability_test.ino.hex"
    
    if hex_file.exists():
        print(f"✅ Firmware file exists: {hex_file.name}")
    else:
        print(f"❌ Firmware file not found")
        print(f"   Expected: {hex_file}")
        all_ok = False
else:
    print("❌ Compilation failed")
    print(compile_result.output)
    all_ok = False

# Test 6: Library management
print("\n📋 Test 6: Library management")
print("Searching for 'Servo' library...")
results = cli.search_library("Servo")
if results:
    print(f"✅ Found {len(results)} libraries")
    if len(results) > 0:
        print(f"   Example: {results[0].get('name', 'Unknown')}")
else:
    print("⚠️  No libraries found (may be network issue)")

# Final summary
print("\n" + "=" * 60)
if all_ok:
    print("✅ All tests passed!")
    print("\n📁 Test project location:")
    print(f"   {project_dir.absolute()}")
    print("\n🎮 To test Wokwi simulation:")
    print(f"   1. Open {project_dir / 'simulation' / 'diagram.json'}")
    print("   2. Press F1 → 'Wokwi: Start Simulator'")
else:
    print("❌ Some tests failed")
    sys.exit(1)

print("=" * 60)
