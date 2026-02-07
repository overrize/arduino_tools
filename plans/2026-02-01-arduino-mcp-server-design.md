# Arduino MCP Server 设计文档

> **创建日期：** 2026-02-01  
> **目标：** 构建一个自然语言驱动的 Arduino 端到端开发 MCP Server

---

## 1. 项目概述

### 1.1 目标

创建一个 MCP Server，让用户通过自然语言描述需求，自动完成：
1. Arduino 代码生成
2. 编译验证
3. 烧录到开发板
4. 串口调试支持

### 1.2 用户场景

**初学者场景：**
- 用户："做一个 LED 闪烁程序"
- 系统：自动生成代码、选择引脚、编译上传、提供调试指导

**快速原型场景：**
- 用户："读取 DHT22 温湿度传感器，每 5 秒通过串口输出"
- 系统：生成代码、自动添加库依赖、编译上传、监控输出

### 1.3 设计原则

- **流程简单**：用户只需描述需求，系统处理所有技术细节
- **模块清晰**：每个功能独立，易于测试和扩展
- **渐进式**：从简单功能开始，逐步扩展复杂场景

---

## 2. 技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────┐
│              Kiro IDE / Claude                  │
│           (用户自然语言输入)                      │
└────────────────┬────────────────────────────────┘
                 │ MCP Protocol
┌────────────────▼────────────────────────────────┐
│           Arduino MCP Server                    │
│  ┌──────────────────────────────────────────┐  │
│  │  1. 意图解析层 (Intent Parser)           │  │
│  │     - 解析用户需求                        │  │
│  │     - 提取硬件信息、功能需求              │  │
│  │     - 识别传感器/执行器类型               │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                                │
│  ┌──────────────▼───────────────────────────┐  │
│  │  2. 代码生成层 (Code Generator)          │  │
│  │     - 基于模板生成代码                    │  │
│  │     - 自动添加库依赖                      │  │
│  │     - 引脚分配和配置                      │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                                │
│  ┌──────────────▼───────────────────────────┐  │
│  │  3. 编译上传层 (Build & Upload)          │  │
│  │     - arduino-cli 封装                    │  │
│  │     - 板型检测和配置                      │  │
│  │     - 编译错误处理                        │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                                │
│  ┌──────────────▼───────────────────────────┐  │
│  │  4. 调试支持层 (Debug Support)           │  │
│  │     - 串口监控                            │  │
│  │     - 日志输出                            │  │
│  │     - 错误诊断                            │  │
│  └──────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│          arduino-cli (命令行工具)               │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│         Arduino 开发板 (Uno/Pico/ESP32)         │
└─────────────────────────────────────────────────┘
```

### 2.2 核心模块

#### 模块 1：意图解析层 (Intent Parser)

**职责：**
- 解析自然语言输入
- 提取关键信息：硬件类型、传感器、功能需求
- 生成结构化的项目配置

**输入示例：**
```
"使用 Arduino Uno 做一个温湿度监测器，用 DHT22 传感器，每 5 秒读取一次数据并通过串口输出"
```

**输出示例：**
```json
{
  "board": "arduino:avr:uno",
  "components": [
    {
      "type": "sensor",
      "name": "DHT22",
      "library": "DHT sensor library",
      "pin": 2
    }
  ],
  "features": [
    {
      "type": "serial_output",
      "interval": 5000
    }
  ]
}
```

#### 模块 2：代码生成层 (Code Generator)

**职责：**
- 基于解析结果生成 Arduino 代码
- 管理代码模板库
- 自动处理库依赖

**代码模板结构：**
```
templates/
├── base/
│   ├── setup_serial.ino
│   └── loop_delay.ino
├── sensors/
│   ├── dht22.ino
│   ├── ultrasonic.ino
│   └── button.ino
└── actuators/
    ├── led.ino
    ├── servo.ino
    └── relay.ino
```

**生成策略：**
1. 选择基础模板（setup + loop）
2. 插入传感器/执行器代码片段
3. 添加必要的库引用
4. 配置引脚定义
5. 生成完整的 .ino 文件

#### 模块 3：编译上传层 (Build & Upload)

**职责：**
- 封装 arduino-cli 命令
- 自动检测连接的开发板
- 处理编译错误并提供友好提示

**核心命令封装：**
```bash
# 1. 检测开发板
arduino-cli board list

