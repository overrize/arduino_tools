# 🧪 Kiro 测试命令

> 在 Kiro 中测试 Arduino MCP Server

## ✅ 配置已完成

配置文件位置：`.kiro/settings/mcp.json`

配置内容：
```json
{
  "mcpServers": {
    "arduino": {
      "command": "python",
      "args": ["-m", "arduino_mcp_server"],
      "cwd": "E:\\embedd_tools\\arduino_tools\\arduino-mcp-server\\src",
      "env": {
        "PYTHONPATH": "E:\\embedd_tools\\arduino_tools\\arduino-mcp-server\\src"
      },
      "disabled": false,
      "autoApprove": ["check_arduino_cli", "detect_boards"]
    }
  }
}
```

---

## 🔄 下一步

### 1. 重启 Kiro

关闭并重新打开 Kiro，或者重新加载 MCP 配置。

### 2. 检查 MCP 连接

在 Kiro 的 MCP 面板中应该能看到 "arduino" 服务器。

---

## 🧪 测试命令

### 测试 1: 检查环境 ⭐

```
检查 Arduino 环境
```

**预期输出**：
```
✅ arduino-cli is installed and ready
```

---

### 测试 2: 检测板子 ⭐

```
检测连接的 Arduino 板
```

**预期输出**：
```
Detected boards:
  • Port: COM7
    FQBN: arduino:mbed_rp2040:pico
    Name: Raspberry Pi Pico
```

---

### 测试 3: 完整工作流 ⭐⭐⭐

```
用 Raspberry Pi Pico 做一个 LED 闪烁，25 号引脚，每秒闪一次
```

**预期流程**：
1. 🔍 解析意图
2. 📝 生成代码
3. 🔨 编译项目
4. 📤 上传到 Pico
5. 📊 监控串口输出
6. ✅ LED 开始闪烁

**预期输出**：
```
🚀 Starting full LED blink workflow...

Step 1: Parsing intent and generating code...
✅ Code generated at: ./arduino_projects/led_blink

Step 2: Compiling...
✅ Compilation successful

Step 3: Detecting board and uploading...
✅ Upload successful to COM7

Step 4: Monitoring serial output...
LED Blink Started
Pin: 25
Interval: 1000ms
LED ON
LED OFF
LED ON
LED OFF

🎉 Workflow complete! Your LED should be blinking now.
```

---

### 测试 4: 改变闪烁频率

```
改成每 2 秒闪一次
```

或者：

```
用 Pico 做一个 LED 闪烁，25 号引脚，每 2 秒闪一次
```

**预期结果**：LED 闪烁变慢

---

### 测试 5: 分步执行

#### 5.1 创建项目
```
创建一个 LED 闪烁项目，用 Pico，25 号引脚
```

#### 5.2 编译
```
编译项目 ./arduino_projects/led_blink
```

#### 5.3 上传
```
上传项目到板子
```

#### 5.4 监控
```
监控 COM7 的串口输出
```

---

### 测试 6: 不同的板型

#### Arduino Uno
```
用 Arduino Uno 做一个 LED 闪烁，13 号引脚
```

#### Arduino Nano
```
用 Arduino Nano 做一个 LED 闪烁，13 号引脚
```

---

## 🐛 故障排查

### 问题 1: MCP Server 未连接

**检查**：
1. 查看 Kiro 的 MCP 面板
2. 确认 "arduino" 服务器状态

**解决**：
```bash
# 测试 MCP Server
cd arduino-mcp-server
python test_mcp_server.py
```

---

### 问题 2: 工具调用失败

**检查 arduino-cli**：
```bash
arduino-cli version
```

**检查板子**：
```bash
arduino-cli board list
```

---

### 问题 3: 编译失败

**检查核心**：
```bash
arduino-cli core list
```

应该看到：
- arduino:avr
- arduino:mbed_rp2040

---

## 📊 成功标志

如果一切正常，你应该能够：

- ✅ 在 Kiro 中看到 Arduino MCP Server 连接
- ✅ 使用自然语言创建项目
- ✅ 自动编译和上传
- ✅ 看到 LED 实际闪烁
- ✅ 监控串口输出

---

## 💡 提示

### 自然语言技巧

**好的描述**：
```
✅ "用 Pico 做一个 LED 闪烁，25 号引脚，每秒闪一次"
✅ "Arduino Uno LED 闪烁 13 号引脚"
✅ "LED 闪烁，每 2 秒一次"
```

**需要改进的描述**：
```
⚠️ "做个灯" - 缺少板型和引脚
⚠️ "Arduino" - 太模糊
⚠️ "闪烁" - 需要更多信息
```

### 最佳实践

1. **明确指定板型**：Uno / Nano / Pico
2. **指定引脚号**：13 / 25 等
3. **可选：指定频率**：每秒 / 每 2 秒

---

## 🎯 下一步功能

测试成功后，可以尝试：

1. **按钮控制**（即将支持）
2. **传感器读取**（即将支持）
3. **串口绘图**（即将支持）

---

## 📝 测试记录

### 测试日期：2026-02-01

| 测试项 | 状态 | 备注 |
|--------|------|------|
| MCP 连接 | ⏳ 待测试 | |
| 检查环境 | ⏳ 待测试 | |
| 检测板子 | ⏳ 待测试 | |
| 完整工作流 | ⏳ 待测试 | |
| LED 闪烁 | ⏳ 待测试 | |

---

**准备就绪！现在可以在 Kiro 中测试了！** 🚀
