@echo off
REM Arduino 开发 CLI 工具启动脚本 - 自然语言版本

REM 设置编码为 UTF-8
chcp 65001 >nul 2>&1

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装 Python 3.8+
    echo.
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 运行 CLI 工具
python "%~dp0arduino_dev_v2.py" %*

REM 如果出错，暂停
if errorlevel 1 pause
