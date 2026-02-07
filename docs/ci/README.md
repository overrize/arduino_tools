# Arduino Tools - 持续集成 (CI)

本目录包含持续集成测试的说明文档。

## 概述

项目使用 **GitHub Actions** 进行持续集成，在每次 push 或 pull request 时自动运行测试。

### 工作流文件

- `.github/workflows/ci.yml` - 主 CI 工作流

### 触发条件

- `push` 到 `main`、`master`、`develop` 分支
- `pull_request` 到上述分支

## 测试分层

| 层级 | 标记 | 说明 | CI 中运行 |
|------|------|------|----------|
| 单元测试 | `@pytest.mark.unit` | 无外部依赖，纯逻辑测试 | ✅ 是 |
| 集成测试 | `@pytest.mark.integration` | 需要 arduino-cli | ✅ 是 |
| 硬件测试 | `@pytest.mark.hardware` | 需要实体 Arduino 板 | ❌ 否* |

\* 硬件测试需设置环境变量 `ARDUINO_HARDWARE_TEST=1` 才会运行

## 本地运行测试

### 1. 安装依赖

```bash
cd arduino-mcp-server
pip install -e ".[dev]"
```

### 2. 仅运行单元测试（无需 arduino-cli）

```bash
# 推荐使用 python -m pytest 确保使用正确 Python 环境
python -m pytest tests/ -m unit -v
```

### 3. 运行单元 + 集成测试（需要 arduino-cli）

```bash
# 确保 arduino-cli 已安装并在 PATH 中
arduino-cli version

# 安装 Arduino 核心（首次需要）
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli core install arduino:mbed_rp2040

# 运行测试
pytest tests/ -m "unit or integration" -v
```

### 4. 运行所有测试（含硬件，需要连接板子）

```bash
# Windows PowerShell
$env:ARDUINO_HARDWARE_TEST="1"
pytest tests/ -v

# Linux / macOS
ARDUINO_HARDWARE_TEST=1 pytest tests/ -v
```

### 5. 按文件运行

```bash
pytest tests/test_ci_unit.py -v
pytest tests/test_ci_integration.py -v
```

## CI 环境

- **OS**: Ubuntu Latest
- **Python**: 3.10
- **arduino-cli**: 通过官方安装脚本安装
- **Arduino 核心**: arduino:avr, arduino:mbed_rp2040

## 测试目录结构

```
arduino-mcp-server/
├── pytest.ini              # Pytest 配置
├── tests/
│   ├── conftest.py         # 共享 fixtures
│   ├── test_ci_unit.py     # 单元测试
│   ├── test_ci_integration.py  # 集成测试
│   └── test_ci_hardware.py     # 硬件测试（CI 中跳过）
└── test_src/               # 原有脚本式测试（非 CI）
```

## 故障排查

### 集成测试被跳过

- 确保 `arduino-cli` 在 PATH 中：`arduino-cli version`
- 安装 Arduino 核心后再运行

### 编译失败

- 检查 arduino-cli 核心是否安装：`arduino-cli core list`
- 如需 Pico：`arduino-cli core install arduino:mbed_rp2040`

### 本地 CI 模拟

可安装 [act](https://github.com/nektos/act) 在本地模拟 GitHub Actions：

```bash
act -j test-arduino-mcp-server
```

---

**文档版本**: 1.0  
**最后更新**: 2026-02-07
