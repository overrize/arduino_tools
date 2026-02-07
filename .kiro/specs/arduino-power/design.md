# Arduino CLI Tool - Design Document

## 概述

创建一个友好的命令行工具 `arduino-dev`，提供引导式界面来收集用户需求，然后自动生成 Kiro 命令调用 Arduino MCP Server。

---

## 架构设计

### 组件结构

```
arduino-cli/
├── arduino_dev.py          # 主程序入口
├── ui/
│   ├── __init__.py
│   ├── menu.py            # 菜单系统
│   ├── prompts.py         # 用户输入提示
│   └── display.py         # 显示和格式化
├── core/
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── project.py         # 项目配置
│   └── kiro_integration.py # Kiro 集成
├── templates/
│   └── commands.json      # 命令模板
└── arduino-dev.bat        # Windows 启动脚本
```

---

## 核心模块设计

### 1. 主程序 (arduino_dev.py)

```python
"""Arduino 开发 CLI 工具"""

def main():
    """主入口"""
    # 1. 显示欢迎界面
    display_welcome()
    
    # 2. 检查依赖
    check_dependencies()
    
    # 3. 显示主菜单
    while True:
        choice = show_main_menu()
        
        if choice == 1:
            create_new_project()
        elif choice == 2:
            compile_project()
        elif choice == 3:
            upload_project()
        elif choice == 4:
            monitor_serial()
        elif choice == 5:
            show_help()
        elif choice == 0:
            break
```

**功能：**
- 程序入口和主循环
- 菜单导航
- 功能分发

---

### 2. 菜单系统 (ui/menu.py)

```python
"""菜单显示和选择"""

class Menu:
    """菜单类"""
    
    def show_main_menu(self) -> int:
        """显示主菜单"""
        print("\n" + "="*50)
        print("🎯 Arduino 开发助手")
        print("="*50)
        print("\n请选择操作：")
        print("  1. 🆕 新建项目")
        print("  2. 🔨 编译项目")
        print("  3. 📤 上传到硬件")
        print("  4. 📡 监控串口")
        print("  5. ❓ 帮助")
        print("  0. 退出")
        
        return self.get_choice(0, 5)
    
    def show_board_menu(self) -> str:
        """选择板型"""
        print("\n选择板型：")
        print("  1. Raspberry Pi Pico")
        print("  2. Arduino Uno")
        print("  3. Arduino Nano")
        print("  4. ESP32")
        
        choice = self.get_choice(1, 4)
        boards = {
            1: "pico",
            2: "uno", 
            3: "nano",
            4: "esp32"
        }
        return boards[choice]
    
    def show_project_type_menu(self) -> str:
        """选择项目类型"""
        print("\n选择项目类型：")
        print("  1. LED 闪烁")
        print("  2. 按钮控制 LED")
        print("  3. 传感器读取")
        print("  4. 自定义")
        
        choice = self.get_choice(1, 4)
        types = {
            1: "led_blink",
            2: "button_led",
            3: "sensor",
            4: "custom"
        }
        return types[choice]
```

**功能：**
- 显示各种菜单
- 获取用户选择
- 输入验证

---

### 3. 用户输入 (ui/prompts.py)

```python
"""用户输入提示和收集"""

class Prompts:
    """输入提示类"""
    
    def get_pin_number(self, default: int = 25) -> int:
        """获取引脚号"""
        while True:
            pin = input(f"LED 引脚号 [默认: {default}]: ").strip()
            if not pin:
                return default
            try:
                pin_num = int(pin)
                if 0 <= pin_num <= 40:
                    return pin_num
                print("❌ 引脚号必须在 0-40 之间")
            except ValueError:
                print("❌ 请输入有效的数字")
    
    def get_interval(self, default: int = 1) -> int:
        """获取闪烁间隔"""
        while True:
            interval = input(f"闪烁间隔（秒）[默认: {default}]: ").strip()
            if not interval:
                return default
            try:
                interval_num = int(interval)
                if interval_num > 0:
                    return interval_num
                print("❌ 间隔必须大于 0")
            except ValueError:
                print("❌ 请输入有效的数字")
    
    def get_project_name(self, default: str = "my_project") -> str:
        """获取项目名称"""
        name = input(f"项目名称 [默认: {default}]: ").strip()
        return name if name else default
```

