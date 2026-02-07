# Arduino Client 开发经验与改动记录

> 后续改动请追加到本文档，作为项目经验沉淀。

## 变更记录

### 2026-02-12 从 MCP Server 重构为独立 Client 工具

**问题**：
- 原项目依赖 kiro 的 MCP server，使用受限
- 代码生成使用模板驱动，灵活性不足
- 无法作为独立工具使用

**改动**：
1. **架构重构**：从 MCP Server 改为独立 Client 工具（参考 STloop）
2. **代码生成**：从模板驱动改为 LLM API（OpenAI/Kimi）
3. **模块拆分**：
   - `arduino_cli.py` → `builder.py` + `uploader.py` + `board_detector.py` + `monitor.py`
   - `code_generator.py` → 使用 LLM API 生成代码
4. **API 设计**：提供 `ArduinoClient` 可编程 API，类似 `STLoopClient`
5. **CLI 接口**：提供命令行工具，支持 gen、build、upload、detect、demo 等命令

**原则**：
- 保持与 STloop 一致的架构风格
- 功能与业务解耦
- 支持可编程 API 和 CLI 两种使用方式

### 2026-02-12 代码生成从模板改为 LLM API

**问题**：
- 模板驱动代码生成灵活性不足
- 无法处理复杂需求
- 需要维护大量模板

**改动**：
- 使用 OpenAI/Kimi 等 LLM API 生成代码
- 参考 STloop 的 `llm_client.py` 实现
- 支持编译错误自动修复（最多 3 轮）

**优势**：
- 更灵活，可处理各种需求
- 无需维护模板
- 支持自然语言交互

### 2026-02-12 模块化设计

**原则**：
- 单一职责：每个模块只负责一个功能
- 依赖注入：通过构造函数注入依赖，便于测试
- 错误处理：统一的异常层次

**模块划分**：
- `board_detector.py` - 板卡检测
- `builder.py` - 编译
- `uploader.py` - 上传
- `monitor.py` - 串口监控
- `code_generator.py` - 代码生成（LLM）
- `port_manager.py` - 串口管理

## 注意事项

1. **arduino-cli 依赖**：需要先安装 arduino-cli
2. **LLM 配置**：需要配置 API Key（.env 或环境变量）
3. **串口占用**：上传前会自动关闭占用串口的进程
4. **板卡检测**：支持自动检测和按类型检测

## 未来改进

1. **交互式终端**：类似 STloop 的 `chat.py`
2. **更多 Demo**：按钮控制、传感器等
3. **Wokwi 集成**：生成 Wokwi 仿真文件
4. **库管理**：自动安装所需库
