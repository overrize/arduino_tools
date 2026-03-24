# Arduino Web

AI 驱动的 Arduino 代码生成器 Web 版本。纯浏览器运行，无需安装。

## 功能特性

- 🤖 **AI 代码生成** - 自然语言描述 → Arduino 代码
- 💬 **对话式界面** - 直观的聊天界面
- 📦 **ZIP 导出** - 一键下载完整项目
- 🌐 **纯浏览器** - 无需安装，打开即用
- 💾 **本地存储** - 项目保存在浏览器本地

## 快速开始

```bash
cd arduino-web
npm install
npm run dev
```

访问 http://localhost:3000

## 使用方法

1. 打开网页后，点击设置按钮配置 LLM API
2. 选择目标 Arduino 板卡
3. 在输入框描述你的项目需求
4. 系统生成代码后，可以导出为 ZIP 文件
5. 使用 Arduino IDE 或 arduino-cli 打开 ZIP 中的 .ino 文件

## 配置 LLM API

**Kimi (推荐):**
- Base URL: `https://api.moonshot.cn/v1`
- Model: `kimi-k2-0905-preview`

**OpenAI:**
- Base URL: `https://api.openai.com/v1`
- Model: `gpt-4`

## 部署

构建静态站点：

```bash
npm run build
```

将 `dist/` 目录部署到任何静态托管服务（Vercel、Netlify、GitHub Pages 等）。

## 与 Desktop 版本的区别

| 功能 | Web 版本 | Desktop 版本 |
|------|---------|-------------|
| 代码生成 | ✅ | ✅ |
| ZIP 导出 | ✅ | ✅ |
| 本地构建 | ❌ | ✅ |
| 板卡烧录 | ❌ | ✅ |
| 串口监控 | ❌ | ✅ |
| 离线使用 | ❌ | ✅ |

## 技术栈

- React 18
- TypeScript
- Vite
- JSZip (ZIP 导出)

## License

MIT
