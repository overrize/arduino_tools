# 文档整理实现计划

> **对于 Kiro：** 必需的子技能：使用 executing-plans 逐任务实现此计划。

**目标：** 将根目录下混乱的 20+ 个 MD 文档按功能模块分类整理，提高可读性和可维护性

**架构：** 创建 docs/ 目录结构，按功能模块（mcp-server/cli-tool/detection/wokwi/general）分类，移动文档并更新索引

**技术栈：** Markdown, 文件系统操作

---

## 任务 1：创建目录结构

**文件：**
- 创建：`docs/mcp-server/`
- 创建：`docs/cli-tool/`
- 创建：`docs/detection/`
- 创建：`docs/wokwi/`
- 创建：`docs/general/`
- 创建：`docs/archive/`

**步骤 1：创建目录**

```bash
mkdir -p docs/mcp-server
mkdir -p docs/cli-tool
mkdir -p docs/detection
mkdir -p docs/wokwi
mkdir -p docs/general
mkdir -p docs/archive
```

**步骤 2：验证目录创建**

运行：`ls -la docs/`
预期：看到 6 个子目录

---

## 任务 2：移动 MCP Server 相关文档

**文件：**
- 移动：`MCP_READY.md` → `docs/mcp-server/`
- 移动：`PROJECT_SUMMARY.md` → `docs/mcp-server/`
- 移动：`PROJECT_CHECKLIST.md` → `docs/mcp-server/`
- 移动：`ARDUINO_CLI_SETUP.md` → `docs/mcp-server/`

**步骤 1：移动文件**

```bash
mv MCP_READY.md docs/mcp-server/
mv PROJECT_SUMMARY.md docs/mcp-server/
mv PROJECT_CHECKLIST.md docs/mcp-server/
mv ARDUINO_CLI_SETUP.md docs/mcp-server/
```

**步骤 2：验证移动**

运行：`ls docs/mcp-server/`
预期：看到 4 个文件

---

## 任务 3：移动 CLI Tool 相关文档

**文件：**
- 移动：`CLI_TOOL_COMPLETE.md` → `docs/cli-tool/`
- 移动：`CLI_V2_COMPLETE.md` → `docs/cli-tool/`

**步骤 1：移动文件**

```bash
mv CLI_TOOL_COMPLETE.md docs/cli-tool/
mv CLI_V2_COMPLETE.md docs/cli-tool/
```

**步骤 2：验证移动**

运行：`ls docs/cli-tool/`
预期：看到 2 个文件

---

## 任务 4：移动 Detection 相关文档

**文件：**
- 移动：`DETECTION_COMPLETE.md` → `docs/detection/`
- 移动：`DETECTION_UPGRADE.md` → `docs/detection/`
- 移动：`DETECTION_CHECKLIST.md` → `docs/detection/`

**步骤 1：移动文件**

```bash
mv DETECTION_COMPLETE.md docs/detection/
mv DETECTION_UPGRADE.md docs/detection/
mv DETECTION_CHECKLIST.md docs/detection/
```

**步骤 2：验证移动**

运行：`ls docs/detection/`
预期：看到 3 个文件

---

## 任务 5：移动 Wokwi 相关文档

**文件：**
- 移动：`WOKWI_READY.md` → `docs/wokwi/`

**步骤 1：移动文件**

```bash
mv WOKWI_READY.md docs/wokwi/
```

**步骤 2：验证移动**

运行：`ls docs/wokwi/`
预期：看到 1 个文件

---

## 任务 6：移动通用文档

**文件：**
- 移动：`GETTING_STARTED.md` → `docs/general/`
- 移动：`HOW_TO_USE_IN_KIRO.md` → `docs/general/`
- 移动：`DEMO_SCRIPT.md` → `docs/general/`
- 移动：`KIRO_TEST_COMMANDS.md` → `docs/general/`
- 移动：`QUICK_TEST_GUIDE.md` → `docs/general/`
- 移动：`FINAL_TEST_GUIDE.md` → `docs/general/`

**步骤 1：移动文件**

```bash
mv GETTING_STARTED.md docs/general/
mv HOW_TO_USE_IN_KIRO.md docs/general/
mv DEMO_SCRIPT.md docs/general/
mv KIRO_TEST_COMMANDS.md docs/general/
mv QUICK_TEST_GUIDE.md docs/general/
mv FINAL_TEST_GUIDE.md docs/general/
```

**步骤 2：验证移动**

运行：`ls docs/general/`
预期：看到 6 个文件

---

## 任务 7：归档过时文档