# 2. 安装核心（如果需要）
arduino-cli core install arduino:avr

# 3. 安装库（如果需要）
arduino-cli lib install "DHT sensor library"

# 4. 编译
arduino-cli compile --fqbn arduino:avr:uno sketch/

# 5. 上传
arduino-cli upload -p COM3 --fqbn arduino:avr:uno sketch/

# 6. 串口监控
arduino-cli monitor -p COM3
```

#### 模块 4：调试支持层 (Debug Support)

**职责：**
- 实时串口监控
- 解析串口输出
- 提供调试建议

**功能：**
- 捕获 Serial.print() 输出
- 识别常见错误模式
- 提供故障排查建议

---

## 3. 硬件支持计划

### 3.1 第一阶段（MVP）

**支持的开发板：**
- Arduino Uno (arduino:avr:uno)
- Arduino Nano (arduino:avr:nano)
- Raspberry Pi Pico (rp2040:rp2040:rpipico)

**支持的组件：**
- LED（数字输出）
- 按钮（数字输入）
- DHT22 温湿度传感器
- 超声波传感器（HC-SR04）

### 3.2 第二阶段

**新增开发板：**
- ESP32 (esp32:esp32:esp32) - Arduino 框架
- Arduino Mega (arduino:avr:mega)

**新增组件：**
- 舵机（Servo）
- 步进电机
- OLED 显示屏
- I2C/SPI 传感器

### 3.3 未来扩展

- ESP-IDF 原生支持（高级模式）
- STM32 系列
- 自定义板型支持

---

## 4. MCP Server 工具定义

### 4.1 核心工具 (Tools)

#### Tool 1: `parse_arduino_intent`
**描述：** 解析用户的自然语言需求，提取硬件和功能信息

**输入参数：**
```typescript
{
  user_input: string;  // 用户的自然语言描述
  board_hint?: string; // 可选的板型提示
}
```

**输出：**
```typescript
{
  board: string;
  components: Component[];
  features: Feature[];
  libraries: string[];
}
```

#### Tool 2: `generate_arduino_code`
**描述：** 基于解析结果生成 Arduino 代码

**输入参数：**
```typescript
{
  project_config: ProjectConfig; // 来自 parse_arduino_intent 的输出
  project_name: string;
  output_dir: string;
}
```

**输出：**
```typescript
{
  sketch_path: string;
  generated_files: string[];
  libraries_needed: string[];
}
```

#### Tool 3: `compile_arduino_sketch`
**描述：** 编译 Arduino 项目

**输入参数：**
```typescript
{
  sketch_path: string;
  board_fqbn: string;
}
```

**输出：**
```typescript
{
  success: boolean;
  output: string;
  errors?: CompileError[];
}
```

#### Tool 4: `upload_to_board`
**描述：** 上传编译好的代码到开发板

**输入参数：**
```typescript
{
  sketch_path: string;
  board_fqbn: string;
  port?: string; // 自动检测如果未提供
}
```

**输出：**
```typescript
{
  success: boolean;
  port: string;
  message: string;
}
```

#### Tool 5: `monitor_serial`
**描述：** 监控串口输出

**输入参数：**
```typescript
{
  port: string;
  baud_rate?: number; // 默认 9600
  duration?: number;  // 监控时长（秒），默认 30
}
```

**输出：**
```typescript
{
  output: string[];
  timestamp: string;
}
```

#### Tool 6: `detect_boards`
**描述：** 检测连接的 Arduino 开发板

**输入参数：** 无

**输出：**
```typescript
{
  boards: {
    port: string;
    fqbn: string;
    name: string;
  }[];
}
```

#### Tool 7: `install_library`
**描述：** 安装 Arduino 库

**输入参数：**
```typescript
{
  library_name: string;
}
```

**输出：**
```typescript
{
  success: boolean;
  message: string;
}
```

### 4.2 辅助工具

#### Tool 8: `list_supported_components`
**描述：** 列出支持的传感器和执行器

**输出：**
```typescript
{
  sensors: string[];
  actuators: string[];
  boards: string[];
}
```

#### Tool 9: `get_component_example`
**描述：** 获取特定组件的示例代码

**输入参数：**
```typescript
{
  component_name: string;
  board?: string;
}
```

**输出：**
```typescript
{
  example_code: string;
  wiring_diagram?: string;
  libraries: string[];
}
```

---

## 5. 工作流示例

### 5.1 完整流程：LED 闪烁

**用户输入：**
```
"用 Arduino Uno 做一个 LED 闪烁程序，连接到 13 号引脚"
```

**系统执行流程：**

1. **意图解析**
   ```
   Tool: parse_arduino_intent
   Input: "用 Arduino Uno 做一个 LED 闪烁程序，连接到 13 号引脚"
   Output: {
     board: "arduino:avr:uno",
     components: [{type: "led", pin: 13}],
     features: [{type: "blink", interval: 1000}]
   }
   ```

2. **代码生成**
   ```
   Tool: generate_arduino_code
   Output: {
     sketch_path: "./arduino_projects/led_blink/led_blink.ino",
     generated_files: ["led_blink.ino"]
   }
   ```

3. **编译**
   ```
   Tool: compile_arduino_sketch
   Output: {success: true, output: "Sketch compiled successfully"}
   ```

4. **检测板子**
   ```
   Tool: detect_boards
   Output: {boards: [{port: "COM3", fqbn: "arduino:avr:uno"}]}
   ```

5. **上传**
   ```
   Tool: upload_to_board
   Output: {success: true, port: "COM3", message: "Upload complete"}
   ```

6. **验证**
   - 提示用户检查 LED 是否闪烁
   - 如果需要调试，使用 monitor_serial

### 5.2 复杂流程：温湿度监测

**用户输入：**
```
"用 Pico 做一个温湿度监测器，DHT22 传感器接 GPIO2，每 5 秒输出一次数据"
```

**系统执行流程：**

1. 解析意图 → 识别 Pico + DHT22 + 串口输出
2. 检查库依赖 → 安装 "DHT sensor library"
3. 生成代码 → 包含 DHT22 读取 + Serial 输出
4. 编译 → 使用 rp2040:rp2040:rpipico
5. 上传 → 自动检测 Pico 端口
6. 监控 → 显示温湿度数据输出

---

## 6. 技术栈

### 6.1 开发语言

**推荐：Python**
- 理由：
  - MCP SDK 支持良好（fastmcp）
  - 丰富的库生态
  - 易于调用命令行工具
  - 字符串处理和模板引擎成熟

**备选：TypeScript**
- 理由：
  - MCP SDK 官方支持
  - 类型安全
  - 异步处理优秀

### 6.2 核心依赖

**Python 实现：**
```
- fastmcp (MCP Server 框架)
- subprocess (调用 arduino-cli)
- jinja2 (代码模板引擎)
- pyserial (串口通信)
- pydantic (数据验证)
```

**TypeScript 实现：**
```
- @modelcontextprotocol/sdk
- child_process (调用 arduino-cli)
- handlebars (代码模板)
- serialport (串口通信)
- zod (数据验证)
```

### 6.3 外部工具

- **arduino-cli**: 核心编译上传工具
- **arduino-pico**: Pico 支持核心
- **esp32 core**: ESP32 支持（第二阶段）

---

## 7. 项目结构

```
arduino-mcp-server/
├── src/
│   ├── server.py              # MCP Server 主入口
│   ├── intent_parser.py       # 意图解析模块
│   ├── code_generator.py      # 代码生成模块
│   ├── arduino_cli.py         # arduino-cli 封装
│   ├── serial_monitor.py      # 串口监控模块
│   └── utils.py               # 工具函数
├── templates/                 # 代码模板
│   ├── base/
│   ├── sensors/
│   └── actuators/
├── tests/                     # 测试
│   ├── test_intent_parser.py
│   ├── test_code_generator.py
│   └── test_arduino_cli.py
├── examples/                  # 示例项目
│   ├── led_blink/
│   └── dht22_monitor/
├── docs/                      # 文档
│   ├── API.md
│   └── TEMPLATES.md
├── pyproject.toml            # Python 依赖
├── README.md
└── LICENSE
```

---

## 8. 实现优先级

### Phase 1: MVP（最小可行产品）

**目标：** 验证核心流程可行性

**功能：**
- ✅ 意图解析（简单场景）
- ✅ 代码生成（LED 闪烁）
- ✅ arduino-cli 封装（编译+上传）
- ✅ 板型检测
- ✅ 支持 Arduino Uno

**交付物：**
- 可以完成 "LED 闪烁" 端到端流程
- 基础 MCP 工具定义

### Phase 2: 扩展组件

**功能：**
- ✅ 更多传感器支持（DHT22, 超声波, 按钮）
- ✅ 串口监控
- ✅ 支持 Raspberry Pi Pico
- ✅ 库依赖自动安装

**交付物：**
- 支持 5+ 常用组件
- 完整的调试支持

### Phase 3: 智能化

**功能：**
- ✅ 更智能的意图解析（复杂场景）
- ✅ 错误诊断和修复建议
- ✅ 代码优化建议
- ✅ 支持 ESP32（Arduino 框架）

**交付物：**
- 初学者友好的错误提示
- 自动故障排查

### Phase 4: 高级功能

**功能：**
- ✅ 项目管理（保存/加载）
- ✅ 多文件项目支持
- ✅ 自定义库支持
- ✅ ESP-IDF 原生支持（可选）

---

## 9. 成功标准

### 9.1 功能性标准

- [ ] 用户可以用自然语言描述需求
- [ ] 系统自动生成可编译的代码
- [ ] 自动检测并上传到正确的开发板
- [ ] 提供实时串口监控
- [ ] 支持至少 3 种开发板
- [ ] 支持至少 5 种常用组件

### 9.2 质量标准

- [ ] 代码生成成功率 > 90%
- [ ] 编译成功率 > 95%
- [ ] 上传成功率 > 90%
- [ ] 平均端到端时间 < 2 分钟
- [ ] 单元测试覆盖率 > 80%

### 9.3 用户体验标准

- [ ] 初学者无需了解 arduino-cli
- [ ] 错误信息清晰易懂
- [ ] 提供接线图和示例
- [ ] 支持中英文交互

---

## 10. 风险和挑战

### 10.1 技术风险

**风险 1：意图解析准确性**
- 挑战：自然语言歧义性
- 缓解：提供明确的提示词模板，支持交互式确认

**风险 2：硬件兼容性**
- 挑战：不同板型的差异
- 缓解：从最常用的板型开始，逐步扩展

**风险 3：库依赖冲突**
- 挑战：不同库版本可能冲突
- 缓解：维护测试过的库版本列表

### 10.2 用户体验风险

**风险 4：错误诊断困难**
- 挑战：硬件问题难以远程诊断
- 缓解：提供详细的故障排查指南

**风险 5：学习曲线**
- 挑战：用户可能不理解生成的代码
- 缓解：添加详细注释，提供学习资源链接

---

## 11. 参考资源

### 11.1 开源项目

- **Arduino_MCP_Server**: https://github.com/AimanMadan/Arduino_MCP_Server
  - 参考：MCP Server 基础结构
  - 限制：只做运行时控制，不生成代码

- **arduino-cli**: https://github.com/arduino/arduino-cli
  - 官方命令行工具
  - 完整文档和示例

- **PlatformIO**: https://platformio.org/
  - 参考：跨平台构建系统
  - 可作为备选工具链

### 11.2 技术文档

- Arduino CLI 文档: https://arduino.github.io/arduino-cli/
- MCP 协议规范: https://modelcontextprotocol.io/
- FastMCP 文档: https://github.com/jlowin/fastmcp
- Arduino 语言参考: https://www.arduino.cc/reference/

### 11.3 硬件资源

- Arduino Uno 引脚图
- Raspberry Pi Pico 引脚图
- 常用传感器数据手册

---

## 12. 下一步行动

### 12.1 立即行动

1. **环境准备**
   - 安装 arduino-cli
   - 安装 Python 3.10+
   - 准备测试硬件（Arduino Uno）

2. **原型验证**
   - 手动测试 arduino-cli 完整流程
   - 验证 LED 闪烁示例
   - 确认串口监控可用

3. **技术选型确认**
   - 确定使用 Python 还是 TypeScript
   - 选择模板引擎
   - 确定项目结构

### 12.2 开发计划

**Week 1: 基础框架**
- MCP Server 骨架
- arduino-cli 封装
- 基础工具定义

**Week 2: 代码生成**
- 模板系统
- LED 闪烁生成
- 编译上传集成

**Week 3: 意图解析**
- 简单场景解析
- 结构化输出
- 端到端测试

**Week 4: 完善和测试**
- 错误处理
- 文档完善
- 用户测试

---

## 附录 A：代码模板示例

### A.1 LED 闪烁模板

```cpp
// LED Blink Example
// Generated by Arduino MCP Server

