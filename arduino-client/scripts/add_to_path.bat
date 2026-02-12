@echo off
REM Arduino Client - 添加 Scripts 目录到 PATH (Windows Batch)
REM 此脚本会将 arduino-client.exe 所在目录添加到用户 PATH 环境变量

echo 正在查找 arduino-client.exe 安装位置...

REM 尝试使用 where 命令查找
where arduino-client.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 找到 arduino-client.exe，已在 PATH 中
    goto :end
)

REM 尝试从 pip 获取安装位置
python -m pip show arduino-client >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误：无法找到 arduino-client 安装
    echo 请先运行: pip install -e arduino-client/
    exit /b 1
)

REM 获取 Python Scripts 目录
for /f "tokens=2 delims=: " %%i in ('python -m pip show arduino-client ^| findstr /C:"Location:"') do set PACKAGE_LOCATION=%%i
set PACKAGE_LOCATION=%PACKAGE_LOCATION: =%

REM 构建 Scripts 路径
for %%i in ("%PACKAGE_LOCATION%\..\Scripts") do set SCRIPTS_PATH=%%~fi

if not exist "%SCRIPTS_PATH%\arduino-client.exe" (
    echo 错误：无法找到 arduino-client.exe
    echo 请手动运行: python -m arduino_client setup
    exit /b 1
)

echo 找到 Scripts 目录: %SCRIPTS_PATH%

REM 检查是否已在 PATH 中
echo %PATH% | findstr /C:"%SCRIPTS_PATH%" >nul
if %ERRORLEVEL% EQU 0 (
    echo Scripts 目录已在 PATH 中
    goto :end
)

REM 添加到用户 PATH
echo 正在添加到用户 PATH...
setx PATH "%PATH%;%SCRIPTS_PATH%" >nul

echo ✓ 已添加到用户 PATH
echo.
echo 注意：需要重新打开命令提示符窗口才能生效
echo 然后可以运行: arduino-client setup

:end
pause