**文件：**
- 移动：`CONTEXT_TRANSFER_COMPLETE.md` → `docs/archive/`
- 移动：`READY_TO_TEST.md` → `docs/archive/`
- 移动：`SUCCESS_REPORT.md` → `docs/archive/`
- 移动：`NEXT_STEPS.md` → `docs/archive/`

**步骤 1：移动文件**

```bash
mv CONTEXT_TRANSFER_COMPLETE.md docs/archive/
mv READY_TO_TEST.md docs/archive/
mv SUCCESS_REPORT.md docs/archive/
mv NEXT_STEPS.md docs/archive/
```

**步骤 2：验证移动**

运行：`ls docs/archive/`
预期：看到 4 个文件

---

## 任务 8：创建文档索引

**文件：**
- 创建：`docs/README.md`

**步骤 1：创建索引文件**

```markdown
# Arduino Tools 文档索引

本目录包含 Arduino MCP Server 和相关工具的所有文档。

## 📁 目录结构

### MCP Server (`mcp-server/`)
MCP Server 核心功能和配置文档
- `MCP_READY.md` - MCP Server 就绪状态
- `PROJECT_SUMMARY.md` - 项目总结
- `PROJECT_CHECKLIST.md` - 项目检查清单
- `ARDUINO_CLI_SETUP.md` - Arduino CLI 设置指南

### CLI Tool (`cli-tool/`)
命令行工具相关文档
- `CLI_TOOL_COMPLETE.md` - CLI 工具完成报告
- `CLI_V2_COMPLETE.md` - CLI V2 完成报告

### Detection (`detection/`)
板卡检测功能文档
- `DETECTION_COMPLETE.md` - 检测功能完成报告
- `DETECTION_UPGRADE.md` - 检测功能升级说明
- `DETECTION_CHECKLIST.md` - 检测功能检查清单

### Wokwi (`wokwi/`)
Wokwi 仿真集成文档
- `WOKWI_READY.md` - Wokwi 集成就绪状态

### General (`general/`)
通用指南和测试文档
- `GETTING_STARTED.md` - 快速开始指南
- `HOW_TO_USE_IN_KIRO.md` - Kiro 使用指南
- `DEMO_SCRIPT.md` - 演示脚本
- `KIRO_TEST_COMMANDS.md` - Kiro 测试命令
- `QUICK_TEST_GUIDE.md` - 快速测试指南
- `FINAL_TEST_GUIDE.md` - 最终测试指南

### Archive (`archive/`)
已过时或历史文档
- `CONTEXT_TRANSFER_COMPLETE.md`
- `READY_TO_TEST.md`
- `SUCCESS_REPORT.md`
- `NEXT_STEPS.md`

## 🚀 快速导航

### 新用户
1. 阅读 `general/GETTING_STARTED.md`
2. 查看 `general/HOW_TO_USE_IN_KIRO.md`
3. 尝试 `general/DEMO_SCRIPT.md`

### 开发者
1. 查看 `mcp-server/PROJECT_SUMMARY.md`
2. 了解 `detection/DETECTION_COMPLETE.md`
3. 参考 `wokwi/WOKWI_READY.md`

### 测试
1. 使用 `general/QUICK_TEST_GUIDE.md`
2. 参考 `general/KIRO_TEST_COMMANDS.md`

## 📚 相关文档

- 主 README: `../README.md`
- MCP Server 详细文档: `../arduino-mcp-server/README.md`
- CLI Tool 文档: `../arduino-cli/README.md`
```

**步骤 2：保存文件**

保存到：`docs/README.md`

**步骤 3：验证创建**

运行：`cat docs/README.md | head -20`
预期：看到索引内容

---

## 任务 9：更新根目录 README

**文件：**
- 修改：`README.md`

**步骤 1：在 README 中添加文档链接**

在 README.md 末尾添加：

```markdown

## 📚 文档

详细文档已整理到 `docs/` 目录：

- **[文档索引](docs/README.md)** - 完整文档导航
- **[快速开始](docs/general/GETTING_STARTED.md)** - 新用户指南
- **[Kiro 使用](docs/general/HOW_TO_USE_IN_KIRO.md)** - Kiro 集成指南
- **[项目总结](docs/mcp-server/PROJECT_SUMMARY.md)** - 项目概览

### 按功能查找

- **MCP Server**: `docs/mcp-server/`
- **CLI Tool**: `docs/cli-tool/`
- **板卡检测**: `docs/detection/`
- **Wokwi 仿真**: `docs/wokwi/`
- **通用指南**: `docs/general/`
```

**步骤 2：验证修改**

运行：`tail -20 README.md`
预期：看到新添加的文档链接

---

## 任务 10：创建各模块的 README

