# Arduino MCP Server - 配置指南

## 稳定性问题解决方案

### 问题 1: 工作目录配置

**症状**: 项目生成在错误的位置，或者路径找不到

**原因**: MCP server 的 `cwd` (工作目录) 配置不正确

**解决方案**: 

在 Kiro 的 MCP 配置中（`.kiro/settings/mcp.json` 或工作区配置），确保 `cwd` 设置为**项目根目录**，而不是 `src` 目录：

```json
{
  "mcpServers": {
    "arduino": {
      "command": "python",
      "args": ["-m", "arduino_mcp_server"],
      "cwd": "E:\\embedd_tools\\arduino_tools",  // ✅ 项目根目录
      "env": {
        "PYTHONPATH": "E:\\embedd_tools\\arduino_tools\\arduino-mcp-server\\src"
      }
    }
  }
}
```

**错误配置示例**:
```json
"cwd": "E:\\embedd_tools\\arduino_tools\\arduino-mcp-server\\src"  // ❌ 错误
```

### 问题 2: 库依赖缺失

**症状**: 编译时报错 `Library 'XXX@latest' not found`

**原因**: 项目需要的库没有安装

**解决方案**:

1. **自动安装** (推荐):
   ```python
   # 在代码中自动检测并安装
   cli = ArduinoCLI()
   cli.install_library("TM1637Display")
   ```

2. **手动安装**:
   ```bash
   arduino-cli lib install TM1637Display
   ```

3. **搜索库**:
   ```bash
   arduino-cli lib search TM1637
   ```

### 问题 3: MCP Server 未重启

**症状**: 代码修改后没有生效

**原因**: MCP server 还在使用旧代码

**解决方案**:

1. **在 Kiro 中重启**:
   - 打开 MCP Server 面板
   - 找到 `arduino` server
   - 点击重启按钮

2. **命令面板重启**:
   - 按 `F1` 或 `Ctrl+Shift+P`
   - 输入 "MCP: Restart Server"
   - 选择 `arduino`

3. **完全重启 Kiro**:
   - 关闭 Kiro
   - 重新打开

## 正确的项目结构

生成的项目应该有以下结构：

```
arduino_projects/
└── {project_name}/
    ├── {project_name}.ino       # Arduino 源代码
    ├── docs/                     # 项目文档
    │   ├── README.md            # 项目说明
    │   ├── requirements.md      # 需求文档（可选）
    │   └── schematic.png        # 原理图（可选）
    ├── simulation/               # Wokwi 仿真
    │   ├── diagram.json         # 电路图
    │   └── wokwi.toml           # 配置文件
    └── build/                    # 编译输出
        └── {project_name}.ino.hex  # 固件文件
```

## 验证配置

运行稳定性测试脚本：

```bash
cd arduino-mcp-server
python test_stability.py
```

应该看到：

```
✅ All tests passed!
```

## 常见问题

### Q1: 为什么 wokwi.toml 没有生成？

**A**: 检查以下几点：
1. MCP server 是否已重启
2. `include_wokwi=True` 是否传递
3. 工作目录配置是否正确

### Q2: 编译产物在哪里？

**A**: 编译产物在 `{project_dir}/build/` 目录中：
- AVR (Uno/Nano): `.hex` 文件
- Pico: `.uf2` 文件
- ESP32: `.bin` 文件

### Q3: Wokwi 仿真找不到固件？

**A**: 检查 `simulation/wokwi.toml` 中的路径：
```toml
[wokwi]
version = 1
firmware = '../build/{project_name}.ino.hex'  # 相对路径
```

### Q4: 如何添加库依赖？

**A**: 在项目代码中添加：
```cpp
#include <TM1637Display.h>
```

然后在编译前安装库：
```bash
arduino-cli lib install TM1637Display
```

## 自动批准的工具

为了提高效率，建议在 MCP 配置中添加自动批准：

```json
{
  "autoApprove": [
    "check_arduino_cli",
    "detect_boards",
    "create_led_blink",
    "compile_sketch"
  ]
}
```

## 性能优化

1. **使用本地 arduino-cli**: 确保 arduino-cli 在 PATH 中
2. **预安装常用库**: 提前安装常用库避免每次编译时安装
3. **缓存编译产物**: build 目录会缓存编译结果

## 故障排查

如果遇到问题，按以下顺序检查：

1. ✅ arduino-cli 是否安装并在 PATH 中
2. ✅ MCP server 配置的 `cwd` 是否正确
3. ✅ MCP server 是否已重启
4. ✅ 项目结构是否完整
5. ✅ 所需库是否已安装
6. ✅ 编译产物是否生成

运行测试脚本可以快速诊断问题：
```bash
python test_stability.py
```
