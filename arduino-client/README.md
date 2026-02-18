# Arduino Client — Arduino 自然语言端到端开发

基于 LLM + arduino-cli 的嵌入式开发 Client，通过自然语言描述需求，由大模型生成代码、自动编译、上传与测试。

> **注意**: 这是重构后的独立 Client 工具，不依赖 MCP Server。如需使用 MCP Server 版本，请参考 `../arduino-mcp-server/`。

## 能力概览

- **编码**：Arduino C++ 代码生成（LLM API）
- **编译**：arduino-cli
- **上传/调试**：arduino-cli
- **仿真**：Wokwi 仿真（未检测到板卡时可用，支持通过串口输出/指令获取反馈）
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

# 2. 首次使用：直接运行（无参数）进入交互式终端
python -m arduino_client
# 或 arduino-client

# 3. 在菜单中选 1 完成 LLM API 配置（API Key、Base URL、模型），无需事先安装 arduino-cli
# 4. 之后可在同一终端选 2～8：检测板卡、生成代码、编译上传、仿真运行（无板时可用）等，或输入 exit 退出后使用单条命令
```

**首次安装即完成配置**：运行 `arduino-client` 或 `python -m arduino_client`（不加子命令）会直接进入交互式终端，菜单第一项即为「配置 LLM API」，按提示即可完成首次配置。

**提示**：
- 需要单条命令时：`arduino-client gen "..." 项目名`、`arduino-client setup`（仅配置）、`arduino-client interactive`（仅进入菜单）
- 配置支持 Kimi K2、OpenAI 等，可保存到当前目录或用户主目录
- 安装 `rich` 库可获得更好终端 UI：`pip install arduino-client[ui]`

**注意**：
- 如果 `arduino-client` 命令找不到，可以使用 `python -m arduino_client` 替代
- Windows Store 版本的 Python 可能需要将 Scripts 目录添加到 PATH，或使用 `python -m` 方式
- 如果 `python -m arduino_client` 也失败，请确保已重新安装包：`pip install -e arduino-client/ --force-reinstall`

**自动添加 PATH（方案二）**：

如果 `arduino-client` 命令找不到，可以运行辅助脚本自动添加 PATH：

**PowerShell 方式**：

如果遇到"禁止运行脚本"的错误，需要使用以下方式之一：

```powershell
# 方式 1：使用 Bypass 执行策略（推荐，仅当前会话）
powershell -ExecutionPolicy Bypass -File .\arduino-client\scripts\add_to_path.ps1

# 方式 2：临时修改当前会话的执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\arduino-client\scripts\add_to_path.ps1

# 方式 3：永久修改执行策略（需要管理员权限）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\arduino-client\scripts\add_to_path.ps1
```

**Windows Batch 方式**（无需修改执行策略）：

```cmd
.\arduino-client\scripts\add_to_path.bat
```

**脚本功能**：
- 自动查找 `arduino-client.exe` 的安装位置
- 检查是否已在 PATH 中（避免重复添加）
- 自动添加到用户 PATH 环境变量
- **自动刷新当前会话的 PATH**（无需重新打开终端）

**运行后**：
- 脚本会自动刷新当前 PowerShell 会话的 PATH
- 如果成功，会显示 "✓ arduino-client is now available!"
- 可以直接运行 `arduino-client setup` 或 `arduino-client --version`
- 如果仍然找不到，请关闭并重新打开 PowerShell 窗口

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

### 交互式终端（可停留的客户端）

除了单次命令，也可以进入**交互式终端**，在同一个会话里用菜单完成配置、检测、生成、编译、上传等操作（类似可停留的客户端，而不是每次敲一条命令就退出）：

```bash
python -m arduino_client interactive
# 或简写
python -m arduino_client i
```

进入后会显示菜单：
- **1** — 配置 LLM API（无需安装 arduino-cli）
- **2** — 检测板卡（未检测到板卡时可使用 7 仿真）
- **3** — 生成代码（自然语言 → 工程）
- **4** — 编译工程
- **5** — 上传固件
- **6** — Demo: Blink（有板则上传，无板则自动运行 Wokwi 仿真）
- **7** — 仿真运行（Wokwi，无板时可用，可获取串口反馈）
- **8** — 退出

输入 `help` 或 `exit` 也可。安装可选依赖 `arduino-client[ui]` 后，交互界面会使用 rich 美化显示。

## 使用流程

1. **描述需求**：自然语言（如「用 Arduino Uno 做一个 LED 闪烁，13 号引脚」）
2. **大模型分析**：解析需求并生成 Arduino 代码
3. **自动编译**：arduino-cli 编译
4. **上传运行**：arduino-cli 上传到设备
5. **串口监控**：验证输出

## 仿真（无板时可用）

当未检测到板卡时，可使用 **Wokwi 仿真**运行固件，并通过串口输出或期望文本做「通过指令获取反馈」的校验。

- **菜单 7**：对已编译工程生成 Wokwi 配置（`diagram.json`、`wokwi.toml`）并运行 `wokwi-cli`，终端会显示仿真串口输出；可输入「期望串口出现某文本」做自动化判定。
- **菜单 6 Demo**：若无板卡，会自动生成代码、编译、生成 Wokwi 项目并运行仿真，输出串口内容。

**仿真前置**：
- 安装 [wokwi-cli](https://docs.wokwi.com/wokwi-ci/cli-usage)：`npm install -g wokwi-cli`
- 在 [Wokwi CI Dashboard](https://wokwi.com/dashboard/ci) 创建 token，并设置环境变量 `WOKWI_CLI_TOKEN`

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
