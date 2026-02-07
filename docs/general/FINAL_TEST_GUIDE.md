# 🎯 最终测试指南 - Arduino CLI V2

## ✅ 准备就绪

所有功能已完成并可测试！

---

## 🚀 快速测试

### 测试 1：命令行参数

```bash
cd arduino-cli
python arduino_dev_v2.py "用 Pico 做一个 LED 闪烁，25 号引脚"
```

**预期结果：**
```
✅ 理解了你的需求！
⏳ 正在启动 Kiro...
✅ Kiro 已启动！
💡 请在 Kiro 中输入：
使用 Arduino MCP server 帮我用 Pico 做一个 LED 闪烁，25 号引脚
✅ 提示已复制到剪贴板
```

### 测试 2：交互式

```bash
arduino-dev-v2.bat

请描述你想做什么：
> 用 Uno 做一个 LED 闪烁
```

### 测试 3：完整流程

1. **运行 CLI 工具**
   ```bash
   arduino-dev-v2.bat "用 Pico 做一个 LED 闪烁，25 号引脚"
   ```

2. **Kiro 自动打开**（使用 `kiro .` 命令）

3. **在 Kiro 中粘贴**（Ctrl+V）
   ```
   使用 Arduino MCP server 帮我用 Pico 做一个 LED 闪烁，25 号引脚
   ```

4. **验证 Kiro 响应**
   - Kiro 应该调用 Arduino MCP Server
   - 生成代码
   - 生成 Wokwi 文件
   - 显示下一步选项

---

## 📋 测试清单

### CLI 工具测试
- [ ] 命令行参数输入正常
- [ ] 交互式输入正常
- [ ] 帮助信息显示正确
- [ ] Kiro 启动成功（`kiro .`）
- [ ] 提示复制到剪贴板

### Kiro 集成测试
- [ ] Kiro 在当前文件夹打开
- [ ] 粘贴提示正常
- [ ] Kiro 识别 Arduino 需求
- [ ] MCP Server 被调用
- [ ] 代码生成成功
- [ ] Wokwi 文件生成

### 端到端测试
- [ ] 从 CLI 输入到代码生成完整流程
- [ ] 自然语言理解正确
- [ ] 板型识别正确
- [ ] 参数解析正确
- [ ] 文件生成位置正确

---

## 💡 测试用例

### 用例 1：Pico LED 基本

**输入：**
```
用 Pico 做一个 LED 闪烁，25 号引脚
```

**预期 Kiro 命令：**
```
使用 Arduino MCP server 帮我用 Pico 做一个 LED 闪烁，25 号引脚
```

**预期结果：**
- 板型：Raspberry Pi Pico
- 引脚：25
- 间隔：1 秒（默认）

### 用例 2：Uno LED 带间隔

**输入：**
```
用 Uno 做一个 LED 闪烁，13 号引脚，每 2 秒闪一次
```

**预期 Kiro 命令：**
```
使用 Arduino MCP server 帮我用 Uno 做一个 LED 闪烁，13 号引脚，每 2 秒闪一次
```

**预期结果：**
- 板型：Arduino Uno
- 引脚：13
- 间隔：2 秒

### 用例 3：简化输入

**输入：**
```
用 Nano 做一个 LED 闪烁
```

**预期 Kiro 命令：**
```
使用 Arduino MCP server 帮我用 Nano 做一个 LED 闪烁
```

**预期结果：**
- 板型：Arduino Nano
- 引脚：13（默认）
- 间隔：1 秒（默认）

---

## 🎯 成功标准

### CLI 工具
- ✅ 接收自然语言输入
- ✅ 使用 `kiro .` 打开当前文件夹
- ✅ 生成正确的提示
- ✅ 复制到剪贴板
- ✅ 友好的输出

### Kiro 集成
- ✅ 在当前文件夹打开
- ✅ 接收粘贴的提示
- ✅ 调用 MCP Server
- ✅ 生成代码和文件

### 用户体验
- ✅ 一句话启动
- ✅ 无需填表单
- ✅ 自动化流程
- ✅ 清晰的提示

---

## 🐛 故障排查

### 问题 1：Kiro 未启动

**检查：**
```bash
kiro --version
```

**解决：**
- 确保 Kiro 在 PATH 中
- 或手动运行 `kiro .`

### 问题 2：剪贴板不工作

**解决：**
- 手动复制显示的提示
- 或安装 pyperclip：`pip install pyperclip`

### 问题 3：MCP Server 未调用

**检查：**
- MCP Server 配置：`.kiro/settings/mcp.json`
- 提示格式是否正确
- Kiro 是否识别 "Arduino MCP server"

---

## 📊 完整流程图

```
用户
  ↓
输入自然语言
  ↓
CLI 工具（arduino_dev_v2.py）
  ↓
生成提示："使用 Arduino MCP server 帮我..."
  ↓
复制到剪贴板
  ↓
启动 Kiro（kiro .）
  ↓
用户在 Kiro 中粘贴
  ↓
Kiro 识别 Arduino 需求
  ↓
调用 Arduino MCP Server
  ↓
MCP Server 处理
  ↓
生成代码 + Wokwi 文件
  ↓
完成！
```

---

## 🎉 测试完成后

### 如果成功
- ✅ CLI 工具可用
- ✅ Kiro 集成正常
- ✅ MCP Server 工作
- ✅ 代码生成成功

### 下一步
1. 收集用户反馈
2. 优化自然语言理解
3. 添加更多功能
4. 创建 Kiro Power

---

## 📚 相关文档

- [CLI V2 README](arduino-cli/README_V2.md)
- [CLI V2 完成报告](CLI_V2_COMPLETE.md)
- [Arduino MCP Server](arduino-mcp-server/)
- [Wokwi 仿真](arduino-mcp-server/WOKWI_SIMULATION.md)

---

## 🚀 立即开始

```bash
cd arduino-cli
arduino-dev-v2.bat "用 Pico 做一个 LED 闪烁，25 号引脚"
```

然后在 Kiro 中粘贴（Ctrl+V）！

---

**测试版本**: 2.0  
**状态**: ✅ 准备测试  
**日期**: 2026-02-01
