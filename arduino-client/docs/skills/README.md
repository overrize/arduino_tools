# Cursor Skills

基于项目经验整理的 Cursor 技能。

## 技能列表

| 技能 | 用途 |
|------|------|
| **arduino-cli-integration** | Arduino CLI 集成，板卡检测、编译、上传、串口监控 |

## 安装

复制到 Cursor 可识别的 skills 目录：

**项目级（推荐）：**
```powershell
# 在项目根目录执行
New-Item -ItemType Directory -Force .cursor\skills
Copy-Item -Recurse docs\skills\* .cursor\skills\
```

**用户级（所有项目生效）：**
```powershell
New-Item -ItemType Directory -Force $env:USERPROFILE\.cursor\skills
Copy-Item -Recurse docs\skills\* $env:USERPROFILE\.cursor\skills\
```

## 使用

安装后，在对话中用 `@arduino-cli-integration` 引用，或在相关场景下由 AI 自动应用。
