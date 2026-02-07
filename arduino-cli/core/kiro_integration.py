"""Kiro 集成"""

import subprocess
import os
from pathlib import Path
from typing import Optional


class KiroIntegration:
    """Kiro 集成类"""
    
    def __init__(self):
        self.kiro_path = self._find_kiro()
    
    def _find_kiro(self) -> Optional[str]:
        """查找 Kiro 可执行文件"""
        # 常见位置
        possible_paths = [
            r"C:\Program Files\Kiro\kiro.exe",
            r"C:\Users\{}\AppData\Local\Kiro\kiro.exe".format(os.getenv("USERNAME", "")),
            r"C:\Program Files (x86)\Kiro\kiro.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 尝试在 PATH 中查找
        try:
            result = subprocess.run(
                ["kiro", "--version"],
                capture_output=True,
                timeout=3
            )
            if result.returncode == 0:
                return "kiro"
        except:
            pass
        
        return None
    
    def generate_command(self, config) -> str:
        """生成 Kiro 命令"""
        nl_description = config.to_natural_language()
        
        # 生成完整的 Kiro 命令
        if config.project_type == "led_blink":
            command = (
                f"使用 Arduino MCP server 的 full_workflow_led_blink 工具，"
                f"{nl_description}"
            )
        else:
            command = (
                f"使用 Arduino MCP server 的 create_led_blink 工具，"
                f"{nl_description}"
            )
        
        return command
    
    def copy_to_clipboard(self, text: str) -> bool:
        """复制到剪贴板"""
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except ImportError:
            # pyperclip 未安装，尝试使用 Windows clip 命令
            try:
                process = subprocess.Popen(
                    ['clip'],
                    stdin=subprocess.PIPE,
                    shell=True
                )
                process.communicate(text.encode('utf-8'))
                return True
            except:
                return False
        except Exception:
            return False
    
    def open_in_kiro(self, config, workspace: Optional[str] = None) -> bool:
        """在 Kiro 中打开项目"""
        # 生成命令
        command = self.generate_command(config)
        
        # 显示命令
        print("\n" + "="*60)
        print("📋 生成的 Kiro 命令")
        print("="*60)
        print(f"\n{command}\n")
        print("="*60 + "\n")
        
        # 尝试复制到剪贴板
        if self.copy_to_clipboard(command):
            print("✅ 命令已复制到剪贴板")
        else:
            print("💡 请手动复制上述命令")
        
        # 如果找不到 Kiro
        if not self.kiro_path:
            print("\n❌ 未找到 Kiro 可执行文件")
            print("💡 请手动打开 Kiro 并粘贴上述命令\n")
            return False
        
        # 打开 Kiro
        print(f"\n⏳ 正在启动 Kiro...")
        try:
            if workspace:
                subprocess.Popen([self.kiro_path, workspace])
            else:
                subprocess.Popen([self.kiro_path])
            
            print(f"✅ Kiro 已启动")
            print(f"💡 请在 Kiro 中粘贴命令（Ctrl+V）\n")
            return True
        except Exception as e:
            print(f"❌ 启动 Kiro 失败: {e}")
            print(f"💡 请手动打开 Kiro 并粘贴上述命令\n")
            return False
