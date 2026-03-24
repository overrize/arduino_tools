# Arduino Desktop 构建修复

## 问题: TaskDialogIndirect 错误

这个错误通常是由于以下原因之一：

### 1. 缺少 Visual C++ Redistributable

下载并安装 Microsoft Visual C++ Redistributable:
- https://aka.ms/vs/17/release/vc_redist.x64.exe

### 2. 使用开发模式运行

```bash
cd arduino-desktop
npm install
npm run tauri:dev
```

### 3. 重新构建

```bash
# 清理缓存
rm -rf src-tauri/target

# 重新构建
npm run tauri:build
```

## Windows 兼容性

如果遇到 TaskDialogIndirect 错误，尝试以下方案：

**方案 A: 安装 VC++ Redist (推荐)**
```powershell
# 以管理员身份运行 PowerShell
winget install Microsoft.VCRedist.2015+.x64
```

**方案 B: 降级 Tauri 版本**
```toml
# Cargo.toml 中修改为
tauri = { version = "1.4", ... }
tauri-build = { version = "1.4", ... }
```

**方案 C: 使用 Web 版本**
如果 Desktop 版本无法运行，可以使用 Web 版本：
```bash
cd arduino-web
npm install
npm run dev
```
