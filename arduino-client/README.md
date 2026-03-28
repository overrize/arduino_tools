# Arduino Client — 自然语言驱动的嵌入式端到端开发工具

**一句话描述需求 → 自动生成代码 → 编译 → 烧录 → 串口调试 → 自动修复**，全程无需手动干预。

## 工作流总览

```
用户描述需求（自然语言）
        │
        ▼
┌───────────────────────────────────────────────┐
│  1. 检测板卡（自动识别 FQBN + 串口）            │
│  2. LLM 生成代码（零依赖优先，bare-metal 实现）  │
│  3. 编译（失败则自动修复，最多 3 轮）            │
│  4. 烧录（有板卡）/ Wokwi 仿真（无板卡）        │
│  5. 串口采集 + 用户验证                         │
│  6. 有问题？→ LLM 诊断 → 修复 → 回到步骤 3     │
└───────────────────────────────────────────────┘
        │
        ▼
   功能验证通过 ✓
```

### 关键特性

| 特性 | 说明 |
|------|------|
| **端到端流水线** | 自然语言 → 编译烧录，一条龙自动化 |
| **零依赖优先** | 代码不依赖第三方库（U8g2、Adafruit 等），直接操作硬件寄存器 |
| **编译自动修复** | 编译失败时 LLM 自动修正代码，缺库自动安装，最多 3 轮 |
| **串口调试闭环** | 烧录后采集串口 → 用户反馈问题 → LLM 诊断修复 → 重新上传，最多 5 轮 |
| **项目复用** | 已有项目自动审查是否满足新需求，按需修改而非重写 |
| **无板卡仿真** | 未检测到板卡时自动走 Wokwi 仿真 |

## 前置条件

### 必需

