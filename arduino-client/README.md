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

```bash
# 1. 进入目录
cd arduino-client

# 2. 安装 Client（推荐）
pip install -e .

# 3. 配置 API Key（复制 .env.example 为 .env 并填入）
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY=sk-xxx

# 4. 运行
python -m arduino_client gen "用 Arduino Uno 做一个 LED 闪烁，13 号引脚" blink_demo --build --flash
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
