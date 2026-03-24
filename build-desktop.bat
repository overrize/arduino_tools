@echo off
chcp 65001 >nul
echo ==========================================
echo Arduino Desktop 构建脚本
echo ==========================================
echo.

set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=dev

if "%BUILD_TYPE%"=="dev" goto dev
if "%BUILD_TYPE%"=="build" goto build
goto help

:dev
echo 启动开发模式...
cd /d "%~dp0\arduino-desktop"
npm run tauri:dev
goto end

:build
echo 构建发布版本...
cd /d "%~dp0\arduino-desktop"
npm install
npm run tauri:build
echo.
echo 构建完成！
echo 可执行文件位置：arduino-desktop\src-tauri\target\release\arduino-desktop.exe
goto end

:help
echo 用法：
echo   build-desktop.bat dev    - 启动开发模式
echo   build-desktop.bat build  - 构建发布版本
goto end

:end
