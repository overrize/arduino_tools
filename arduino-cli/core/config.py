"""配置和依赖检查"""

import subprocess
import sys
from pathlib import Path


class DependencyChecker:
    """依赖检查器"""
    
    def check_all(self, verbose: bool = True) -> bool:
        """检查所有依赖"""
        if verbose:
            print("\n" + "="*60)
            print("🔍 检查依赖")
            print("="*60 + "\n")
        
        checks = [
            ("Python", self.check_python),
            ("arduino-cli", self.check_arduino_cli),
            ("MCP Server", self.check_mcp_server),
        ]
        
        all_ok = True
        for name, check_func in checks:
            if not check_func():
                if verbose:
                    print(f"❌ {name} 未安装或配置不正确")
                all_ok = False
            else:
                if verbose:
                    print(f"✅ {name} 已就绪")
        
        if verbose:
            print()
        
        if not all_ok and verbose:
            self.show_installation_guide()
        
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
            # 检查模块是否可导入
            result = subprocess.run(
                [sys.executable, "-c", "import arduino_mcp_server"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def show_installation_guide(self):
        """显示安装指南"""
        print("="*60)
        print("📚 安装指南")
        print("="*60)
        print("\n如果 arduino-cli 未安装：")
        print("  Windows: winget install ArduinoSA.CLI")
        print("  或访问: https://arduino.github.io/arduino-cli/\n")
        
        print("如果 MCP Server 未安装：")
        print("  cd arduino-mcp-server")
        print("  pip install -e .\n")
        
        print("="*60 + "\n")
