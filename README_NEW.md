# Arduino Tools 项目

> 自然语言驱动的 Arduino 端到端开发工具

## 📚 新增内容

本项目现在包含 **三个版本**：

1. **CLI 工具** (`arduino-client/`) - 命令行界面 ⭐ 已完成
2. **桌面应用** (`arduino-desktop/`) - Tauri + React 🆕 **新增**
3. **Web 版本** (`arduino-web/`) - 纯浏览器版 🆕 **新增**

所有版本都提供一致的交互体验：自然语言输入 → AI 生成代码 → 编译/导出。

---

## 🎯 架构对比

| 功能 | CLI | Desktop | Web |
|------|-----|---------|-----|
| 自然语言输入 | ✅ | ✅ | ✅ |
| AI 代码生成 | ✅ | ✅ | ✅ |
| 本地编译 | ✅ | ✅ | ❌ |
| 板卡烧录 | ✅ | ✅ | ❌ |
| ZIP 导出 | ❌ | ✅ | ✅ |
| 串口监控 | ✅ | ✅ | ❌ |
| 安装要求 | Python | 可执行文件 | 浏览器 |

---

## 🚀 快速开始

### CLI 工具

```bash
pip install -e arduino-client/
arduino-client
```

### 桌面应用

```bash
# 开发模式
build-desktop.bat dev

# 构建发布版
build-desktop.bat build
```

### Web 版本

```bash
# 开发模式
build-web.bat dev

# 构建静态站点
build-web.bat build
```

---

## 📁 项目结构

```
arduino_tools/
├── arduino-client/        # CLI 工具 (Python)
│   ├── arduino_client/
│   └── README.md
│
├── arduino-desktop/       # 桌面应用 (Tauri + React) 🆕
│   ├── src/              # React 前端
│   ├── src-tauri/        # Rust 后端
│   └── README.md
│
├── arduino-web/          # Web 版本 (React + Vite) 🆕
│   ├── src/
│   └── README.md
│
├── build-desktop.bat     # 桌面版构建脚本
├── build-web.bat         # Web 版构建脚本
└── README.md
```

---

## 💻 桌面应用特性

- **Claude 风格 UI** - 暗黑主题，优雅界面
- **对话式开发** - 自然语言描述需求
- **端到端自动化** - 生成 → 构建 → 烧录
- **项目管理** - 历史项目列表
- **板卡检测** - 自动检测连接的 Arduino 板卡
- **实时日志** - 构建和烧录过程实时显示

## 🌐 Web 版本特性

- **纯浏览器运行** - 无需安装
- **ZIP 导出** - 一键下载项目
- **本地存储** - 项目保存在浏览器
- **快速部署** - 可部署到任何静态托管

---

## 🔧 系统要求

### CLI / Desktop
- Python 3.10+
- arduino-cli
- LLM API Key (OpenAI / Kimi)

### Desktop 额外要求
- Node.js 18+
- Rust

### Web
- 现代浏览器
- LLM API Key

---

## 📖 详细文档

- [CLI 工具文档](arduino-client/README.md)
- [桌面应用文档](arduino-desktop/README.md)
- [Web 版本文档](arduino-web/README.md)

---

## 🎨 界面预览

所有版本采用统一的暗黑主题设计：
- 主色调：#1a1a2e (深蓝)
- 强调色：#e94560 (红色)
- 侧边栏：项目历史
- 主界面：对话式交互

---

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| CLI | Python + Rich |
| Desktop Frontend | React + TypeScript + Vite |
| Desktop Backend | Rust + Tauri |
| Web | React + TypeScript + Vite |
| Build Tool | arduino-cli |
| LLM | OpenAI API (兼容) |

---

## 📝 更新日志

### 2024-03-24
- ✨ 新增 Arduino Desktop (Tauri + React)
- ✨ 新增 Arduino Web (React + Vite)
- ✅ 完整实现端到端工作流
- ✅ 统一 UI 设计
- ✅ 项目管理系统

---

## 🤝 贡献

欢迎提交 PR 和 Issue！

---

## 📄 许可证

MIT
