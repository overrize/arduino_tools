# Arduino Tools 项目优化路线图

> 记录项目可优化点及实施建议，供后续迭代参考。  
> 创建日期：2026-02-07

---

## 1. 意图解析优化（高优先级）

### 现状

`parse_led_blink_intent` 使用简单正则表达式提取用户意图，覆盖场景有限。

### 问题

- 只匹配少量表达，如 `"13 号引脚"`、`"pin 13"`，对 `"引脚 13"`、`"13号"` 等变体支持不足
- 仅支持秒级间隔（`"每 2 秒"`），不支持毫秒、`"ms"` 等表达
- 未处理多板型歧义（如 "uno 或 pico"）
- README 提到 ESP32，但 `parse_led_blink_intent` 未解析

### 建议

- 扩展正则/规则，覆盖更多中英文表达
- 增加输入校验和默认值边界检查
- 规划 Phase 3 时引入 LLM 辅助意图解析，作为 fallback

---

## 2. 日志系统（高优先级）

### 现状

项目大量使用 `print()` 输出，混入 MCP 协议 stdio 通信。

涉及文件：
- `code_generator.py`：代码生成、Wokwi 文件生成
- `server.py`：编译进度
- `arduino_cli.py`：安装检查、板卡检测、库安装
- `port_manager.py`：串口准备、进程关闭

### 问题

- MCP Server 的 stdout 用于 JSON-RPC 协议，`print` 会污染输出
- 无统一日志级别，难以区分 info/warning/error
- 生产环境无法按需关闭或重定向

### 建议

- 统一使用 `logging` 模块，输出到 stderr
- 按 `DEBUG` / `INFO` / `WARNING` / `ERROR` 分级
- 在 MCP 主入口配置 `basicConfig`，支持环境变量控制日志级别

---

## 3. 全局单例与依赖注入（中优先级）

### 现状

`server.py` 在模块级创建全局实例：

```python
app = Server("arduino-mcp-server")
arduino_cli = ArduinoCLI()
```

### 问题

- 不利于单元测试和 mock
- `ArduinoCLI()` 在导入时执行 `check_installation()` 并打印，启动即执行

### 建议

- 将 `arduino_cli` 改为惰性初始化或依赖注入
- 把初始化/检查逻辑封装为可配置、可 mock 的函数

---

## 4. 代码重复（中优先级）

### 现状

`create_led_blink` 和 `full_workflow_led_blink` 存在大量重复逻辑：

- 相同的意图解析
- 相同的代码生成流程
- 相同的 Wokwi 使用说明

### 建议

- 抽取公共函数：`_parse_and_generate_led_blink(user_input, project_name, output_dir)`
- 抽取 `_format_wokwi_instructions()` 统一 Wokwi 说明
- 两个 tool 只负责组合步骤和返回格式

---

## 5. 硬编码路径（中优先级）

### 现状

`arduino_cli.py` 中硬编码 Windows 路径：

```python
possible_paths = [
    "arduino-cli",
    "F:\\Arduino\\arduino-cli.exe",  # 特定用户安装路径
    os.path.expandvars("%LOCALAPPDATA%\\Arduino15\\arduino-cli.exe"),
    "C:\\Program Files\\Arduino CLI\\arduino-cli.exe",
]
```

### 问题

- 含特定用户路径（`F:\Arduino`），不利于通用部署
- 跨平台性差

### 建议

- 支持环境变量 `ARDUINO_CLI_PATH` 指定路径
- 默认只依赖 PATH 中的 `arduino-cli`，再按平台扩展常见路径

---

## 6. 串口管理策略（中优先级）

### 现状

`PortManager.close_port_users()` 会 `terminate()` / `kill()` 占用串口的进程。

### 问题

- 可能关闭 Arduino IDE、串口监视器等，影响用户工作流
- 无白名单或保护机制

### 建议

- 增加可配置的白名单/黑名单（如允许关闭的进程列表）
- 关闭前给出明确提示或二次确认
- 提供「仅尝试打开串口、不杀进程」的选项

---

## 7. 板卡检测性能（中优先级）

### 现状

`detect_board_by_type` 每次调用都会执行 `detect_boards()`，在 `full_workflow` 中可能多次检测。

### 建议

- 在 `full_workflow` 中缓存一次 `detect_boards` 结果并复用
- 为 `detect_board_by_type` 增加可选参数：传入已检测结果，避免重复调用

---

## 8. 错误处理与健壮性（中优先级）

### 现状

部分 `subprocess.run` 只捕获通用 `Exception`，错误信息不够明确。

### 问题

- 用户难以判断是超时、路径错误还是权限问题
- 生产环境 `traceback.print_exc()` 输出到 stdout，可能干扰 MCP 协议

### 建议

- 区分 `FileNotFoundError`、`TimeoutError`、`subprocess.SubprocessError` 等
- 对用户返回简洁、可操作的错误提示
- 详细 traceback 仅在 logger `DEBUG` 级别输出

---

## 9. CLI 工具功能（中优先级）

### 现状

`arduino-cli` 主要生成 Kiro 命令，编译、上传、串口监控仍为「即将推出」。

### 建议

- 直接复用 `arduino-mcp-server` 的 `ArduinoCLI` 逻辑
- 实现本地编译、上传、串口监控
- 或通过子进程调用 MCP server 的工具，保持 CLI 与 MCP 行为一致

---

## 10. 其他可改进点

| 方面 | 现状 | 建议 |
|------|------|------|
| 模板缓存 | 每次 `generate_led_blink` 新建 Jinja2 `Template` | 在模块级或单例中缓存模板对象 |
| 测试 | 测试文件在 `test_src/` 分散 | 使用 pytest 统一组织，并加入 CI |
| 类型注解 | 部分函数缺少完整类型注解 | 补充参数和返回值类型 |
| 配置 | 输出目录、超时等写死在代码中 | 抽到配置文件或环境变量 |
| `create_led_blink` 编译 | 每次创建项目都会编译 | 增加 `skip_compile` 参数，支持「只生成不编译」以加快迭代 |

---

## 建议实施顺序

1. **日志系统**：替换 `print` 为 `logging`，保证 MCP 通信不受干扰
2. **意图解析**：扩展正则和规则，提升鲁棒性
3. **去除重复**：抽取公共逻辑，精简 `create_led_blink` / `full_workflow`
4. **串口管理**：增加白名单和更谨慎的关闭策略
5. **配置与路径**：从环境变量/配置文件读取 arduino-cli 路径和输出目录

---

## 附录：涉及文件一览

| 模块 | 文件 | 主要优化点 |
|------|------|-----------|
| MCP Server | `server.py` | 日志、依赖注入、代码重复、意图解析 |
| Arduino CLI | `arduino_cli.py` | 日志、硬编码路径、错误处理 |
| 代码生成 | `code_generator.py` | 日志、模板缓存 |
| 串口管理 | `port_manager.py` | 日志、关闭策略、白名单 |
| 数据模型 | `models.py` | 类型注解、校验 |
| CLI 工具 | `arduino-cli/*.py` | 编译/上传/监控功能 |

---

**文档版本**：1.0  
**最后更新**：2026-02-07