const int LED_PIN = {{ pin }};

void setup() {
  pinMode(LED_PIN, OUTPUT);
  {% if serial_enabled %}
  Serial.begin(9600);
  Serial.println("LED Blink Started");
  {% endif %}
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  {% if serial_enabled %}
  Serial.println("LED ON");
  {% endif %}
  delay({{ interval }});
  
  digitalWrite(LED_PIN, LOW);
  {% if serial_enabled %}
  Serial.println("LED OFF");
  {% endif %}
  delay({{ interval }});
}
```

### A.2 DHT22 温湿度模板

```cpp
// DHT22 Temperature & Humidity Monitor
// Generated by Arduino MCP Server

#include <DHT.h>

#define DHTPIN {{ pin }}
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
  Serial.println("DHT22 Monitor Started");
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  
  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.print("%  Temperature: ");
  Serial.print(temperature);
  Serial.println("°C");
  
  delay({{ interval }});
}
```

---

## 附录 B：arduino-cli 命令速查

```bash
# 初始化配置
arduino-cli config init

# 更新板型索引
arduino-cli core update-index

# 安装核心
arduino-cli core install arduino:avr
arduino-cli core install rp2040:rp2040 --additional-urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json

# 列出已安装的核心
arduino-cli core list

# 搜索库
arduino-cli lib search DHT