**功能：**
- 收集各种参数
- 输入验证
- 默认值处理

---

### 4. 显示模块 (ui/display.py)

```python
"""显示和格式化"""

class Display:
    """显示类"""
    
    def welcome(self):
        """欢迎界面"""
        print("\n" + "="*50)
        print("🎯 Arduino 开发助手")
        print("="*50)
        print("\n欢迎使用 Arduino 自然语言开发工具！")
        print("从想法到硬件，只需几步。\n")
    
    def show_project_summary(self, config: dict):
        """显示项目摘要"""
        print("\n" + "="*50)
        print("✅ 配置完成")
        print("="*50)
        print("\n项目信息：")
        print(f"  板型: {config['board_name']}")
        print(f"  类型: {config['project_type']}")
        print(f"  引脚: {config['pin']}")
        print(f"  间隔: {config['interval']} 秒")
        print()
    
    def show_progress(self, message: str):
        """显示进度"""
        print(f"⏳ {message}...")
    
    def show_success(self, message: str):
        """显示成功"""
        print(f"✅ {message}")
    
    def show_error(self, message: str):
        """显示错误"""
        print(f"❌ {message}")
```

**功能：**
- 格式化输出
- 进度提示
- 状态显示

---

### 5. 项目配置 (core/project.py)

```python
"""项目配置管理"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ProjectConfig:
    """项目配置"""
    board: str              # pico, uno, nano, esp32
    board_fqbn: str         # arduino:mbed_rp2040:pico
    project_type: str       # led_blink, button_led, sensor
    pin: int                # LED 引脚
    interval: int           # 闪烁间隔（秒）
    project_name: str       # 项目名称
    
    # 板型映射
    BOARD_MAPPING = {
        "pico": {
            "name": "Raspberry Pi Pico",
            "fqbn": "arduino:mbed_rp2040:pico",
            "default_pin": 25
        },
        "uno": {
            "name": "Arduino Uno",
            "fqbn": "arduino:avr:uno",
            "default_pin": 13
        },
        "nano": {
            "name": "Arduino Nano",
            "fqbn": "arduino:avr:nano",
            "default_pin": 13
        },
        "esp32": {
            "name": "ESP32",
            "fqbn": "esp32:esp32:esp32",
            "default_pin": 2
        }
    }
    
    @classmethod
    def from_user_input(cls, board: str, project_type: str, 
                       pin: int, interval: int, name: str):
        """从用户输入创建配置"""
        board_info = cls.BOARD_MAPPING[board]
        return cls(
            board=board,
            board_fqbn=board_info["fqbn"],
            project_type=project_type,
            pin=pin,
            interval=interval,
            project_name=name
        )
    
    def to_natural_language(self) -> str:
        """转换为自然语言描述"""
        board_name = self.BOARD_MAPPING[self.board]["name"]
        
        if self.project_type == "led_blink":
            return (f"用 {board_name} 做一个 LED 闪烁，"
                   f"{self.pin} 号引脚，每 {self.interval} 秒闪一次")
        elif self.project_type == "button_led":
            return f"用 {board_name} 做一个按钮控制 LED"
        else:
            return f"用 {board_name} 创建项目"
```

**功能：**
- 项目配置数据结构
- 板型映射
- 自然语言转换

---

### 6. Kiro 集成 (core/kiro_integration.py)

