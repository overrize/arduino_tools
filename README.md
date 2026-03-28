# Arduino Tools

> 自然语言驱动的 Arduino 端到端开发工具 — 从想法到闪烁的 LED，只需要一句话

## 工作流程

```
描述需求 → 自动检测板卡 → AI 生成代码 → 编译 → 烧录/仿真 → 串口验证
```

启动后进入端到端线性流程：用户只需描述需求，其余全部自动完成。
如果没有检测到物理板卡，自动切换到 Wokwi 仿真。

## 三个版本

| 功能 | CLI (Python) | Desktop (Tauri) | Web (React) |
|------|:---:|:---:|:---:|
| 自然语言输入 | ✅ | ✅ | ✅ |
| AI 代码生成 | ✅ | ✅ | ✅ |
| 本地编译 | ✅ | ✅ | — |
| 板卡烧录 | ✅ | ✅ | — |
| 串口监控 | ✅ | ✅ | — |
| Wokwi 仿真 | ✅ | ✅ | — |
| ZIP 导出 | — | ✅ | ✅ |
| 安装要求 | Python 3.9+ | 可执行文件 | 浏览器 |

## 快速开始

### CLI 工具（推荐）

```bash
# 安装
pip install -e arduino-client/[ui]

# 启动端到端流程
arduino-client
# 或
python -m arduino_client
```

启动后自动显示 splash → 检查 LLM 配置 → 等待用户描述需求 → 自动完成全流程。

### CLI 子命令

```bash
arduino-client                  # 端到端交互模式（默认）
arduino-client setup             # 配置 LLM API
arduino-client gen "需求" name   # 单次生成代码
arduino-client run "需求"        # 端到端自动化（非交互）
arduino-client build <sketch>    # 编译
arduino-client upload <sketch>   # 烧录
arduino-client detect            # 检测板卡
arduino-client monitor           # 串口监视器
arduino-client catalog           # 浏览板卡数据库
arduino-client check             # 环境检查
arduino-client sim <sketch>      # Wokwi 仿真
arduino-client demo              # LED 闪烁演示
```

### 桌面应用

```bash
cd arduino-desktop
npm install
npm run tauri:dev      # 开发模式
npm run tauri:build    # 构建安装包
```

也可以使用项目根目录的构建脚本：

```bash
build-desktop.bat dev      # 启动开发模式
build-desktop.bat build    # 构建发布版本
```

#### 发布产物

`npm run tauri:build` 会在 `arduino-desktop/src-tauri/target/release/bundle/` 下生成平台对应的安装包：

| 平台 | 产物路径 | 格式 |
|------|----------|------|
| Windows | `bundle/msi/*.msi` | MSI 安装包 |
| Windows | `bundle/nsis/*.exe` | NSIS 安装程序 |
| macOS | `bundle/dmg/*.dmg` | DMG 镜像 |
| macOS | `bundle/macos/*.app` | App Bundle |
| Linux | `bundle/deb/*.deb` | Debian 包 |
| Linux | `bundle/appimage/*.AppImage` | AppImage |

独立可执行文件：`arduino-desktop/src-tauri/target/release/arduino-desktop(.exe)`

#### Wokwi 仿真

桌面版内置 Wokwi 仿真支持，未检测到物理板卡时自动切换：

- 首次使用自动安装 `wokwi-cli`（通过官方安装脚本）
- 自动生成 `wokwi.toml` 和 `diagram.json` 配置文件
- 需在设置中配置 Wokwi Token（从 https://wokwi.com/dashboard/ci 获取）
- 支持板卡：Arduino Uno / Nano / Mega、Raspberry Pi Pico、ESP32

> **注意**：当前 CI 只包含 Client 和 MCP Server 的测试，桌面端尚未配置自动构建/发布流水线。如需跨平台构建，需在对应平台上分别执行 `npm run tauri:build`。

### Web 版本

```bash
cd arduino-web
npm install
npm run dev            # 开发模式
npm run build          # 构建静态站点
```

## 项目结构

```
arduino_tools/
├── arduino-client/          # CLI 工具 (Python + Rich)
│   ├── arduino_client/
│   │   ├── ui/              # Rich UI 组件（主题、面板、进度条）
│   │   ├── cli_rich.py      # Rich CLI 入口（12 个子命令）
│   │   ├── interactive_rich.py  # 端到端交互流程
│   │   ├── client.py        # ArduinoClient 核心 API
│   │   ├── code_generator.py    # LLM 代码生成
│   │   ├── builder.py       # arduino-cli 编译封装
│   │   ├── board_detector.py    # 板卡自动检测
│   │   └── setup.py         # 配置向导
│   └── pyproject.toml
│
├── arduino-desktop/         # 桌面应用 (Tauri + React)
│   ├── src/                 # React 前端
│   └── src-tauri/           # Rust 后端
│
├── arduino-web/             # Web 版本 (React + Vite)
│   └── src/
│
├── arduino-mcp-server/      # MCP Server（Kiro 集成，早期版本）
├── build-desktop.bat        # 桌面版构建脚本
└── build-web.bat            # Web 版构建脚本
```

## 系统要求

### CLI
- Python 3.9+
- arduino-cli
- LLM API Key（Kimi / OpenAI / 兼容 API）
- 可选：`pip install -e arduino-client/[ui]` 安装 Rich 终端 UI

### Desktop 额外要求
- Node.js 18+
- Rust + Cargo

### Web
- 现代浏览器
- LLM API Key

## 技术栈

| 层级 | 技术 |
|------|------|
| CLI | Python + Rich + pyserial |
| CLI UI | Arduino 品牌主题 (teal #00979D) |
| Desktop | Tauri + React + TypeScript |
| Web | React + Vite + TypeScript |
| 编译工具 | arduino-cli |
| 仿真 | wokwi-cli |
| LLM | OpenAI 兼容 API |

## 设计原则

- **端到端线性流程**：不使用菜单，用户只需描述需求
- **自动化优先**：板卡检测、编译、烧录、验证全部自动
- **无板自动仿真**：未检测到板卡时自动切换 Wokwi
- **自动修复**：编译失败自动 LLM 重新生成（最多 3 轮）
- **串口验证**：烧录后自动捕获串口输出，LLM 诊断异常
- **Rich 可选**：所有 Rich UI 为可选依赖，纯文本 fallback 始终可用
- **与 STLoop 对齐**：同一产品线，交互体验保持一致

## 许可证

MIT