| 工具 | 版本 | 用途 | 安装方式 |
|------|------|------|---------|
| **Python** | 3.10+ | 运行本工具 | [python.org](https://www.python.org/) |
| **LLM API Key** | — | 代码生成/修复/调试 | 支持 OpenAI、Kimi(Moonshot) 等兼容 API |

### 可选（首次运行时会引导安装）

| 工具 | 用途 | 安装方式 |
|------|------|---------|
| **arduino-cli** | 编译、上传固件 | 工具内自动引导安装 |
| **wokwi-cli** | 无板卡仿真 | [安装指南](https://docs.wokwi.com/wokwi-ci/cli-installation) + [获取 token](https://wokwi.com/dashboard/ci) |
| **rich** | 美化终端 UI | `pip install arduino-client[ui]` |

## 快速开始

```bash
# 1. 安装
pip install -e arduino-client/

# 2. 启动交互式终端
python -m arduino_client
# 或 arduino-client

# 3. 菜单选 1 配置 LLM API（首次）
# 4. 菜单选 2 开始开发！
```

### 大模型配置

在 `.env` 文件中配置（或通过菜单选项 1 交互式配置）：

**Kimi K2（推荐）**：
```bash
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.moonshot.cn/v1
OPENAI_MODEL=kimi-k2-0905-preview
```

**OpenAI**：
```bash
OPENAI_API_KEY=sk-xxx
```

支持任意兼容 OpenAI 格式的 API。

## 交互式终端菜单

```
┌──────────────────────────────────────────┐
│  Arduino Client v0.1.0 — 交互式终端       │
│  1. 配置 LLM API                         │
│  2. 生成代码（自然语言 → 自动编译烧录）     │
│  3. 调试（串口诊断 + 自动修复）             │
│  4. Demo: Blink                          │
│  5. 退出                                 │
└──────────────────────────────────────────┘
```

### 选项 2：生成代码（核心流程）

```
输入需求: 用 pico 做一个闹钟，GP10=LED，GP3=按键，GP12=蜂鸣器，GP6/GP7=OLED
项目名称: press_clock

  [检测] 板卡: Raspberry Pi Pico @ COM7
  [自动] 目标 FQBN: arduino:mbed_rp2040:pico
  [生成] 使用模型: kimi-k2-0905-preview
  [生成] 正在调用 API...
  [生成] 收到响应 (3245 字符)
  已生成: arduino_projects/press_clock
  正在编译（arduino:mbed_rp2040:pico）...
  编译成功: arduino_projects/press_clock/build
  烧录成功: COM7

是否采集串口输出进行验证？(Y/n): Y
  [串口] 采集 COM7 @ 115200 baud，等待 8 秒...
─── 串口输出 ───
Pico Alarm Clock Started
I2C scan: found device at 0x3D
OLED initialized
─── 结束 ───

功能是否正常？(正常请按 Enter / 描述问题): OLED没有显示内容
  [调试] 第 1/5 轮诊断...
  [诊断] OLED 控制器可能是 SSD1327 而非 SSD1306，初始化命令不匹配
  [修改] 重写 OLED 驱动为 SSD1327 4-bit 灰度模式
  [修复] 代码已更新，编译中...
  编译成功
  [修复] 上传成功，采集串口中...
```

### 选项 3：独立调试

对已有项目进行串口诊断 + LLM 自动修复循环：

1. 列出已有项目，选择要调试的项目
2. 检测板卡，上传当前代码
3. 采集串口输出
4. 描述问题 → LLM 诊断 → 修复代码 → 重新编译上传
5. 循环直到问题解决

## 完整工作流程图

```
python -m arduino_client
         │
    ┌─────┴─────┐
    │ 菜单选择    │
    └─────┬─────┘
          │
     ┌────┴────┐
     │ 选项 2   │  生成代码
     └────┬────┘
          │
  ┌───────▼───────┐
  │  检测板卡       │ ← arduino-cli board list
  │  确定 FQBN     │
  └───────┬───────┘
          │
  ┌───────▼───────┐     ┌──────────────────┐
  │  项目已存在？   │─Yes→│ LLM 审查代码      │
  └───────┬───────┘     │ 满足需求？→ 跳过   │
          │ No          │ 不满足？→ 修改代码  │
  ┌───────▼───────┐     └──────────────────┘
  │  LLM 生成代码  │ ← 零依赖优先（软件I2C、直接寄存器操作）
  └───────┬───────┘
          │
  ┌───────▼───────┐
  │  编译           │ ← arduino-cli compile
  │  失败？         │
  │  ├─ 缺库 → 自动安装 → 重试
  │  └─ 语法 → LLM 修复 → 重试（最多3轮）
  └───────┬───────┘
          │ 成功
     ┌────┴────┐
     │ 有板卡？ │
     └────┬────┘
     Yes  │  No
     │    └────────────┐
     ▼                 ▼
  ┌──────┐      ┌──────────┐
  │ 烧录  │      │ Wokwi    │
  │ COM7  │      │ 仿真运行  │
  └──┬───┘      └──────────┘
     │
  ┌──▼───────────────┐
  │  串口采集 (8秒)    │
  │  显示输出          │
  └──┬───────────────┘
     │
  ┌──▼───────────────┐
  │  用户验证          │
  │  正常 → 结束 ✓    │
  │  有问题 → 进入调试 │
  └──┬───────────────┘
     │ 有问题
  ┌──▼───────────────────┐
  │  LLM 诊断             │ ← 串口输出 + 问题描述 + 代码 + 硬件信息
  │  输出: 根因 + 修复代码  │
  │  编译 → 上传 → 串口    │
  │  循环（最多 5 轮）      │
  └───────────────────────┘
```

## 核心设计原则：零依赖优先 (Bare-Metal First)

从实际项目调试中总结的教训 — **先让功能跑起来，再优化**：

### 为什么不用第三方库？

| 问题 | 真实案例 |
|------|---------|
| 库与平台不兼容 | U8g2 的 Wire 库在 RP2040 上不支持自定义 I2C 引脚 |
| 驱动 IC 假设错误 | U8g2 假设 SH1107，实际硬件是 SSD1327 |
| 安装失败阻塞编译 | `U8g2lib.h: No such file or directory` |
| 库的黑盒行为难调试 | Wire 库内部状态机导致 I2C 通信静默失败 |

### 正确的实现策略

| 外设 | 做法 | 不做 |
|------|------|------|
| I2C 设备 | 软件 I2C (bit-bang GPIO) | Wire 库 |
| OLED | 直接发控制器命令 + 自带字体 | U8g2 / Adafruit |
| 传感器 | 直接实现协议 | DHT / OneWire 库 |
| 性能敏感 | MCU 寄存器直接操作 | digitalWrite |

## 项目结构

```
arduino-client/
├── arduino_client/
│   ├── interactive.py      # 交互式终端 + 端到端流水线
│   ├── client.py           # ArduinoClient 可编程 API
│   ├── code_generator.py   # LLM 代码生成/修复/审查/诊断
│   ├── builder.py          # 编译（自动缺库安装 + 错误提取）
│   ├── uploader.py         # 上传（自定义 build-path）
│   ├── monitor.py          # 串口采集（Popen + 定时捕获）
│   ├── board_detector.py   # 板卡检测
│   ├── llm_config.py       # LLM 配置动态加载
│   ├── simulation.py       # Wokwi 仿真
│   └── port_manager.py     # 串口管理
├── docs/
│   └── LESSONS.md          # 开发经验
└── pyproject.toml
```

## 可编程 API

```python
from arduino_client import ArduinoClient

client = ArduinoClient(work_dir=".")

# 检测板卡
boards = client.detect_boards()

# 生成代码（LLM 零依赖实现）
project_dir, analysis = client.generate(
    "用 pico 做 LED 闪烁", "blink",
    platform_hint="arduino:mbed_rp2040:pico"
)

# 编译
result = client.build(project_dir, "arduino:mbed_rp2040:pico")

# 上传
upload = client.upload(project_dir, "arduino:mbed_rp2040:pico", port="COM7")
```

## CLI 命令

```bash
# 交互式终端（推荐）
python -m arduino_client

# 检测板卡
python -m arduino_client detect

# 生成 + 编译 + 上传
python -m arduino_client gen "需求描述" 项目名 --build --flash

# 编译
python -m arduino_client build 项目名 --fqbn arduino:avr:uno

# 上传
python -m arduino_client upload 项目名 --fqbn arduino:avr:uno
```

## 当前效果

### 已验证的硬件组合

| 板卡 | 外设 | 状态 |
|------|------|------|
| Raspberry Pi Pico | LED + 按键 + 蜂鸣器 | 完全正常 |
| Raspberry Pi Pico | SSD1327 128x128 OLED (I2C) | 软件 I2C 驱动正常，SIO 寄存器加速 |
| Arduino Uno | LED Blink | 生成/编译/上传正常 |

### 已解决的典型问题

- **编译超时**：mbed_rp2040 首次编译需 ~60s → 超时设为 600s
- **FQBN 推断**：从已连接板卡自动获取，不依赖 LLM 猜测
- **缺库自动安装**：编译错误中检测 `No such file or directory` → 自动 `arduino-cli lib install`
- **Windows 编码**：`subprocess` 输出用 `encoding="utf-8", errors="replace"` 防止 GBK 崩溃
- **串口占用**：简化 port_manager，不再用 pyserial 抢占，交给 arduino-cli 管理
- **OLED 驱动 IC 识别**：通过 0xA5 全亮测试 → RAM 写入测试 → 确定 SSD1327

## 支持板卡

- Arduino Uno / Nano
- Raspberry Pi Pico (mbed_rp2040)
- ESP32
- 其他 arduino-cli 支持的板卡

## 未来方向

### 短期

- [ ] **项目规格文件 (.md)**：每个项目目录下生成 `项目名.md`，记录需求、引脚定义、外设型号，作为后续调试和代码审查的上下文
- [ ] **硬件测试套件**：生成独立的硬件测试 sketch，逐个验证每个外设（I2C 扫描 → OLED 全亮 → 按键响应 → 蜂鸣器发声）
- [ ] **Serial 实时监控**：调试模式下持续显示串口输出，而非定时采集

### 中期

- [ ] **OTA 更新**：通过 WiFi (ESP32) 或 USB 自动推送固件更新
- [ ] **多板卡协同**：支持同时管理多个板卡的编译/上传
- [ ] **外设数据库**：积累已验证的外设驱动代码（如 SSD1327、SSD1306 等），直接复用而非每次让 LLM 重新生成
- [ ] **可视化接线图**：根据代码中的引脚定义自动生成接线示意图

### 长期愿景

- [ ] **闭环自主开发**：用户只需描述最终效果，工具自主完成从选型到调试的全流程
- [ ] **硬件感知 AI**：结合摄像头/传感器反馈，AI 能"看到"硬件实际状态并自主调试
- [ ] **社区驱动的外设生态**：用户验证过的驱动代码自动入库，形成零依赖外设驱动库

## License

MIT