```python
"""Kiro 集成"""

import subprocess
import os
from pathlib import Path

class KiroIntegration:
    """Kiro 集成类"""
    
    def __init__(self):
        self.kiro_path = self._find_kiro()
    
    def _find_kiro(self) -> Optional[str]:
        """查找 Kiro 可执行文件"""
        # 常见位置
        possible_paths = [
            r"C:\Program Files\Kiro\kiro.exe",
            r"C:\Users\{}\AppData\Local\Kiro\kiro.exe".format(os.getenv("USERNAME")),
            "kiro",  # 在 PATH 中
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 尝试在 PATH 中查找
        try:
            subprocess.run(["kiro", "--version"], 
                         capture_output=True, check=True)
            return "kiro"
        except:
            return None
    
    def generate_command(self, config: ProjectConfig) -> str:
        """生成 Kiro 命令"""
        nl_description = config.to_natural_language()
        
        # 生成完整的 Kiro 命令
        command = (
            f"使用 Arduino MCP server 的 full_workflow_led_blink 工具，"
            f"{nl_description}"
        )
        
        return command
    
    def open_in_kiro(self, config: ProjectConfig, 
                     workspace: Optional[str] = None) -> bool:
        """在 Kiro 中打开项目"""
        if not self.kiro_path:
            print("❌ 未找到 Kiro，请手动打开 Kiro 并输入以下命令：")
            print(f"\n{self.generate_command(config)}\n")
            return False
        
        # 生成命令
        command = self.generate_command(config)
        
        # 保存到临时文件
        temp_file = Path.home() / ".arduino-dev-command.txt"
        temp_file.write_text(command, encoding="utf-8")
        
        print(f"\n✅ 命令已生成：")
        print(f"\n{command}\n")
        print(f"📋 已复制到剪贴板（如果支持）")
        
        # 尝试复制到剪贴板
        try:
            import pyperclip
            pyperclip.copy(command)
        except:
            pass
        
        # 打开 Kiro
        try:
            if workspace:
                subprocess.Popen([self.kiro_path, workspace])
            else:
                subprocess.Popen([self.kiro_path])
            
            print(f"✅ Kiro 已启动")
            print(f"💡 请在 Kiro 中粘贴上述命令")
            return True
        except Exception as e:
            print(f"❌ 启动 Kiro 失败: {e}")
            return False
```

**功能：**
- 查找 Kiro 可执行文件
- 生成 Kiro 命令
- 打开 Kiro
- 复制命令到剪贴板

---

### 7. 依赖检查 (core/config.py)

```python
"""配置和依赖检查"""

import subprocess
import sys

class DependencyChecker:
    """依赖检查器"""
    
    def check_all(self) -> bool:
        """检查所有依赖"""
        checks = [
            ("Python", self.check_python),
            ("arduino-cli", self.check_arduino_cli),
            ("MCP Server", self.check_mcp_server),
        ]
        
        all_ok = True
        for name, check_func in checks:
            if not check_func():
                print(f"❌ {name} 未安装或配置不正确")
                all_ok = False
            else:
                print(f"✅ {name} 已就绪")
        
        return all_ok
    
    def check_python(self) -> bool:
        """检查 Python"""
        return sys.version_info >= (3, 8)
    
    def check_arduino_cli(self) -> bool:
        """检查 arduino-cli"""
        try:
            result = subprocess.run(
                ["arduino-cli", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def check_mcp_server(self) -> bool:
        """检查 MCP Server"""
        try:
            result = subprocess.run(
                ["python", "-m", "arduino_mcp_server", "--help"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
```

**功能：**
- 检查 Python 版本
- 检查 arduino-cli
- 检查 MCP Server
- 提供安装指导

---

## 工作流程

### 新建项目流程

```
1. 用户启动 CLI
   ↓
2. 显示欢迎界面
   ↓
3. 检查依赖
   ↓
4. 显示主菜单
   ↓
5. 用户选择"新建项目"
   ↓
6. 选择板型 (Pico/Uno/Nano/ESP32)
   ↓
7. 选择项目类型 (LED闪烁/按钮/传感器)
   ↓
8. 输入参数 (引脚/间隔/名称)
   ↓
9. 显示配置摘要
   ↓
10. 生成 Kiro 命令
   ↓
11. 复制到剪贴板
   ↓
12. 打开 Kiro
   ↓
13. 提示用户粘贴命令
```

