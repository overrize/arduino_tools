# Arduino Power - Requirements

## 概述

创建一个 Kiro Power，封装 Arduino MCP Server 的功能，提供友好的入口和引导界面。

---

## 用户故事

### 故事 1：发现和启动
**作为** 嵌入式开发者  
**我想要** 在 Kiro 中看到 "Arduino 开发" 的 Power  
**以便** 我能快速开始 Arduino 项目，而不需要记住 MCP server 的工具名称

**验收标准：**
1.1 Power 在 Kiro Powers 列表中可见  
1.2 Power 名称清晰：Arduino 开发 / Arduino Development  
1.3 Power 描述说明功能：自然语言端到端 Arduino 开发  
1.4 Power 关键词包含：arduino, embedded, 嵌入式, led, pico, uno, nano

### 故事 2：CLI 入口
**作为** 用户  
**我想要** 通过命令行用自然语言描述需求  
**以便** 我能快速开始，不需要填写表单

**验收标准：**
2.1 提供 `arduino-dev` 命令行工具  
2.2 显示欢迎界面  
2.3 接收用户的自然语言输入  
2.4 自动打开 Kiro 并传递需求  
2.5 Kiro 自动调用 MCP server 处理

### 故事 3：自然语言交互
**作为** 用户  
**我想要** 用自然语言描述我的需求  
**以便** 我不需要记住命令格式或填写表单

**验收标准：**
3.1 接受自然语言输入（中文或英文）  
3.2 支持多种表达方式  
3.3 理解板型、功能、参数  
3.4 提供输入示例  
3.5 友好的错误提示

### 故事 4：Kiro 自动化
**作为** 用户  
**我想要** CLI 工具自动启动 Kiro 并传递我的需求  
**以便** 我不需要手动操作

**验收标准：**
4.1 CLI 接收自然语言后自动启动 Kiro  
4.2 通过命令行参数或其他方式传递需求给 Kiro  
4.3 Kiro 自动识别并调用 Arduino MCP server  
4.4 用户看到完整的处理过程  
4.5 无需手动复制粘贴

### 故事 5：Power 集成
**作为** Kiro 用户  
**我想要** 直接在 Kiro 中激活 Arduino Power  
**以便** 我能使用自然语言开发 Arduino 项目

**验收标准：**
5.1 Power 包含完整的文档（POWER.md）  
5.2 Power 包含引导文件（steering files）  
5.3 Power 自动发现和使用 Arduino MCP server  
5.4 Power 提供示例对话和命令  
5.5 Power 支持中英文

---

## 功能需求

### F1: CLI 工具
- 命令：`arduino-dev` 或 `arduino-dev.bat`
- 交互式菜单
- 参数收集
- Kiro 集成

### F2: Power 结构
```
arduino-power/
├── POWER.md              # Power 文档
├── steering/
│   ├── getting-started.md    # 入门指南
│   ├── led-projects.md       # LED 项目
│   └── workflow.md           # 工作流程
└── mcp-config.json       # MCP server 配置
```

### F3: 主菜单选项
1. 🆕 新建项目
2. 🔨 编译项目
3. 📤 上传到硬件
4. 📡 监控串口
5. 🎮 Wokwi 仿真
6. ❓ 帮助

### F4: 新建项目流程
```
1. 选择板型
   → Raspberry Pi Pico
   → Arduino Uno
   → Arduino Nano
   → ESP32

2. 选择项目类型
   → LED 闪烁
   → 按钮控制 LED
   → 传感器读取
   → 自定义

3. 配置参数
   → LED 引脚号
   → 闪烁间隔
   → 其他选项

4. 生成项目
   → 调用 Kiro
   → 使用 MCP server
   → 生成代码 + Wokwi
```

### F5: Kiro 命令生成
CLI 工具生成的 Kiro 命令格式：
```
使用 Arduino MCP server 的 full_workflow_led_blink 工具，
用 [板型] 做一个 [项目类型]，[引脚] 号引脚，每 [间隔] 秒闪一次
```