# 安装库
arduino-cli lib install "DHT sensor library"

# 列出已安装的库
arduino-cli lib list

# 检测开发板
arduino-cli board list

# 创建项目
arduino-cli sketch new MyProject

# 编译
arduino-cli compile --fqbn arduino:avr:uno MyProject/

# 上传
arduino-cli upload -p COM3 --fqbn arduino:avr:uno MyProject/

# 串口监控
arduino-cli monitor -p COM3 -c baudrate=9600
```

---

**文档版本：** 1.1  
**最后更新：** 2026-02-01  
**状态：** ✅ MVP 已实现

---

## 🎉 实现状态更新

### MVP 已完成！

项目位置：`arduino-mcp-server/`

**核心功能：**
- ✅ 自然语言意图解析
- ✅ LED 闪烁代码生成
- ✅ arduino-cli 完整封装
- ✅ 编译、上传、监控一体化
- ✅ 7 个 MCP 工具
- ✅ 完整文档和示例

**快速开始：**
```bash
cd arduino-mcp-server
pip install -e .
python test_basic.py
```

**详细文档：**
- [README.md](../arduino-mcp-server/README.md) - 项目概述
- [QUICKSTART.md](../arduino-mcp-server/QUICKSTART.md) - 5 分钟快速上手
- [USAGE.md](../arduino-mcp-server/USAGE.md) - 详细使用指南
- [IMPLEMENTATION_LOG.md](../arduino-mcp-server/IMPLEMENTATION_LOG.md) - 实现记录

**示例：**
```
用户: "用 Arduino Uno 做一个 LED 闪烁，13 号引脚，每秒闪一次"
系统: 自动生成 → 编译 → 上传 → 完成！
```

---

## 原始设计文档

**文档版本：** 1.0  
**最后更新：** 2026-02-01  
**状态：** 设计阶段 - 待审查
