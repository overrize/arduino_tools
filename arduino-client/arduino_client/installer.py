"""
arduino-cli 和 wokwi-cli 自动安装模块
支持 Windows/Linux/macOS

wokwi-cli 是独立二进制，从 GitHub Releases 直接下载安装。
"""

import subprocess
import sys
import os
import platform
import shutil
import struct
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple

# wokwi-cli GitHub release 下载模板
_WOKWI_RELEASE_URL = "https://github.com/wokwi/wokwi-cli/releases/latest/download/{asset}"

# 平台 → 资产文件名映射
_WOKWI_ASSETS = {
    ("Windows", "x64"): "wokwi-cli-win-x64.exe",
    ("Linux", "x64"): "wokwi-cli-linuxstatic-x64",
    ("Linux", "arm64"): "wokwi-cli-linuxstatic-arm64",
    ("Darwin", "x64"): "wokwi-cli-macos-x64",
    ("Darwin", "arm64"): "wokwi-cli-macos-arm64",
}


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _is_linux() -> bool:
    return platform.system() == "Linux"


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def _check_command(cmd: str) -> bool:
    """检查命令是否可用"""
    return shutil.which(cmd) is not None


def _get_arch() -> str:
    """返回标准化架构: x64 或 arm64"""
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64", "x64"):
        return "x64"
    if machine in ("aarch64", "arm64"):
        return "arm64"
    # 32-bit Python on 64-bit Windows 也报 x64
    if _is_windows() and struct.calcsize("P") * 8 == 64:
        return "x64"
    return machine


def _get_install_dir() -> Path:
    """获取安装目录，确保在 PATH 上"""
    if _is_windows():
        # 优先 %LOCALAPPDATA%/Programs/wokwi-cli，其次 %USERPROFILE%/.local/bin
        local_app = os.environ.get("LOCALAPPDATA")
        if local_app:
            d = Path(local_app) / "Programs" / "wokwi-cli"
        else:
            d = Path.home() / ".local" / "bin"
    else:
        d = Path.home() / ".local" / "bin"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _add_to_path(directory: Path) -> None:
    """将目录加入当前进程 PATH（立即生效）"""
    dir_str = str(directory)
    path_env = os.environ.get("PATH", "")
    if dir_str not in path_env.split(os.pathsep):
        os.environ["PATH"] = dir_str + os.pathsep + path_env

    if _is_windows():
        # 写入用户级 PATH 注册表（永久生效）
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0,
                winreg.KEY_READ | winreg.KEY_WRITE,
            ) as key:
                try:
                    current, _ = winreg.QueryValueEx(key, "Path")
                except FileNotFoundError:
                    current = ""
                if dir_str not in current.split(";"):
                    new_path = dir_str + ";" + current if current else dir_str
                    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
        except Exception:
            pass  # 注册表写入失败不影响当前会话


def install_wokwi_cli() -> Tuple[bool, str]:
    """自动下载安装 wokwi-cli

    从 GitHub Releases 下载对应平台的二进制文件，放到用户目录下并加入 PATH。

    Returns:
        (success, message) 安装是否成功及消息
    """
    if _check_command("wokwi-cli"):
        return True, "wokwi-cli 已安装"

    system = platform.system()
    arch = _get_arch()
    asset = _WOKWI_ASSETS.get((system, arch))

    if not asset:
        return False, (
            f"不支持的平台: {system} {arch}\n"
            "请从 https://github.com/wokwi/wokwi-cli/releases 手动下载"
        )

    url = _WOKWI_RELEASE_URL.format(asset=asset)
    install_dir = _get_install_dir()
    bin_name = "wokwi-cli.exe" if _is_windows() else "wokwi-cli"
    target = install_dir / bin_name

    try:
        # 下载到临时文件再移动，避免下载中断留下残缺文件
        with tempfile.NamedTemporaryFile(
            dir=install_dir, suffix=".tmp", delete=False
        ) as tmp:
            tmp_path = Path(tmp.name)
            req = urllib.request.Request(url, headers={"User-Agent": "arduino-tools-installer"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                shutil.copyfileobj(resp, tmp)

        # 移动到最终位置
        if target.exists():
            target.unlink()
        tmp_path.rename(target)

        # 设置可执行权限 (Linux/macOS)
        if not _is_windows():
            target.chmod(0o755)

        # 确保安装目录在 PATH 上
        _add_to_path(install_dir)

        if _check_command("wokwi-cli"):
            return True, f"已安装 wokwi-cli → {target}"
        else:
            return True, f"已下载 wokwi-cli → {target}\n请重启终端使 PATH 生效"

    except urllib.error.HTTPError as e:
        return False, f"下载失败 (HTTP {e.code}): {url}"
    except urllib.error.URLError as e:
        return False, f"网络错误: {e.reason}\n请检查网络连接或从 https://github.com/wokwi/wokwi-cli/releases 手动下载"
    except Exception as e:
        # 清理临时文件
        if 'tmp_path' in locals() and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return False, f"安装失败: {e}"


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
                [
                    "winget",
                    "install",
                    "ArduinoSA.CLI",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ],
                capture_output=True,
                text=True,
                timeout=300,
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
                timeout=300,
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
            subprocess.run(["sudo", "apt-get", "update"], capture_output=True, timeout=60)
            result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", "arduino-cli"],
                capture_output=True,
                text=True,
                timeout=300,
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
                timeout=300,
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
                timeout=300,
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
                ["brew", "install", "arduino-cli"], capture_output=True, text=True, timeout=300
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
