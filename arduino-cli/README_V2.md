# 🎯 Arduino 开发 CLI 工具 V2 - 自然语言版本

真正的自然语言交互，无需填表单！

## ✨ 核心理念

**用户只需要说出想法，工具自动处理一切。**

---

## 🚀 使用方式

### 方式 1：交互式

```bash
arduino-dev-v2.bat

请描述你想做什么：
> 用 Pico 做一个 LED 闪烁，25 号引脚，每 2 秒闪一次
```

### 方式 2：命令行参数

```bash
arduino-dev-v2.bat "用 Pico 做一个 LED 闪烁，25 号引脚"
```

### 方式 3：直接 Python

```bash
python arduino_dev_v2.py "用 Uno 做一个 LED 闪烁"
```

---

## 💡 示例

### 示例 1：Pico LED 闪烁

```bash
> arduino-dev-v2.bat

🎯 Arduino 开发助手
============================================================

欢迎使用 Arduino 自然语言开发工具！

💡 示例：
  • 用 Pico 做一个 LED 闪烁，25 号引脚
  • 用 Uno 做一个 LED 闪烁，13 号引脚，每 2 秒闪一次
  • 用 Nano 做一个按钮控制 LED
  • 用 ESP32 读取传感器数据

请描述你想做什么（或输入 'help' 查看更多示例）：
> 用 Pico 做一个 LED 闪烁，25 号引脚，每 2 秒闪一次

✅ 理解了你的需求！
⏳ 正在启动 Kiro...

✅ Kiro 已启动！

💡 请在 Kiro 中输入：

使用 Arduino MCP server 帮我用 Pico 做一个 LED 闪烁，25 号引脚，每 2 秒闪一次

或者直接说：

用 Pico 做一个 LED 闪烁，25 号引脚，每 2 秒闪一次

✅ 提示已复制到剪贴板，可以直接粘贴（Ctrl+V）

💡 提示：
  Kiro 将自动调用 Arduino MCP Server
  生成代码、Wokwi 仿真文件，并提供编译上传选项
```

### 示例 2：快速命令

```bash
arduino-dev-v2.bat "用 Uno 做一个 LED 闪烁"

✅ 理解了你的需求！
⏳ 正在启动 Kiro...
✅ Kiro 已启动！
```

---

## 🎯 工作流程

```
用户输入自然语言
  ↓
CLI 工具接收
  ↓
启动 Kiro
  ↓
传递需求给 Kiro（复制到剪贴板）
  ↓
用户在 Kiro 中粘贴
  ↓
Kiro 调用 Arduino MCP Server
  ↓
生成代码 + Wokwi 文件
  ↓
完成！
```

---

## 🔧 技术实现

### CLI 工具职责
1. ✅ 接收自然语言输入
2. ✅ 使用 `kiro .` 命令打开当前文件夹
3. ✅ 生成完整提示
4. ✅ 复制到剪贴板
5. ✅ 提示用户粘贴

### Kiro 启动方式
```bash
kiro .
```
这是 PowerShell 中的标准用法，会在当前文件夹打开 Kiro。

### Kiro 职责
1. ✅ 接收用户输入
2. ✅ 识别 Arduino 需求
3. ✅ 调用 MCP Server
4. ✅ 生成代码和文件

---

## 📋 支持的表达方式

### 基本格式
```
用 [板型] 做一个 [功能]，[参数]
```

### 示例
- `用 Pico 做一个 LED 闪烁，25 号引脚`
- `用 Uno 做一个 LED 闪烁，13 号引脚，每 2 秒闪一次`
- `用 Nano 做一个按钮控制 LED，8 号引脚`
- `用 ESP32 读取传感器数据，2 号引脚`

### 支持的板型
- Pico / Raspberry Pi Pico
- Uno / Arduino Uno
- Nano / Arduino Nano
- ESP32

### 支持的功能
- LED 闪烁
- 按钮控制 LED
- 传感器读取
- 更多功能...

---

## 🆚 对比

### V1 (菜单版本)
```
❌ 选择板型: 1, 2, 3, 4
❌ 选择功能: 1, 2, 3, 4
❌ 输入引脚: 25
❌ 输入间隔: 2
❌ 输入名称: my_project
```

### V2 (自然语言版本)
```
✅ 用 Pico 做一个 LED 闪烁，25 号引脚，每 2 秒闪一次
```

**一句话搞定！**

---

## 🎉 优势

### 1. 自然交互
- ✅ 用自然语言描述
- ✅ 无需记住选项
- ✅ 无需填表单

### 2. 快速启动
- ✅ 一句话启动
- ✅ 命令行参数支持
- ✅ 自动打开 Kiro

### 3. 无缝集成
- ✅ 自动复制到剪贴板
- ✅ Kiro 自动处理
- ✅ MCP Server 自动调用

---

## 📦 安装

### 依赖
```bash
pip install pyperclip  # 可选，用于剪贴板
```

### 使用
```bash
cd arduino-cli
arduino-dev-v2.bat
```

---

## 🔮 未来改进

### Phase 2
- [ ] Kiro 命令行参数支持（直接传递提示）
- [ ] 更智能的自然语言理解
- [ ] 支持更多板型和功能

### Phase 3
- [ ] 完全自动化（无需手动粘贴）
- [ ] 实时反馈
- [ ] 项目管理

---

## 📚 相关文档

- [V1 菜单版本](README.md)
- [设计文档](../.kiro/specs/arduino-power/design.md)
- [Arduino MCP Server](../arduino-mcp-server/)

---

**版本**: 2.0  
**状态**: ✅ 可用  
**理念**: 自然语言，无需表单  
**最后更新**: 2026-02-01
