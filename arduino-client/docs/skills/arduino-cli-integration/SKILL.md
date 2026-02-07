# Arduino CLI 集成技能

## 概述

本技能用于处理 Arduino CLI 集成相关任务，包括板卡检测、编译、上传、串口监控等。

## 核心概念

### arduino-cli 命令

- `arduino-cli board list` - 检测板卡
- `arduino-cli compile --fqbn <fqbn> <sketch>` - 编译工程
- `arduino-cli upload -p <port> --fqbn <fqbn> <sketch>` - 上传固件
- `arduino-cli monitor -p <port>` - 串口监控

### FQBN（Fully Qualified Board Name）

格式：`<package>:<architecture>:<board>`

示例：
- `arduino:avr:uno` - Arduino Uno
- `arduino:avr:nano` - Arduino Nano
- `arduino:mbed_rp2040:pico` - Raspberry Pi Pico
- `esp32:esp32:esp32` - ESP32

### 板卡检测

1. 使用 `arduino-cli board list --format json` 获取板卡列表
2. 解析 JSON 格式（注意新旧版本格式差异）
3. 验证串口连接（可选）

### 串口管理

- 上传前需要关闭占用串口的进程（Arduino IDE、串口监视器等）
- 使用 `psutil` 查找占用进程
- 使用 `pyserial` 验证串口可用性

## 常见问题

### 1. 板卡检测失败

**原因**：
- arduino-cli 未安装或不在 PATH
- 板卡未连接或驱动未安装
- 串口被占用

**解决**：
- 检查 arduino-cli 安装：`arduino-cli version`
- 检查板卡连接和驱动
- 关闭占用串口的程序

### 2. 编译失败

**原因**：
- FQBN 不正确
- 缺少库依赖
- 代码语法错误

**解决**：
- 确认 FQBN 正确
- 安装所需库：`arduino-cli lib install <library>`
- 检查代码语法

### 3. 上传失败

**原因**：
- 串口被占用
- 板卡未进入上传模式
- FQBN 不匹配

**解决**：
- 关闭占用串口的程序
- 按住 RESET 按钮或使用 bootloader 模式
- 确认 FQBN 与板卡匹配

## 代码示例

### 板卡检测

```python
from arduino_client import ArduinoClient

client = ArduinoClient()
boards = client.detect_boards()
for board in boards:
    print(f"串口: {board.port}, FQBN: {board.fqbn}")
```

### 编译和上传

```python
from arduino_client import ArduinoClient

client = ArduinoClient()
# 编译
result = client.build("my_project", "arduino:avr:uno")
if result.success:
    # 上传
    upload_result = client.upload("my_project", "arduino:avr:uno")
```

## 参考

- [Arduino CLI 文档](https://arduino.github.io/arduino-cli/)
- [FQBN 格式说明](https://arduino.github.io/arduino-cli/latest/package-index-specification/#platform)
