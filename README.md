# Arduino Tools

> 自然语言驱动的 Arduino 端到端开发工具 — 从想法到闪烁的 LED，只需要一句话

## 工作流程

```
描述需求 → 自动检测板卡 → AI 生成代码 → 编译 → 烧录/仿真 → 串口验证
```

启动后进入端到端线性流程：用户只需描述需求，其余全部自动完成。
如果没有检测到物理板卡，自动切换到 Wokwi 仿真。

---

## 三个版本对比

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

---

## 快速开始

### CLI 工具（推荐）

```bash
# 1. 安装
pip install -e arduino-client/[ui]

# 2. 启动端到端流程
arduino-client
```

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

### Web 版本

```bash
cd arduino-web
npm install
npm run dev            # 开发模式
npm run build          # 构建静态站点
```

---

## 发布版本（Release）

### 桌面版本发布流程

```bash
# 1. 构建可执行文件
cd arduino-desktop
npm run tauri:build

# 2. 产物位置
arduino-desktop/src-tauri/target/release/bundle/
├── msi/                    # Windows MSI 安装包
├── nsis/                   # Windows NSIS 安装程序
├── dmg/                    # macOS DMG 镜像
├── macos/                  # macOS App Bundle
├── deb/                    # Linux Debian 包
└── appimage/               # Linux AppImage
```

**独立可执行文件**：
```
arduino-desktop/src-tauri/target/release/arduino-desktop(.exe)
```

### 创建 GitHub Release

```bash
# 1. 版本更新
# 修改 arduino-desktop/src-tauri/tauri.conf.json 中的版本号
# 或 package.json 中的版本号

# 2. 创建 Git 标签
git tag -a v0.3.0 -m "Release version 0.3.0"
git push origin v0.3.0

# 3. GitHub 自动创建 Release（如配置了 CI）
# 或手动在 GitHub 上：
# - 进入 Releases 页面
# - 点击 "Draft a new release"
# - 选择标签 v0.3.0
# - 上传平台对应的安装包
# - 发布
```

### CLI 版本发布

```bash
# 1. 更新版本号 (pyproject.toml)
cd arduino-client
# 修改 version = "x.y.z"

# 2. 发布到 PyPI
python -m build
python -m twine upload dist/*
```

---

## 项目结构

```
arduino_tools/
├── arduino-client/          # CLI 工具 (Python + Rich)
│   ├── arduino_client/      # 核心代码
│   │   ├── ui/              # Rich UI 组件
│   │   ├── cli_rich.py      # CLI 入口
│   │   ├── client.py        # 核心 API
│   │   ├── code_generator.py    # LLM 生成
│   │   ├── builder.py       # 编译封装
│   │   └── board_detector.py    # 板卡检测
│   └── pyproject.toml
│
├── arduino-desktop/         # 桌面应用 (Tauri + React)
│   ├── src/                 # React 前端
│   ├── src-tauri/           # Rust 后端（Tauri）
│   └── src-tauri/tauri.conf.json  # 版本配置
│
├── arduino-web/             # Web 版本 (React + Vite)
│   ├── src/                 # React 代码
│   └── package.json
│
└── arduino-mcp-server/      # MCP Server（早期版本）
```

---

## 系统要求

### CLI
- Python 3.9+
- arduino-cli（自动检测或下载）
- LLM API Key（Kimi / OpenAI / 兼容 API）

### Desktop
- Node.js 18+
- Rust + Cargo（仅构建时需要）
- npm / yarn

### Web
- 现代浏览器（Chrome, Firefox, Safari）
- LLM API Key

---

## 技术栈

| 层级 | 技术 |
|------|------|
| CLI | Python + Rich UI + pyserial |
| Desktop | Tauri + React + TypeScript + Rust |
| Web | React + Vite + TypeScript |
| 编译 | arduino-cli |
| 仿真 | wokwi-cli |
| LLM | Moonshot Kimi / OpenAI |

---

## 核心特性

### 1. 端到端自动化
- 一条命令从需求到运行代码
- 自动检测板卡，无需手动配置
- 自动编译、烧录、验证

### 2. AI 代码生成
- 自然语言描述 → Arduino 代码
- 基于实际硬件约束生成代码
- 支持多种板卡和传感器

### 3. 智能修复
- 编译失败自动诊断和修复
- 运行时异常自动调整代码
- 最多 5 轮自动修复（防止无限循环）

### 4. Wokwi 仿真
- 无硬件情况下自动仿真
- 支持多种 Arduino 板卡和组件
- 自动生成电路图配置

### 5. 安全框架
- **Agent-Guard**: 防止危险操作，速率限制
  - 所有文件操作被监控
  - 自动修复次数限制（防止循环）
  - 凭证自动隐藏
- **First Principles**: 改进推理质量
  - 审计代码生成的假设
  - 分解问题到基础
  - 避免基于惯例的错误决策

---

## 开发指南

### 设置开发环境

**推荐使用 Claude Code + 以下框架**：

1. **First Principles**（认知框架）
   ```bash
   # 已自动安装到 ~/.claude/CLAUDE.md
   # 改进推理质量，审计假设，分解到基础
   ```

2. **Agent-Guard**（安全框架）
   ```bash
   # 已自动安装，监控所有工具操作
   # npm install -g agent-guard
   # 防止危险操作，限制修复循环
   ```

### 贡献指南

1. 代码应在 First Principles 框架下开发
   - 审计需求而不是复制模式
   - 分解到可验证的部分
   - 考虑约束而非惯例

2. 所有工具操作由 Agent-Guard 保护
   - 自动速率限制
   - 安全检查
   - 操作审计

---

## 许可证

MIT

---

## 最新版本

| 版本 | 发布日期 | 主要更新 |
|------|---------|---------|
| v0.3.0 | 2026-04-12 | 集成 Agent-Guard 和 First Principles 安全框架 |
| v0.2.3+ | 2026-04-12 | 仿真文件 API，优化自动修复 |
| v0.2.0+ | 2026-04-01 | 终端式 UI 重设计，去除对话形式 |
