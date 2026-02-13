"""
arduino-cli 自动安装模块
支持 Windows/Linux/macOS
"""
import subprocess
import sys
import platform
import shutil
from typing import Optional, Tuple


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _is_linux() -> bool:
    return platform.system() == "Linux"


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def _check_command(cmd: str) -> bool:
    """检查命令是否可用"""
    return shutil.which(cmd) is not None


def install_arduino_cli() -> Tuple[bool, str]:
    """尝试自动安装 arduino-cli
    
    Returns:
        (success, message) 安装是否成功及消息
    """
    if _is_windows():
        return _install_windows()
    elif _is_linux():
        return _install_linux()
    elif _is_macos():
        return _install_macos()
    else:
        return False, f"不支持的操作系统: {platform.system()}"


def _install_windows() -> Tuple[bool, str]:
    """Windows 安装（优先用 winget，其次用 choco，最后提示手动）"""
    # 1. 尝试 winget
    if _check_command("winget"):
        try:
            result = subprocess.run(
                ["winget", "install", "ArduinoSA.CLI", "--accept-package-agreements", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return True, "已通过 winget 安装 arduino-cli，请重新启动终端或刷新 PATH"
            else:
                # winget 失败，尝试 choco
                pass
        except subprocess.TimeoutExpired:
            return False, "winget 安装超时"
        except Exception as e:
            pass  # 继续尝试其他方法
    
    # 2. 尝试 choco
    if _check_command("choco"):
        try:
            result = subprocess.run(
                ["choco", "install", "arduino-cli", "-y"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return True, "已通过 Chocolatey 安装 arduino-cli，请重新启动终端或刷新 PATH"
        except subprocess.TimeoutExpired:
            return False, "choco 安装超时"
        except Exception as e:
            pass
    
    # 3. 都不行，提示手动安装
    return False, (
        "未找到 winget 或 Chocolatey。请手动安装：\n"
        "  - winget: winget install ArduinoSA.CLI\n"
        "  - 或访问: https://arduino.github.io/arduino-cli/"
    )


def _install_linux() -> Tuple[bool, str]:
    """Linux 安装（优先用包管理器）"""
    # 检测包管理器
    if _check_command("apt-get"):
        # Debian/Ubuntu
        try:
            # 先更新包列表
            subprocess.run(
                ["sudo", "apt-get", "update"],
                capture_output=True,
                timeout=60
            )
            result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", "arduino-cli"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return True, "已通过 apt-get 安装 arduino-cli"
        except subprocess.TimeoutExpired:
            return False, "apt-get 安装超时"
        except Exception as e:
            pass
    
    if _check_command("yum"):
        # RHEL/CentOS
        try:
            result = subprocess.run(
                ["sudo", "yum", "install", "-y", "arduino-cli"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return True, "已通过 yum 安装 arduino-cli"
        except subprocess.TimeoutExpired:
            return False, "yum 安装超时"
        except Exception as e:
            pass
    
    if _check_command("dnf"):
        # Fedora
        try:
            result = subprocess.run(
                ["sudo", "dnf", "install", "-y", "arduino-cli"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return True, "已通过 dnf 安装 arduino-cli"
        except subprocess.TimeoutExpired:
            return False, "dnf 安装超时"
        except Exception as e:
            pass
    
    # 都不行，提示手动安装
    return False, (
        "未找到支持的包管理器。请手动安装：\n"
        "  - 访问: https://arduino.github.io/arduino-cli/\n"
        "  - 或使用 snap: snap install arduino"
    )


def _install_macos() -> Tuple[bool, str]:
    """macOS 安装（优先用 Homebrew）"""
    if _check_command("brew"):
        try:
            result = subprocess.run(
                ["brew", "install", "arduino-cli"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return True, "已通过 Homebrew 安装 arduino-cli"
        except subprocess.TimeoutExpired:
            return False, "brew 安装超时"
        except Exception as e:
            pass
    
    # 提示手动安装
    return False, (
        "未找到 Homebrew。请手动安装：\n"
        "  - brew install arduino-cli\n"
        "  - 或访问: https://arduino.github.io/arduino-cli/"
    )
