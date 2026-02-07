# Arduino MCP Server

自然语言驱动的 Arduino 开发 MCP Server

## 概述

Arduino MCP Server 是一个基于 Model Context Protocol (MCP) 的服务器，让用户通过自然语言对话完成 Arduino 嵌入式开发的完整流程。

### 核心特性

- 🗣️ **自然语言输入** - 用对话描述需求
- 🤖 **自动代码生成** - 基于模板可靠生成
- 🎮 **Wokwi 仿真** - 无需硬件即可测试
- 🔍 **智能板卡检测** - 自动识别和验证连接
- ⚡ **一键编译上传** - 端到端自动化
- 📡 **串口监控** - 实时查看输出

## 快速开始

### 前置要求

1. Python 3.10+
2. arduino-cli ([安装指南](https://arduino.github.io/arduino-cli/))
3. Kiro IDE (可选，用于 MCP 集成)

### 安装

```bash
cd arduino-mcp-server
pip install -e .
```

### 配置 arduino-cli

```bash
arduino-cli config init
arduino-cli core update-index
arduino-cli core install arduino:avr        # Arduino Uno/Nano
arduino-cli core install arduino:mbed_rp2040  # Raspberry Pi Pico
```

### 稳定性测试

运行测试脚本验证配置：

```bash
python test_stability.py
```

应该看到所有测试通过：
```
✅ All tests passed!
```

如果测试失败，请查看 [CONFIGURATION.md](./CONFIGURATION.md) 排查问题。

### MCP 配置

在 Kiro 的 MCP 配置文件中添加：

```json
{
  "mcpServers": {
    "arduino": {
      "command": "python",
      "args": ["-m", "arduino_mcp_server"],
      "disabled": false
    }
  }
}
```

## 架构

### 系统架构

```
用户输入 (自然语言)
    ↓
意图解析 (parse_led_blink_intent)
    ↓
代码生成 (CodeGenerator)
    ├── Arduino 代码 (.ino)
    └── Wokwi 仿真文件 (diagram.json)
    ↓
编译 (ArduinoCLI.compile_sketch)
    ↓
板卡检测 (ArduinoCLI.detect_boards)
    ├── 连接验证
    └── 类型匹配
    ↓
上传 (ArduinoCLI.upload_sketch)
    ├── 串口管理 (PortManager)
    └── 自动释放占用
    ↓
串口监控 (ArduinoCLI.monitor_serial)
```

### 技术栈

- **MCP SDK** - Model Context Protocol 实现
- **Pydantic** - 数据模型和验证
- **Jinja2** - 代码模板引擎
- **pyserial** - 串口通信
- **psutil** - 进程管理
- **arduino-cli** - Arduino 工具链

## 核心模块

### 1. models.py - 数据模型

定义项目配置和结果的数据结构。

**主要类：**

- `Component` - 硬件组件定义（LED、按钮、传感器）
- `ProjectConfig` - Arduino 项目配置
- `CompileResult` - 编译结果
- `UploadResult` - 上传结果
- `BoardInfo` - 板卡信息

**示例：**
```python
class ProjectConfig(BaseModel):
    board_fqbn: str = "arduino:avr:uno"
    components: List[Component] = []
    blink_interval: int = 1000
    serial_enabled: bool = True
    serial_baud: int = 9600
```

### 2. templates.py - 代码模板

使用 Jinja2 模板生成 Arduino 代码。

**模板类型：**

- `LED_BLINK_TEMPLATE` - LED 闪烁代码
- `BUTTON_LED_TEMPLATE` - 按钮控制 LED 代码

**特性：**
- 支持变量替换（引脚、间隔、波特率）
- 可选串口输出
- 清晰的代码注释

### 3. arduino_cli.py - Arduino CLI 封装

封装 arduino-cli 命令行工具的所有功能。

**主要方法：**

- `check_installation()` - 检查 arduino-cli 是否安装
- `detect_boards(verify_connection=True)` - 检测连接的板卡
  - 支持连接验证
  - 过滤被占用的串口
  - 返回板卡信息（端口、FQBN、名称）
- `detect_board_by_type(board_type)` - 按类型检测板卡
  - 支持 pico/uno/nano 等类型
  - 精确匹配 name/FQBN
- `compile_sketch(sketch_path, fqbn)` - 编译 Arduino 代码
- `upload_sketch(sketch_path, fqbn, port)` - 上传代码到板卡
  - 自动检测端口
  - 自动释放串口占用
- `monitor_serial(port, baud_rate, duration)` - 监控串口输出

**板卡检测特性：**
```python
# 验证检测（推荐）
boards = cli.detect_boards(verify_connection=True)

# 类型检测
pico = cli.detect_board_by_type("pico")
```

### 4. port_manager.py - 串口管理

管理串口访问和冲突解决。

**主要方法：**

- `find_port_users(port)` - 查找占用串口的进程
- `close_port_users(port)` - 关闭占用串口的进程
- `is_port_available(port)` - 检查串口是否可用
- `wait_for_port_available(port, timeout)` - 等待串口可用
- `prepare_port_for_upload(port)` - 准备串口用于上传
  - 自动关闭占用进程
  - 等待串口释放
- `reset_port(port)` - 重置串口

**使用场景：**
- 上传前自动释放被 Arduino IDE 占用的串口
- 避免"串口被占用"错误
- 提高上传成功率

### 5. code_generator.py - 代码生成器

从项目配置生成 Arduino 代码和 Wokwi 仿真文件。

**主要方法：**

- `generate_led_blink(config, project_name, include_wokwi)` - 生成 LED 闪烁项目
  - 渲染代码模板
  - 创建 .ino 文件
  - 生成 Wokwi 仿真文件（可选）

**生成文件：**
```
project_name/
├── project_name.ino    # Arduino 代码
├── diagram.json        # Wokwi 电路图
└── wokwi.toml         # Wokwi 配置
```

### 6. wokwi_generator.py - Wokwi 仿真生成器

生成 Wokwi 仿真所需的 diagram.json 文件。

**主要方法：**

- `generate_diagram(config, project_name)` - 生成完整的 Wokwi 图表
- `_add_led(board_id, component, board_fqbn)` - 添加 LED 组件
- `_add_button(board_id, component)` - 添加按钮组件

**支持的板卡：**
- Arduino Uno (`board-arduino-uno`)
- Arduino Nano (`board-arduino-nano`)
- Raspberry Pi Pico (`board-pi-pico`)
- ESP32 (`board-esp32-devkit-c-v4`)

**特性：**
- 自动布局组件
- 自动连接电路
- 包含串口监视器
- 支持多种组件类型

### 7. server.py - MCP Server 主入口

实现 MCP 协议，提供 7 个工具供 AI 调用。

**MCP 工具列表：**

1. `check_arduino_cli` - 检查 arduino-cli 安装状态
2. `detect_boards` - 检测连接的 Arduino 板卡
3. `create_led_blink` - 创建 LED 闪烁项目
4. `compile_sketch` - 编译 Arduino 代码
5. `upload_sketch` - 上传代码到板卡
6. `monitor_serial` - 监控串口输出
7. `full_workflow_led_blink` - 完整工作流（一键完成）

**意图解析：**
```python
def parse_led_blink_intent(user_input: str) -> ProjectConfig:
    """从自然语言提取项目配置"""
    # 提取板卡类型（uno/nano/pico）
    # 提取引脚号
    # 提取闪烁间隔
    # 返回 ProjectConfig
```

## MCP 工具详解

### 1. check_arduino_cli

检查 arduino-cli 是否已安装。

**输入：** 无

**输出：**
```
✅ arduino-cli is installed and ready
```

### 2. detect_boards

检测连接的 Arduino 板卡，支持连接验证和类型过滤。

**输入：**
- `verify_connection` (bool, 默认 true) - 是否验证连接
- `board_type` (string, 可选) - 板卡类型（pico/uno/nano）

**输出：**
```
✅ Detected 1 board(s):

1. Port: COM7
   FQBN: arduino:mbed_rp2040:pico
   Name: Raspberry Pi Pico
   Status: ✅ Accessible
```

### 3. create_led_blink

从自然语言描述创建 LED 闪烁项目。

**输入：**
- `user_input` (string, 必需) - 自然语言描述
- `project_name` (string, 默认 "led_blink") - 项目名称
- `output_dir` (string, 默认 "./arduino_projects") - 输出目录

**示例：**
```
用 Arduino Uno 做一个 LED 闪烁，13 号引脚，每 2 秒闪一次
```

**输出：**
```
✅ LED Blink project created!

📁 Location: ./arduino_projects/led_blink
📌 Board: arduino:avr:uno
📍 LED Pin: 13
⏱️  Interval: 2000ms

📦 Generated files:
  • led_blink.ino (Arduino code)
  • diagram.json (Wokwi simulation)
  • wokwi.toml (Wokwi config)
```

### 4. compile_sketch

编译 Arduino 代码。

**输入：**
- `sketch_path` (string, 必需) - 代码路径
- `board_fqbn` (string, 默认 "arduino:avr:uno") - 板卡 FQBN

**输出：**
```
✅ Compilation successful!
```

### 5. upload_sketch

上传代码到 Arduino 板卡。

**输入：**
- `sketch_path` (string, 必需) - 代码路径
- `board_fqbn` (string, 默认 "arduino:avr:uno") - 板卡 FQBN
- `port` (string, 可选) - 串口（自动检测）

**输出：**
```
✅ Upload successful!

Port: COM7
```

### 6. monitor_serial

监控串口输出。

**输入：**
- `port` (string, 必需) - 串口
- `baud_rate` (int, 默认 9600) - 波特率
- `duration` (int, 默认 10) - 监控时长（秒）

**输出：**
```
📡 Serial Monitor (Port: COM7, Baud: 9600)
Duration: 10s

LED Blink Started
Pin: 13
Interval: 1000ms
LED ON
LED OFF
...
```

### 7. full_workflow_led_blink

完整工作流：解析 → 生成 → 编译 → 检测 → 上传 → 监控

**输入：**
- `user_input` (string, 必需) - 自然语言描述
- `auto_upload` (bool, 默认 true) - 是否自动上传
- `monitor_after_upload` (bool, 默认 true) - 是否监控串口

**输出：**
```
🚀 Starting full LED blink workflow...

Step 1: Parsing intent and generating code...
✅ Code generated at: ./arduino_projects/led_blink

🎮 Wokwi Simulation Files Generated:
   • diagram.json (circuit diagram)
   • wokwi.toml (configuration)

Step 2: Compiling...
✅ Compilation successful

Step 3: Detecting board and uploading...
Looking for pico board...
✅ Found pico at COM7
✅ Upload successful to COM7

Step 4: Monitoring serial output...
LED ON
LED OFF
...

🎉 Workflow complete! Your LED should be blinking now.
```

## 功能特性

### 板卡检测

**连接验证：**
- 实际尝试打开串口
- 确保串口可访问
- 过滤被占用的串口

**类型匹配：**
- 支持按类型检测（pico/uno/nano）
- 精确匹配 name/FQBN
- 不会误报其他板卡

**错误提示：**
```
❌ No pico board detected.

请检查：
  1. Pico 开发板是否已连接
  2. USB 线是否支持数据传输
  3. 驱动是否已安装
  4. 串口是否被占用

💡 建议：先在 Wokwi 中仿真测试！
```

### Wokwi 仿真

**自动生成：**
- 每个项目自动生成 diagram.json
- 包含完整的电路连接
- 支持多种板卡和组件

**使用方式：**
1. 在 VS Code 中打开项目文件夹
2. 打开 diagram.json
3. 按 F1 → "Wokwi: Start Simulator"
4. 查看电路和运行效果

**优势：**
- 无需硬件即可测试
- 验证代码正确性
- 查看接线图
- 快速迭代

### 串口管理

**自动释放：**
- 检测占用串口的进程
- 自动关闭占用进程
- 等待串口释放

**支持场景：**
- Arduino IDE 占用串口
- 串口监视器占用
- 其他工具占用

**提高成功率：**
- 避免"串口被占用"错误
- 自动重试机制
- 友好的错误提示

## 使用示例

### 示例 1：创建 Pico LED 项目

```
用户：用 Pico 做一个 LED 闪烁，25 号引脚

系统：
1. ✅ 生成代码和 Wokwi 仿真
2. ✅ 编译代码
3. 🔍 检测 Pico 板卡
4. ✅ 上传到硬件
5. 📡 监控串口输出
```

### 示例 2：Wokwi 仿真

```
用户：用 Uno 做一个 LED 闪烁，13 号引脚

系统：
1. ✅ 生成代码和 Wokwi 文件
2. 💡 推荐：先在 Wokwi 中仿真
3. 用户在 VS Code 中打开 diagram.json
4. 启动 Wokwi 仿真器
5. 查看电路和运行效果
```

### 示例 3：手动检测板卡

```python
# 检测所有板卡
mcp.detect_boards(verify_connection=True)

# 检测特定板卡
mcp.detect_boards(board_type="pico")
```

## 开发

### 项目结构

```
arduino-mcp-server/
├── src/arduino_mcp_server/
│   ├── __init__.py
│   ├── __main__.py
│   ├── models.py           # 数据模型
│   ├── templates.py        # 代码模板
│   ├── arduino_cli.py      # Arduino CLI 封装
│   ├── code_generator.py   # 代码生成器
│   ├── port_manager.py     # 串口管理
│   ├── wokwi_generator.py  # Wokwi 仿真生成
│   └── server.py           # MCP Server 主入口
├── examples/
│   ├── example-conversations.md
│   └── kiro-mcp-config.json
├── pyproject.toml
└── README.md
```

### 运行测试

**CI 测试套件（推荐）**：

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 单元测试（无需 arduino-cli）
python -m pytest tests/ -m unit -v

# 单元 + 集成测试（需要 arduino-cli）
python -m pytest tests/ -m "unit or integration" -v
```

详见 [docs/ci/README.md](../docs/ci/README.md)。

**原有脚本测试**：

```bash
# 基础测试
python test_basic.py

# 板卡检测测试
python test_board_detection.py

# 完整工作流测试
python test_full_workflow.py

# Wokwi 测试
python test_wokwi.py
```

### 添加新功能

1. 在 `models.py` 中定义数据模型
2. 在 `templates.py` 中添加代码模板
3. 在 `code_generator.py` 中实现生成逻辑
4. 在 `server.py` 中添加 MCP 工具
5. 编写测试验证功能

## 支持的硬件

- ✅ Arduino Uno
- ✅ Arduino Nano
- ✅ Raspberry Pi Pico
- ⏳ ESP32（计划中）
- ⏳ Arduino Mega（计划中）

## 常见问题

### Q: arduino-cli 未找到？

**A:** 安装 arduino-cli：
```bash
# Windows
winget install ArduinoSA.CLI

# macOS
brew install arduino-cli

# Linux
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
```

### Q: 检测不到板卡？

**A:** 检查：
1. 板卡是否已连接
2. USB 线是否支持数据传输
3. 驱动是否已安装
4. 串口是否被占用

### Q: 串口被占用？

**A:** 系统会自动尝试释放，如果失败：
1. 关闭 Arduino IDE
2. 关闭串口监视器
3. 重新运行

### Q: 没有硬件怎么办？

**A:** 使用 Wokwi 仿真：
1. 生成项目时会自动创建 diagram.json
2. 在 VS Code 中打开
3. 启动 Wokwi 仿真器
4. 无需硬件即可测试

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**版本**: 0.2.0  
**状态**: ✅ 生产就绪  
**最后更新**: 2026-02-02
