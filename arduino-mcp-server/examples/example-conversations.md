# Arduino MCP Server - 示例对话

## 场景 1: 第一次使用 - 完整流程

### 用户
```
我想用 Arduino Uno 做一个 LED 闪烁程序，让板载 LED（13 号引脚）每秒闪一次
```

### Kiro 的处理流程
1. 识别用户意图：LED 闪烁项目
2. 调用 `full_workflow_led_blink` 工具
3. 自动完成：解析 → 生成 → 编译 → 上传 → 监控

### 预期输出
```
🚀 Starting full LED blink workflow...

Step 1: Parsing intent and generating code...
✅ Code generated at: ./arduino_projects/led_blink

Step 2: Compiling...
✅ Compilation successful

Step 3: Detecting board and uploading...
✅ Upload successful to COM3

Step 4: Monitoring serial output...
LED Blink Started
Pin: 13
Interval: 1000ms
LED ON
LED OFF
LED ON
LED OFF

🎉 Workflow complete! Your LED should be blinking now.
```

---

## 场景 2: 分步调试

### 用户
```
先检查一下我的 Arduino 环境是否正常
```

### Kiro
调用 `check_arduino_cli` 工具

### 输出
```
✅ arduino-cli is installed and ready
```

---

### 用户
```
检测一下连接的板子
```

### Kiro
调用 `detect_boards` 工具

### 输出
```
Detected boards:
  • Port: COM3
    FQBN: arduino:avr:uno
    Name: Arduino Uno
```

---

### 用户
```
好的，帮我创建一个 LED 闪烁项目，使用 7 号引脚，每 2 秒闪一次
```

### Kiro
调用 `create_led_blink` 工具

### 输出
```
✅ LED Blink project created!

📁 Location: ./arduino_projects/led_blink
📌 Board: arduino:avr:uno
📍 LED Pin: 7
⏱️  Interval: 2000ms

Next steps:
1. Compile: use compile_sketch tool
2. Upload: use upload_sketch tool
```

---

### 用户
```
编译这个项目
```

### Kiro
调用 `compile_sketch` 工具

### 输出
```
✅ Compilation successful!

Sketch uses 924 bytes (2%) of program storage space.
Global variables use 9 bytes (0%) of dynamic memory.
```

---

### 用户
```
上传到板子
```

### Kiro
调用 `upload_sketch` 工具

### 输出
```
✅ Upload successful!

Port: COM3

avrdude: AVR device initialized and ready to accept instructions
avrdude: writing flash (924 bytes):
avrdude: 924 bytes of flash written
avrdude done. Thank you.
```

---

### 用户
```
监控串口输出看看
```

### Kiro
调用 `monitor_serial` 工具

### 输出
```
📡 Serial Monitor (Port: COM3, Baud: 9600)
Duration: 10s

LED Blink Started
Pin: 7
Interval: 2000ms
LED ON
LED OFF
LED ON
LED OFF
LED ON
```

---

## 场景 3: 快速原型 - 不同配置

### 用户
```
用 Arduino Nano 做一个快速闪烁的 LED，13 号引脚，每 0.5 秒闪一次
```

### Kiro
调用 `full_workflow_led_blink` 工具

### 解析结果
- Board: arduino:avr:nano
- Pin: 13
- Interval: 500ms (虽然用户说 0.5 秒，但目前解析器可能识别为默认值)

### 改进建议
用户可以更明确地说：
```
用 Arduino Nano 做一个 LED 闪烁，13 号引脚，每秒闪两次
```
或者分步创建时指定间隔。

---

## 场景 4: 使用 Raspberry Pi Pico

### 用户
```
我有一个 Raspberry Pi Pico，想让 LED 闪烁，用 25 号引脚
```

### Kiro
调用 `full_workflow_led_blink` 工具

### 解析结果
- Board: rp2040:rp2040:rpipico
- Pin: 25 (Pico 的板载 LED)
- Interval: 1000ms

### 注意事项
确保已安装 Pico 核心：
```bash
arduino-cli core install rp2040:rp2040 --additional-urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
```

---

## 场景 5: 错误处理

### 用户
```
用 Arduino Uno 做一个 LED 闪烁
```

### 如果没有连接板子

### 输出
```
🚀 Starting full LED blink workflow...

Step 1: Parsing intent and generating code...
✅ Code generated at: ./arduino_projects/led_blink

Step 2: Compiling...
✅ Compilation successful

Step 3: Detecting board and uploading...
❌ No board detected. Please connect Arduino.
```

### Kiro 的建议
```
看起来没有检测到 Arduino 板。请检查：
1. USB 线是否连接
2. 驱动是否安装
3. 在设备管理器中是否显示端口

连接好后，可以用 "检测板子" 命令验证。
```

---

## 场景 6: 修改现有项目

### 用户
```
我想把刚才的 LED 闪烁改成每 3 秒闪一次
```

### Kiro
重新调用 `create_led_blink` 工具，指定新的间隔

### 用户
```
创建一个 LED 闪烁项目，Arduino Uno，13 号引脚，每 3 秒闪一次
```

### 然后
```
编译并上传
```

---

## 场景 7: 多个 LED（未来功能预览）

### 用户（未来）
```
我想控制两个 LED，一个在 13 号引脚，一个在 12 号引脚，交替闪烁
```

### 预期功能
- 解析多个组件
- 生成更复杂的代码
- 支持自定义逻辑

---

## 场景 8: 传感器读取（未来功能预览）

### 用户（未来）
```
用 DHT22 传感器读取温湿度，传感器接在 2 号引脚，每 5 秒输出一次数据
```

### 预期功能
- 识别传感器类型
- 自动添加库依赖
- 生成传感器读取代码
- 串口输出格式化数据

---

## 提示词技巧

### ✅ 好的提示词
```
"用 Arduino Uno 做一个 LED 闪烁，13 号引脚，每秒闪一次"
"Arduino Nano LED blink pin 7 every 2 seconds"
"Pico LED 闪烁 25 号引脚"
```

### ⚠️ 需要改进的提示词
```
"做个闪灯" → 缺少板型和引脚信息
"Arduino 程序" → 太模糊
"LED" → 需要更多上下文
```

### 💡 最佳实践
1. 明确指定板型（Uno/Nano/Pico）
2. 指定引脚号
3. 如果需要特定频率，明确说明
4. 使用自然语言，不需要技术术语

---

## 调试技巧

### 问题：编译失败
```
用户: "为什么编译失败了？"
Kiro: 查看编译输出，可能是：
- 核心未安装
- 语法错误
- 库缺失
```

### 问题：上传失败
```
用户: "上传不了"
Kiro: 
1. 先检测板子："检测板子"
2. 确认端口是否正确
3. 检查是否有其他程序占用串口
```

### 问题：看不到输出
```
用户: "LED 不闪"
Kiro:
1. 监控串口："监控串口输出"
2. 检查硬件连接
3. 确认引脚号是否正确
```

---

## 总结

Arduino MCP Server 让嵌入式开发变得简单：
- 🗣️ 用自然语言描述需求
- 🤖 AI 理解并生成代码
- ⚡ 自动编译和上传
- 🎉 立即看到结果

从想法到闪烁的 LED，只需要一句话！
