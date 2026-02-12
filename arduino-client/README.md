# Arduino Client — Arduino 自然语言端到端开发

基于 LLM + arduino-cli 的嵌入式开发 Client，通过自然语言描述需求，由大模型生成代码、自动编译、上传与测试。

> **注意**: 这是重构后的独立 Client 工具，不依赖 MCP Server。如需使用 MCP Server 版本，请参考 `../arduino-mcp-server/`。

## 能力概览

- **编码**：Arduino C++ 代码生成（LLM API）
- **编译**：arduino-cli
- **上传/调试**：arduino-cli
- **自动化测试**：串口监控
- **目标**：快速原型开发，从想法到运行代码

## 前置条件

- Python 3.10+
- [arduino-cli](https://arduino.github.io/arduino-cli/)
- LLM API Key（OpenAI 或 Kimi）

## 快速开始

### 方式一：从项目根目录安装（推荐）⭐

```bash
# 1. 在 arduino_tools 项目根目录执行
pip install -e arduino-client/

# 2. 运行交互式配置向导（首次使用推荐）
arduino-client setup
# 向导会引导你选择 API 提供商并输入 API Key

# 3. 开始使用
arduino-client gen "用 Arduino Uno 做一个 LED 闪烁，13 号引脚" blink_demo --build --flash
```

**提示**：
- 安装后首次运行任何命令时，如果未配置会提示运行 `arduino-client setup`
- 配置向导支持 Kimi K2、OpenAI 和其他兼容 API
- 配置可保存到当前目录（项目级）或用户主目录（全局）
- 安装 `rich` 库可获得更好的终端 UI 体验：`pip install arduino-client[ui]`

**注意**：
- 如果 `arduino-client` 命令找不到，可以使用 `python -m arduino_client` 替代
- Windows Store 版本的 Python 可能需要将 Scripts 目录添加到 PATH，或使用 `python -m` 方式
- 如果 `python -m arduino_client` 也失败，请确保已重新安装包：`pip install -e arduino-client/ --force-reinstall`

**自动添加 PATH（方案二）**：

如果 `arduino-client` 命令找不到，可以运行辅助脚本自动添加 PATH：

```powershell
# PowerShell 方式
.\arduino-client\scripts\add_to_path.ps1

# 或 Windows Batch 方式
.\arduino-client\scripts\add_to_path.bat
```

脚本会自动查找 `arduino-client.exe` 的安装位置并添加到用户 PATH。添加后需要**重新打开终端窗口**才能生效。

### 方式二：进入目录安装（兼容旧方式）

```bash
# 1. 进入目录
cd arduino-client

# 2. 安装 Client
pip install -e .

# 3. 运行配置向导
arduino-client setup

# 4. 运行
arduino-client gen "用 Arduino Uno 做一个 LED 闪烁，13 号引脚" blink_demo --build --flash
```

## 大模型配置

交互式生成代码前需配置 API。复制 `.env.example` 为 `.env` 并填入。

**Kimi K2**（推荐）：
```bash
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.moonshot.cn/v1
OPENAI_MODEL=kimi-k2-0905-preview   # 或 kimi-k2-turbo-preview
```

**OpenAI**：`OPENAI_API_KEY=sk-xxx` 即可。

支持任意兼容 OpenAI 格式的 API。

## 项目结构

```
arduino-client/
├── arduino_client/          # Client 包
│   ├── client.py           # ArduinoClient 可编程 API
│   ├── cli.py              # CLI 入口
│   ├── builder.py          # 编译模块
│   ├── uploader.py         # 上传模块
│   ├── monitor.py          # 串口监控
│   ├── board_detector.py   # 板卡检测
│   ├── code_generator.py   # LLM 代码生成
│   └── ...
├── docs/                   # 文档
│   ├── LESSONS.md         # 开发经验
│   └── skills/            # Cursor Skills
├── demos/                 # 示例项目
└── pyproject.toml         # 包配置
```

## 可编程 API

```python
from arduino_client import ArduinoClient

client = ArduinoClient(work_dir=".")
# 检测板卡
boards = client.detect_boards()
# 生成代码
project_dir = client.generate("用 Arduino Uno 做一个 LED 闪烁，13 号引脚", "blink_demo")
# 编译
result = client.build(project_dir, "arduino:avr:uno")
# 上传
upload_result = client.upload(project_dir, "arduino:avr:uno", port=boards[0].port)
```

## CLI 命令

```bash
# 检测板卡
python -m arduino_client detect

# 生成代码
python -m arduino_client gen "用 Arduino Uno 做一个 LED 闪烁，13 号引脚" blink_demo

# 生成并编译
python -m arduino_client gen "..." blink_demo --build

# 生成、编译并上传
python -m arduino_client gen "..." blink_demo --build --flash

# 编译工程
python -m arduino_client build my_project --fqbn arduino:avr:uno

# 上传固件
python -m arduino_client upload my_project --fqbn arduino:avr:uno

# Demo
python -m arduino_client demo blink --board uno --flash
```

## 使用流程

1. **描述需求**：自然语言（如「用 Arduino Uno 做一个 LED 闪烁，13 号引脚」）
2. **大模型分析**：解析需求并生成 Arduino 代码
3. **自动编译**：arduino-cli 编译
4. **上传运行**：arduino-cli 上传到设备
5. **串口监控**：验证输出

## 支持板卡

- Arduino Uno
- Arduino Nano
- Raspberry Pi Pico
- ESP32
- 其他 arduino-cli 支持的板卡

## 与 MCP Server 版本的区别

| 特性 | Client 版本（本目录） | MCP Server 版本（../arduino-mcp-server/） |
|------|---------------------|------------------------------------------|
| 使用方式 | CLI/Python API | 通过 kiro MCP Server |
| 代码生成 | LLM API | 模板驱动 |
| 依赖 | 独立工具 | 需要 kiro |
| 灵活性 | 高 | 中 |

## 开发经验

改动与踩坑记录见 [docs/LESSONS.md](docs/LESSONS.md)。

## License

MIT
