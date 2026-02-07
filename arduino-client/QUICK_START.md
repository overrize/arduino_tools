# Arduino Client 快速开始

## 安装

```bash
cd arduino-client
pip install -e .
```

## 配置

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 配置示例（Kimi K2）

```bash
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.moonshot.cn/v1
OPENAI_MODEL=kimi-k2-0905-preview
```

### 配置示例（OpenAI）

```bash
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini
```

## 使用

### 1. 检测板卡

```bash
python -m arduino_client detect
```

### 2. 生成代码

```bash
python -m arduino_client gen "用 Arduino Uno 做一个 LED 闪烁，13 号引脚" blink_demo
```

### 3. 生成并编译

```bash
python -m arduino_client gen "用 Arduino Uno 做一个 LED 闪烁，13 号引脚" blink_demo --build
```

### 4. 完整流程（生成+编译+上传）

```bash
python -m arduino_client gen "用 Arduino Uno 做一个 LED 闪烁，13 号引脚" blink_demo --build --flash
```

### 5. Demo

```bash
python -m arduino_client demo blink --board uno --flash
```

## Python API

```python
from arduino_client import ArduinoClient

client = ArduinoClient(work_dir=".")

# 检测板卡
boards = client.detect_boards()
print(f"检测到 {len(boards)} 个板卡")

# 生成代码
project_dir = client.generate(
    "用 Arduino Uno 做一个 LED 闪烁，13 号引脚",
    "blink_demo"
)

# 编译
result = client.build(project_dir, "arduino:avr:uno")
if result.success:
    print(f"编译成功: {result.build_path}")

# 上传
upload_result = client.upload(
    project_dir,
    "arduino:avr:uno",
    port=boards[0].port
)
if upload_result.success:
    print(f"上传成功到 {upload_result.port}")
```

## 更多信息

- 完整文档：[README.md](README.md)
- 开发经验：[docs/LESSONS.md](docs/LESSONS.md)
- Cursor Skills：[docs/skills/](docs/skills/)
