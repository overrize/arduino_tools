"""测试完整流程：生成代码 → 编译 → 检查产物"""

import sys
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arduino_mcp_server.models import ProjectConfig, Component
from arduino_mcp_server.code_generator import CodeGenerator
from arduino_mcp_server.arduino_cli import ArduinoCLI

print("=" * 70)
print("🧪 测试完整流程：生成代码 → 编译 → 检查产物")
print("=" * 70)

# 创建测试配置
config = ProjectConfig(
    board_fqbn="arduino:avr:uno",
    components=[
        Component(type="led", name="LED", pin=13, mode="OUTPUT")
    ],
    blink_interval=1000
)

# 步骤 1: 生成代码和 Wokwi 文件
print("\n📋 步骤 1: 生成代码和 Wokwi 文件")
print("-" * 70)

output_dir = Path("./test_output/complete_flow_test")
if output_dir.exists():
    import shutil
    shutil.rmtree(output_dir)

generator = CodeGenerator(output_dir)
project_dir = generator.generate_led_blink(config, "test_complete", include_wokwi=True)

print(f"✅ 项目已创建: {project_dir}")

# 步骤 2: 检查文件结构
print("\n📋 步骤 2: 检查文件结构")
print("-" * 70)

expected_files = {
    "test_complete.ino": "Arduino 源代码",
    "docs": "文档目录",
    "simulation": "仿真目录",
    "simulation/diagram.json": "Wokwi 电路图",
    "simulation/wokwi.toml": "Wokwi 配置",
    "build": "编译输出目录"
}

all_exist = True
for file_path, description in expected_files.items():
    path = project_dir / file_path
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {file_path:30s} - {description}")
    if not exists:
        all_exist = False

if not all_exist:
    print("\n❌ 文件结构不完整！")
    sys.exit(1)

# 步骤 3: 检查 diagram.json 内容
print("\n📋 步骤 3: 检查 diagram.json 内容")
print("-" * 70)

diagram_path = project_dir / "simulation" / "diagram.json"
try:
    with open(diagram_path, 'r', encoding='utf-8') as f:
        diagram = json.load(f)
    
    print(f"✅ diagram.json 解析成功")
    print(f"   版本: {diagram.get('version')}")
    print(f"   元件数量: {len(diagram.get('parts', []))}")
    print(f"   连接数量: {len(diagram.get('connections', []))}")
    
    # 检查必要的元件
    parts = diagram.get('parts', [])
    part_types = [p.get('type') for p in parts]
    
    required_parts = ['board-arduino-uno', 'wokwi-led', 'wokwi-resistor']
    for part_type in required_parts:
        if part_type in part_types:
            print(f"   ✅ 包含 {part_type}")
        else:
            print(f"   ❌ 缺少 {part_type}")
            all_exist = False
    
except Exception as e:
    print(f"❌ diagram.json 解析失败: {e}")
    all_exist = False

# 步骤 4: 检查 wokwi.toml 内容
print("\n📋 步骤 4: 检查 wokwi.toml 内容")
print("-" * 70)

toml_path = project_dir / "simulation" / "wokwi.toml"
try:
    toml_content = toml_path.read_text(encoding='utf-8')
    print(f"✅ wokwi.toml 读取成功")
    print(f"内容:\n{toml_content}")
    
    # 检查固件路径
    if "../build/test_complete.ino.hex" in toml_content:
        print("✅ 固件路径正确")
    else:
        print("❌ 固件路径不正确")
        all_exist = False
        
except Exception as e:
    print(f"❌ wokwi.toml 读取失败: {e}")
    all_exist = False

# 步骤 5: 编译代码
print("\n📋 步骤 5: 编译代码")
print("-" * 70)

cli = ArduinoCLI()
compile_result = cli.compile_sketch(project_dir, config.board_fqbn)

if compile_result.success:
    print(f"✅ 编译成功")
    print(f"   编译输出目录: {compile_result.build_path}")
else:
    print(f"❌ 编译失败")
    print(f"   错误: {compile_result.output}")
    all_exist = False

# 步骤 6: 检查编译产物
print("\n📋 步骤 6: 检查编译产物")
print("-" * 70)

if compile_result.success and compile_result.build_path:
    build_path = Path(compile_result.build_path)
    hex_file = build_path / "test_complete.ino.hex"
    elf_file = build_path / "test_complete.ino.elf"
    
    if hex_file.exists():
        size = hex_file.stat().st_size
        print(f"✅ HEX 文件存在: {hex_file.name} ({size} bytes)")
    else:
        print(f"❌ HEX 文件不存在: {hex_file}")
        all_exist = False
    
    if elf_file.exists():
        size = elf_file.stat().st_size
        print(f"✅ ELF 文件存在: {elf_file.name} ({size} bytes)")
    else:
        print(f"⚠️  ELF 文件不存在: {elf_file}")
else:
    print("❌ 无法检查编译产物（编译失败）")
    all_exist = False

# 最终总结
print("\n" + "=" * 70)
if all_exist and compile_result.success:
    print("✅ 所有测试通过！")
    print("\n📁 完整的项目结构:")
    print(f"   {project_dir}/")
    print(f"   ├── test_complete.ino          # Arduino 源代码")
    print(f"   ├── docs/                       # 文档目录")
    print(f"   ├── simulation/                 # 仿真文件")
    print(f"   │   ├── diagram.json           # Wokwi 电路图")
    print(f"   │   └── wokwi.toml             # Wokwi 配置")
    print(f"   └── build/                      # 编译产物")
    print(f"       ├── test_complete.ino.hex  # 固件文件")
    print(f"       └── test_complete.ino.elf  # ELF 文件")
    print("\n🎮 Wokwi 仿真:")
    print(f"   1. 打开 {project_dir / 'simulation' / 'diagram.json'}")
    print(f"   2. 按 F1 → 'Wokwi: Start Simulator'")
    print(f"   3. 仿真器会自动加载 build/ 目录中的固件")
else:
    print("❌ 部分测试失败")
    sys.exit(1)

print("=" * 70)
