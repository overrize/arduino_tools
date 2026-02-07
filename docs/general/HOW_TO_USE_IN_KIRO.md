# 🎯 如何在 Kiro 中使用 Arduino MCP Server

## ⚠️ 重要：MCP Server 需要明确调用

Kiro 不会自动使用 MCP server，需要明确提示。

---

## ✅ 正确的使用方式

### 方法 1：明确要求使用 MCP tools

```
请使用 Arduino MCP server 帮我用 Pico 做一个 LED 闪烁，25 号引脚
```

或

```
调用 full_workflow_led_blink 工具，用 Pico 做一个 LED 闪烁，25 号引脚
```

### 方法 2：先检查 MCP server 状态

```
检查 Arduino MCP server 是否可用
```

然后：

```
用 Arduino MCP server 创建 LED 闪烁项目
```

### 方法 3：列出可用的 MCP tools

```
列出 Arduino MCP server 的所有工具
```

---

## 🔍 检查 MCP Server 连接状态

### 步骤 1：查看 MCP Server 面板

1. 在 Kiro 中打开侧边栏
2. 找到 "MCP Servers" 面板
3. 查看 "arduino" server 状态
4. 应该显示为 "Connected" 或 "Running"

### 步骤 2：如果未连接

1. 点击 "arduino" server 旁边的刷新按钮
2. 或者重启 Kiro
3. 检查 `.kiro/settings/mcp.json` 配置

---

## 📋 MCP Server 配置检查

### 当前配置位置
```
.kiro/settings/mcp.json
```

### 配置内容应该是：
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

## 🎮 可用的 MCP Tools

### 1. check_arduino_cli
检查 arduino-cli 是否安装

```
使用 check_arduino_cli 工具
```

### 2. detect_boards
检测连接的 Arduino 板子

```
使用 detect_boards 工具
```

### 3. create_led_blink
创建 LED 闪烁项目（带 Wokwi）

```
使用 create_led_blink 工具，用 Pico 做一个 LED 闪烁，25 号引脚
```

### 4. full_workflow_led_blink
完整工作流（推荐）

```
使用 full_workflow_led_blink 工具，用 Pico 做一个 LED 闪烁，25 号引脚
```

### 5. compile_sketch
编译 Arduino 代码

```
使用 compile_sketch 工具编译 ./arduino_projects/led_blink
```

### 6. upload_sketch
上传到硬件

```
使用 upload_sketch 工具上传 ./arduino_projects/led_blink
```

### 7. monitor_serial
监控串口输出

```
使用 monitor_serial 工具监控 COM3 端口
```

---

## 🚀 推荐的完整测试流程

### 步骤 1：检查 MCP server
```
检查 Arduino MCP server 的状态
```

### 步骤 2：检查 arduino-cli
```
使用 check_arduino_cli 工具
```

### 步骤 3：检测板子
```
使用 detect_boards 工具
```

### 步骤 4：创建项目（完整工作流）
```
使用 full_workflow_led_blink 工具，用 Pico 做一个 LED 闪烁，25 号引脚
```

---

## ❌ 错误的使用方式

### ❌ 不要这样说：
```
帮我用 Pico 做一个 LED 闪烁，25 号引脚
```

**问题**：Kiro 会直接生成代码，不会调用 MCP server

### ✅ 应该这样说：
```
使用 Arduino MCP server 帮我用 Pico 做一个 LED 闪烁，25 号引脚
```

或

```
调用 full_workflow_led_blink 工具，用 Pico 做一个 LED 闪烁，25 号引脚
```

---

## 🔧 故障排查

### 问题 1：MCP server 未连接

**症状**：Kiro 直接生成代码，不调用 MCP tools

**解决**：
1. 检查 MCP Server 面板状态
2. 点击刷新按钮
3. 检查配置文件路径是否正确
4. 重启 Kiro

### 问题 2：找不到 arduino_mcp_server 模块

**症状**：MCP server 启动失败

**解决**：
```powershell
cd arduino-mcp-server
pip install -e .
```

### 问题 3：Python 路径错误

**症状**：MCP server 无法启动

**解决**：
检查 `cwd` 和 `PYTHONPATH` 是否指向正确的目录：
```
E:\embedd_tools\arduino_tools\arduino-mcp-server\src
```

---

## 📊 验证 MCP Server 工作

### 测试命令：
```
使用 Arduino MCP server 的 check_arduino_cli 工具
```

### 预期输出：
```
✅ arduino-cli is installed and ready
```

### 如果看到这个输出，说明：
- ✅ MCP server 已连接
- ✅ 工具可以正常调用
- ✅ 可以继续使用其他工具

---

## 🎯 完整示例对话

### 用户：
```
使用 Arduino MCP server 的 full_workflow_led_blink 工具，
用 Pico 做一个 LED 闪烁，25 号引脚
```

### 预期 Kiro 响应：
```
🚀 Starting full LED blink workflow...

Step 1: Parsing intent and generating code...
✅ Code generated at: ./arduino_projects/led_blink
   📌 Board: arduino:mbed_rp2040:pico
   📍 LED Pin: 25
   ⏱️  Interval: 1000ms

🎮 Wokwi Simulation Files Generated:
   • diagram.json (circuit diagram)
   • wokwi.toml (configuration)

📋 下一步选择：
   1. [在 Wokwi 中仿真] - 先测试代码和接线
   2. [直接上传到硬件] - 如果已经接好线

💡 推荐：先在 Wokwi 中仿真，确认接线正确后再上传硬件！

Step 2: Compiling...
✅ Compilation successful
...
```

---

## 💡 关键点

1. **必须明确提到 "MCP server" 或 "工具名称"**
2. **检查 MCP Server 面板确认连接状态**
3. **使用 `check_arduino_cli` 验证 MCP server 工作**
4. **然后使用 `full_workflow_led_blink` 完整工作流**

---

## ✅ 快速测试命令

复制粘贴到 Kiro：

```
使用 Arduino MCP server 的 full_workflow_led_blink 工具，用 Pico 做一个 LED 闪烁，25 号引脚
```

或者分步骤：

```
1. 使用 check_arduino_cli 工具
2. 使用 detect_boards 工具
3. 使用 full_workflow_led_blink 工具，用 Pico 做一个 LED 闪烁，25 号引脚
```

---

**关键**：必须明确告诉 Kiro 使用 MCP server 或具体的工具名称！
