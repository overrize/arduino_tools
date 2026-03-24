# Arduino Desktop

AI 驱动的 Arduino 桌面开发工具，提供端到端的自然语言开发体验。

## 功能特性

- 🤖 **AI 代码生成** - 自然语言描述 → Arduino 代码
- 💬 **对话式界面** - Claude 风格聊天界面
- 🔨 **一键构建** - 集成 arduino-cli 编译
- ⚡ **自动烧录** - 检测板卡并自动上传
- 🎨 **Claude 风格 UI** - 暗黑主题，优雅界面
- 📁 **项目管理** - 历史项目列表

## 快速开始

### 前置要求

- Node.js 18+
- Rust (安装 Tauri 需要)
- arduino-cli

### 安装

```bash
cd arduino-desktop
npm install
```

### 开发模式

```bash
npm run tauri:dev
```

### 构建发布版

```bash
npm run tauri:build
```

构建完成后，可执行文件位于：
- Windows: `src-tauri/target/release/arduino-desktop.exe`

## 使用方法

1. 启动应用后，点击设置按钮配置 LLM API (支持 OpenAI、Kimi 等)
2. 选择目标 Arduino 板卡
3. 在输入框描述你的项目需求
4. 系统自动生成代码、编译并烧录到板卡

## 项目结构

```
arduino-desktop/
├── src/                    # React 前端
│   ├── components/        # UI 组件
│   ├── App.tsx           # 主应用
│   └── ...
├── src-tauri/             # Tauri (Rust) 后端
│   ├── src/
│   │   ├── commands.rs   # Tauri 命令
│   │   ├── llm.rs        # LLM 集成
│   │   └── project.rs    # 项目数据结构
│   └── Cargo.toml
└── package.json
```

## 配置

在设置中配置 LLM API：

**Kimi (推荐):**
- Base URL: `https://api.moonshot.cn/v1`
- Model: `kimi-k2-0905-preview`

**OpenAI:**
- Base URL: `https://api.openai.com/v1`
- Model: `gpt-4`

## 技术栈

- **前端**: React + TypeScript + Vite
- **后端**: Rust + Tauri
- **构建**: arduino-cli
- **LLM**: OpenAI API (兼容)

## License

MIT