---

## 命令模板

### templates/commands.json

```json
{
  "led_blink": {
    "template": "使用 Arduino MCP server 的 full_workflow_led_blink 工具，用 {board_name} 做一个 LED 闪烁，{pin} 号引脚，每 {interval} 秒闪一次",
    "description": "LED 闪烁项目"
  },
  "button_led": {
    "template": "使用 Arduino MCP server 的 create_led_blink 工具，用 {board_name} 做一个按钮控制 LED",
    "description": "按钮控制 LED"
  },
  "compile": {
    "template": "使用 Arduino MCP server 的 compile_sketch 工具编译 {sketch_path}",
    "description": "编译项目"
  },
  "upload": {
    "template": "使用 Arduino MCP server 的 upload_sketch 工具上传 {sketch_path}",
    "description": "上传到硬件"
  },
  "monitor": {
    "template": "使用 Arduino MCP server 的 monitor_serial 工具监控 {port} 端口",
    "description": "监控串口"
  }
}
```

---

## Windows 启动脚本

### arduino-dev.bat

```batch
@echo off
REM Arduino 开发 CLI 工具启动脚本

REM 设置编码为 UTF-8
chcp 65001 >nul

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 运行 CLI 工具
python "%~dp0arduino_dev.py" %*

REM 如果出错，暂停
if errorlevel 1 pause
```

---

## 安装和使用

### 安装

```bash
# 1. 克隆或下载代码
cd arduino-cli

# 2. 安装依赖
pip install pyperclip

# 3. 添加到 PATH（可选）
# 将 arduino-cli 目录添加到系统 PATH
```

### 使用

```bash
# Windows
arduino-dev.bat

# 或直接运行 Python
python arduino_dev.py
```

---

## 错误处理

### 常见错误

1. **Kiro 未找到**
   - 提示用户手动打开 Kiro
   - 显示命令让用户复制

2. **arduino-cli 未安装**
   - 显示安装指南
   - 提供下载链接

3. **MCP Server 未配置**
   - 检查配置文件
   - 提供配置指南

4. **输入无效**
   - 友好的错误提示
   - 重新请求输入

---

## 扩展性

### 添加新板型

在 `ProjectConfig.BOARD_MAPPING` 中添加：

```python
"new_board": {
    "name": "New Board Name",
    "fqbn": "vendor:arch:board",
    "default_pin": 13
}
```

### 添加新项目类型

1. 在 `show_project_type_menu` 添加选项
2. 在 `commands.json` 添加模板
3. 在 `to_natural_language` 添加转换逻辑

---

## 测试计划

### 单元测试

- [ ] 菜单显示和选择
- [ ] 输入验证
- [ ] 配置生成
- [ ] 命令生成

### 集成测试

- [ ] 完整的新建项目流程
- [ ] Kiro 集成
- [ ] 依赖检查

### 用户测试

- [ ] 新手用户完成 LED 项目
- [ ] 体验流畅度
- [ ] 错误处理

---

## 性能目标

- CLI 启动时间: < 1 秒
- 菜单响应: 即时
- 命令生成: < 0.1 秒
- Kiro 启动: < 3 秒

---

## 安全考虑

- 输入验证防止注入
- 路径验证防止目录遍历
- 命令参数转义

---

## 未来改进

### Phase 2
- [ ] 项目管理（列表、删除、重新打开）
- [ ] 配置保存和加载
- [ ] 历史记录

### Phase 3
- [ ] Web 界面
- [ ] 远程 Kiro 支持
- [ ] 团队协作功能

---

**设计版本**: 1.0  
**最后更新**: 2026-02-01  
**状态**: 待实现
