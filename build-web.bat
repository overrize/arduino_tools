@echo off
chcp 65001 >nul
echo ==========================================
echo Arduino Web 构建脚本
echo ==========================================
echo.

set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=dev

if "%BUILD_TYPE%"=="dev" goto dev
if "%BUILD_TYPE%"=="build" goto build
goto help

:dev
echo 启动开发服务器...
cd /d "%~dp0\arduino-web"
npm install
npm run dev
goto end

:build
echo 构建 Web 版本...
cd /d "%~dp0\arduino-web"
npm install
npm run build
echo.
echo 构建完成！
echo 静态文件位置：arduino-web\dist\
goto end

:help
echo 用法：
echo   build-web.bat dev    - 启动开发服务器
echo   build-web.bat build  - 构建静态站点
goto end

:end
