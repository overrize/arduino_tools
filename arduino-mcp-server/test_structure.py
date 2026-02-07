"""Test new project structure"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arduino_mcp_server.models import ProjectConfig, Component
from arduino_mcp_server.code_generator import CodeGenerator

# Create test config
config = ProjectConfig(
    board_fqbn="arduino:avr:uno",
    components=[
        Component(type="led", name="LED", pin=13, mode="OUTPUT")
    ],
    blink_interval=1000
)

# Generate project
output_dir = Path("./test_output/structure_test")
output_dir.mkdir(parents=True, exist_ok=True)

generator = CodeGenerator(output_dir)
project_dir = generator.generate_led_blink(config, "test_project", include_wokwi=True)

print(f"\n✅ Project generated at: {project_dir}\n")

# Check structure
print("📁 Project structure:")
for item in sorted(project_dir.rglob("*")):
    if item.is_file():
        rel_path = item.relative_to(project_dir)
        print(f"   - {rel_path}")

# Verify expected files
expected_files = [
    "test_project.ino",
    "docs",
    "simulation/diagram.json",
    "simulation/wokwi.toml",
    "build"
]

print("\n🔍 Verification:")
for expected in expected_files:
    path = project_dir / expected
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"   {status} {expected}")

# Check wokwi.toml content
toml_path = project_dir / "simulation" / "wokwi.toml"
if toml_path.exists():
    print(f"\n📄 wokwi.toml content:")
    print(toml_path.read_text())
