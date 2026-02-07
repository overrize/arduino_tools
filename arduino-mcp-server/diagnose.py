"""Quick diagnostic tool for Arduino MCP Server"""

import sys
import json
from pathlib import Path

print("🔍 Arduino MCP Server - 快速诊断")
print("=" * 60)

# Check 1: Python version
print("\n1️⃣ Python 版本")
version = sys.version_info
if version.major >= 3 and version.minor >= 10:
    print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
else:
    print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (需要 3.10+)")

# Check 2: arduino-cli
print("\n2️⃣ arduino-cli")
import subprocess
try:
    result = subprocess.run(
        ["arduino-cli", "version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        version_line = result.stdout.strip().split('\n')[0]
        print(f"   ✅ {version_line}")
    else:
        print("   ❌ arduino-cli 无法运行")
except FileNotFoundError:
    print("   ❌ arduino-cli 未安装")
    print("   💡 安装: https://arduino.github.io/arduino-cli/")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# Check 3: MCP 配置
print("\n3️⃣ MCP 配置")
config_path = Path("kiro-mcp-config.json")
if config_path.exists():
    try:
        config = json.loads(config_path.read_text())
        arduino_config = config.get("mcpServers", {}).get("arduino", {})
        
        cwd = arduino_config.get("cwd", "")
        if "src" in cwd and cwd.endswith("src"):
            print(f"   ⚠️  工作目录可能不正确: {cwd}")
            print("   💡 建议改为项目根目录")
        else:
            print(f"   ✅ 工作目录: {cwd}")
        
        disabled = arduino_config.get("disabled", False)
        if disabled:
            print("   ⚠️  MCP server 已禁用")
        else:
            print("   ✅ MCP server 已启用")
            
    except Exception as e:
        print(f"   ❌ 配置文件解析失败: {e}")
else:
    print("   ⚠️  配置文件不存在")

# Check 4: 项目结构
print("\n4️⃣ 项目结构")
src_path = Path("src/arduino_mcp_server")
if src_path.exists():
    print("   ✅ 源代码目录存在")
    
    key_files = [
        "server.py",
        "arduino_cli.py",
        "code_generator.py",
        "wokwi_generator.py"
    ]
    
    missing = []
    for file in key_files:
        if not (src_path / file).exists():
            missing.append(file)
    
    if missing:
        print(f"   ⚠️  缺少文件: {', '.join(missing)}")
    else:
        print("   ✅ 所有核心文件存在")
else:
    print("   ❌ 源代码目录不存在")

# Check 5: 依赖库
print("\n5️⃣ Python 依赖")
required_packages = [
    "mcp",
    "pydantic",
    "jinja2",
    "pyserial",
    "psutil"
]

missing_packages = []
for package in required_packages:
    try:
        __import__(package)
        print(f"   ✅ {package}")
    except ImportError:
        print(f"   ❌ {package} (未安装)")
        missing_packages.append(package)

if missing_packages:
    print(f"\n   💡 安装缺失的包:")
    print(f"      pip install {' '.join(missing_packages)}")

# Check 6: Arduino 核心
print("\n6️⃣ Arduino 核心")
try:
    result = subprocess.run(
        ["arduino-cli", "core", "list"],
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        cores = [line for line in lines if line and not line.startswith('ID')]
        if cores:
            print(f"   ✅ 已安装 {len(cores)} 个核心:")
            for core in cores[:3]:  # Show first 3
                print(f"      • {core.split()[0]}")
        else:
            print("   ⚠️  未安装任何核心")
            print("   💡 安装: arduino-cli core install arduino:avr")
except Exception as e:
    print(f"   ⚠️  无法检查: {e}")

# Summary
print("\n" + "=" * 60)
print("📊 诊断完成")
print("\n💡 建议:")
print("   1. 确保所有 ✅ 项都正常")
print("   2. 修复所有 ❌ 项")
print("   3. 检查 ⚠️  项并根据提示操作")
print("   4. 运行 'python test_stability.py' 进行完整测试")
print("=" * 60)