---

## 非功能需求

### NFR1: 易用性
- 清晰的提示和说明
- 中英文支持
- 错误提示友好
- 提供示例

### NFR2: 可扩展性
- 支持添加新板型
- 支持添加新项目类型
- 支持自定义模板

### NFR3: 可靠性
- 检查依赖（arduino-cli, Python, MCP server）
- 错误处理和恢复
- 提供故障排查指南

### NFR4: 性能
- CLI 启动快速（< 1秒）
- Kiro 集成流畅
- 代码生成快速

---

## 技术约束

### TC1: 依赖
- Python 3.8+
- Kiro IDE
- Arduino MCP Server
- arduino-cli

### TC2: 平台
- Windows (主要)
- 支持 PowerShell 和 CMD

### TC3: 集成
- 使用 Kiro Powers 机制
- 使用 MCP protocol
- 兼容现有 Arduino MCP Server

---

## 优先级

### P0 (必须有)
- CLI 工具基本功能
- Power 基本结构
- 新建 LED 项目
- Kiro 集成

### P1 (应该有)
- 完整的菜单系统
- 多种板型支持
- Wokwi 集成提示
- 中英文支持

### P2 (可以有)
- 项目管理（列表、删除）
- 配置保存和加载
- 模板自定义
- Web 界面

---

## 成功指标

### 用户体验
- ✅ 用户无需记住 MCP tool 名称
- ✅ 从启动到生成代码 < 1 分钟
- ✅ 清晰的步骤和提示
- ✅ 新手能独立完成

### 技术指标
- ✅ CLI 启动时间 < 1 秒
- ✅ Kiro 命令生成准确率 100%
- ✅ MCP server 调用成功率 > 95%
- ✅ 代码生成成功率 > 95%

---

## 示例对话

### 场景 1：CLI 启动
```
> arduino-dev

🎯 Arduino 开发助手
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

欢迎使用 Arduino 自然语言开发工具！

请描述你想做什么（或输入 'help' 查看示例）：
> 用 Pico 做一个 LED 闪烁，25 号引脚，每 2 秒闪一次

✅ 理解了你的需求！
   板型: Raspberry Pi Pico
   功能: LED 闪烁
   引脚: 25
   间隔: 2 秒

⏳ 正在启动 Kiro...
✅ Kiro 已启动，正在处理你的需求...

💡 Kiro 将自动：
   1. 生成 Arduino 代码
   2. 生成 Wokwi 仿真文件
   3. 编译代码
   4. 提供上传选项
```

### 场景 2：简单输入
```
> arduino-dev "用 Uno 做一个 LED 闪烁"

✅ 理解了你的需求！
   板型: Arduino Uno
   功能: LED 闪烁
   引脚: 13 (默认)
   间隔: 1 秒 (默认)

⏳ 正在启动 Kiro...
✅ Kiro 已启动，正在处理你的需求...
```

### 场景 3：Kiro 中使用 Power
```
用户: "我想做一个 LED 闪烁项目"

Kiro (检测到 Arduino Power):
  "我看到你想做 Arduino 项目。让我使用 Arduino Power 帮你。
  
  请告诉我：
  1. 使用什么板子？(Pico / Uno / Nano)
  2. LED 接在哪个引脚？
  3. 闪烁间隔是多少秒？"

用户: "Pico，25 号引脚，每 2 秒"

Kiro: "好的，我来帮你创建项目..."
  [调用 Arduino MCP server]
  [生成代码 + Wokwi 文件]
  [显示下一步选项]
```

---

## 下一步

1. 创建 Power 结构和文档
2. 实现 CLI 工具
3. 编写 steering files
4. 测试集成
5. 编写用户文档

---

**优先级**: P0  
**预计工作量**: 2-3 天  
**依赖**: Arduino MCP Server (已完成)