**文件：**
- 创建：`docs/mcp-server/README.md`
- 创建：`docs/cli-tool/README.md`
- 创建：`docs/detection/README.md`
- 创建：`docs/wokwi/README.md`
- 创建：`docs/general/README.md`

**步骤 1：创建 MCP Server README**

```markdown
# MCP Server 文档

Arduino MCP Server 核心功能和配置文档。

## 文档列表

- **[MCP_READY.md](MCP_READY.md)** - MCP Server 就绪状态和配置指南
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - 项目总结和架构概览
- **[PROJECT_CHECKLIST.md](PROJECT_CHECKLIST.md)** - 项目开发检查清单
- **[ARDUINO_CLI_SETUP.md](ARDUINO_CLI_SETUP.md)** - Arduino CLI 安装和配置

## 快速链接

- [返回文档索引](../README.md)
- [MCP Server 源码](../../arduino-mcp-server/)
```

保存到：`docs/mcp-server/README.md`

**步骤 2：创建 CLI Tool README**

```markdown
# CLI Tool 文档

Arduino CLI 工具开发和完成报告。

## 文档列表

- **[CLI_TOOL_COMPLETE.md](CLI_TOOL_COMPLETE.md)** - CLI 工具完成报告
- **[CLI_V2_COMPLETE.md](CLI_V2_COMPLETE.md)** - CLI V2 版本完成报告

## 快速链接

- [返回文档索引](../README.md)
- [CLI Tool 源码](../../arduino-cli/)
```

保存到：`docs/cli-tool/README.md`

**步骤 3：创建 Detection README**

```markdown
# 板卡检测文档

板卡检测功能的实现、升级和验证文档。

## 文档列表

- **[DETECTION_COMPLETE.md](DETECTION_COMPLETE.md)** - 检测功能完成报告和总结
- **[DETECTION_UPGRADE.md](DETECTION_UPGRADE.md)** - 检测功能升级说明
- **[DETECTION_CHECKLIST.md](DETECTION_CHECKLIST.md)** - 检测功能验证清单

## 相关文档

- [板卡检测详细文档](../../arduino-mcp-server/BOARD_DETECTION.md)
- [检测示例](../../arduino-mcp-server/DETECTION_EXAMPLE.md)
- [快速参考](../../arduino-mcp-server/DETECTION_QUICK_REF.md)

## 快速链接

- [返回文档索引](../README.md)
```

保存到：`docs/detection/README.md`

**步骤 4：创建 Wokwi README**

```markdown
# Wokwi 仿真文档

Wokwi 仿真集成的实现和使用文档。

## 文档列表

- **[WOKWI_READY.md](WOKWI_READY.md)** - Wokwi 集成就绪状态和测试指南

## 相关文档

- [Wokwi 仿真详细文档](../../arduino-mcp-server/WOKWI_SIMULATION.md)

## 快速链接

- [返回文档索引](../README.md)
```

保存到：`docs/wokwi/README.md`

**步骤 5：创建 General README**

```markdown
# 通用文档

快速开始指南、使用教程和测试文档。

## 文档列表

### 入门指南
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - 快速开始指南
- **[HOW_TO_USE_IN_KIRO.md](HOW_TO_USE_IN_KIRO.md)** - Kiro 使用指南
- **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** - 演示脚本

### 测试指南
- **[KIRO_TEST_COMMANDS.md](KIRO_TEST_COMMANDS.md)** - Kiro 测试命令
- **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** - 快速测试指南
- **[FINAL_TEST_GUIDE.md](FINAL_TEST_GUIDE.md)** - 最终测试指南

## 快速链接

- [返回文档索引](../README.md)
```

保存到：`docs/general/README.md`

**步骤 6：验证所有 README 创建**

运行：`find docs -name "README.md"`
预期：看到 6 个 README.md 文件

---

## 任务 11：验证整理结果

**步骤 1：检查根目录清理**

运行：`ls *.md`
预期：只剩下 `README.md`（和可能的 `Embedd agent.xmind`）

**步骤 2：检查 docs 目录结构**

运行：`tree docs -L 2`
预期：看到完整的目录结构和文件分布

**步骤 3：验证文档数量**

运行：`find docs -name "*.md" | wc -l`
预期：约 25 个文件（包括 README）

**步骤 4：测试文档链接**

手动检查几个关键文档的链接是否正确

---

## 完成标准

- ✅ 所有文档按功能模块分类
- ✅ 每个模块有独立的 README
- ✅ 创建了总索引文档
- ✅ 根目录 README 更新了文档链接
- ✅ 根目录只保留主 README
- ✅ 文档结构清晰易导航
