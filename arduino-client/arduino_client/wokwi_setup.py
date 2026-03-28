"""Wokwi CLI Token 自动检测和配置模块

自动检测 WOKWI_CLI_TOKEN 环境变量，若未设置则引导用户输入并持久化保存。
支持从 ~/.wokwi/env 文件读取和保存 token。
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# 默认配置路径
DEFAULT_WOKWI_CONFIG_DIR = Path.home() / ".wokwi"
DEFAULT_WOKWI_ENV_FILE = DEFAULT_WOKWI_CONFIG_DIR / "env"


def get_wokwi_token() -> Optional[str]:
    """获取 Wokwi CLI Token

    查找顺序:
    1. 环境变量 WOKWI_CLI_TOKEN
    2. ~/.wokwi/env 文件中的 WOKWI_CLI_TOKEN

    Returns:
        Token 字符串，如果未找到则返回 None
    """
    # 1. 检查环境变量
    token = os.environ.get("WOKWI_CLI_TOKEN")
    if token:
        return token

    # 2. 检查配置文件
    if DEFAULT_WOKWI_ENV_FILE.exists():
        try:
            content = DEFAULT_WOKWI_ENV_FILE.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("WOKWI_CLI_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip("\"'")
                    if token:
                        # 同时设置到环境变量，供当前进程使用
                        os.environ["WOKWI_CLI_TOKEN"] = token
                        return token
        except Exception:
            pass

    return None


def save_wokwi_token(token: str) -> bool:
    """保存 Wokwi CLI Token 到配置文件

    Args:
        token: Wokwi CLI Token

    Returns:
        是否成功保存
    """
    try:
        # 确保配置目录存在
        DEFAULT_WOKWI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # 写入 token
        env_content = f"WOKWI_CLI_TOKEN={token}\n"
        DEFAULT_WOKWI_ENV_FILE.write_text(env_content, encoding="utf-8")

        # 同时设置到环境变量
        os.environ["WOKWI_CLI_TOKEN"] = token

        return True
    except Exception:
        return False


def check_and_setup_wokwi_token(auto_setup: bool = True) -> Tuple[bool, Optional[str]]:
    """检查并设置 Wokwi CLI Token

    Args:
        auto_setup: 如果未设置 token，是否自动引导用户输入

    Returns:
        (是否成功获取 token, token 字符串或错误信息)
    """
    # 先尝试获取已有的 token
    token = get_wokwi_token()
    if token:
        return True, token

    # 未找到 token，需要用户输入
    if not auto_setup:
        return (
            False,
            "未设置 WOKWI_CLI_TOKEN。请在 https://wokwi.com/dashboard/ci 创建 token 并设置环境变量。",
        )

    # 尝试引导用户输入
    try:
        success, result = _interactive_setup()
        return success, result
    except Exception as e:
        return False, f"配置失败: {e}"


def _interactive_setup() -> Tuple[bool, Optional[str]]:
    """交互式配置 Wokwi Token

    Returns:
        (是否成功, token 或错误信息)
    """
    import shutil

    try:
        from rich.prompt import Prompt, Confirm
        from rich.panel import Panel
        from rich.align import Align
        from rich.text import Text
        from rich.console import Console

        console = Console()

        # 先检查 wokwi-cli 是否已安装
        if not shutil.which("wokwi-cli"):
            console.print(
                Panel(
                    Align.center(
                        Text.assemble(
                            ("Wokwi CLI Configuration\n", "bold cyan"),
                            ("需要先安装 wokwi-cli", "dim"),
                        )
                    ),
                    border_style="cyan",
                    padding=(1, 2),
                )
            )
            console.print("[yellow][!] 未找到 wokwi-cli[/yellow]")

            try:
                if Confirm.ask("[cyan][>] 是否自动安装 wokwi-cli?[/cyan]", default=True):
                    from .installer import install_wokwi_cli

                    with console.status("[cyan]Installing wokwi-cli...[/cyan]"):
                        success, msg = install_wokwi_cli()
                    if success:
                        console.print(f"[green][OK] {msg}[/green]")
                    else:
                        console.print(f"[yellow][!] {msg}[/yellow]")
                        console.print("[dim]可手动安装: https://docs.wokwi.com/wokwi-ci/cli-installation[/dim]")
                        return False, "wokwi-cli 安装失败"
                else:
                    return False, "用户取消安装"
            except (EOFError, KeyboardInterrupt):
                return False, "用户取消"

        # 显示提示信息
        console.print(
            Panel(
                Align.center(
                    Text.assemble(
                        ("Wokwi CLI Configuration\n", "bold cyan"),
                        ("仿真功能需要 Wokwi CLI Token", "dim"),
                    )
                ),
                border_style="cyan",
                padding=(1, 2),
            )
        )

        console.print("\n[dim]请在 https://wokwi.com/dashboard/ci 创建 token[/dim]")
        console.print("[dim]步骤: 登录 Wokwi → 访问 CI Dashboard → 创建 Token[/dim]\n")

        # 询问是否已有 token
        has_token = Confirm.ask("[>] 是否已有 Wokwi CLI Token?", default=False)
        if not has_token:
            console.print("\n[yellow]请先访问 https://wokwi.com/dashboard/ci 创建 token[/yellow]")
            console.print("[dim]完成后重新运行此命令[/dim]")
            return False, "用户选择稍后配置"

        # 输入 token
        token = Prompt.ask("[>] 请输入 Wokwi CLI Token")
        token = token.strip()

        if not token:
            console.print("[red][X] Token 不能为空[/red]")
            return False, "Token 为空"

        # 验证 token 格式（简单检查）
        if len(token) < 10:
            console.print("[yellow][!] Token 长度较短，请确认输入正确[/yellow]")

        # 保存 token
        if save_wokwi_token(token):
            console.print(f"\n[green][OK] Token 已保存到 {DEFAULT_WOKWI_ENV_FILE}[/green]")
            console.print("[dim]现在可以使用 Wokwi 仿真功能了[/dim]")
            return True, token
        else:
            console.print("[red][X] 保存 Token 失败[/red]")
            return False, "保存失败"

    except ImportError:
        # Rich 不可用，使用纯文本模式
        return _interactive_setup_plain()


def _interactive_setup_plain() -> Tuple[bool, Optional[str]]:
    """纯文本版交互式配置（Rich 不可用时的 fallback）"""
    import shutil

    print("=" * 60)
    print("Wokwi CLI Configuration")
    print("=" * 60)

    # 先检查 wokwi-cli 是否已安装
    if not shutil.which("wokwi-cli"):
        print("\n[!] 未找到 wokwi-cli，需要先安装")
        install_choice = input("是否自动安装 wokwi-cli? (Y/n): ").strip().lower()
        if install_choice not in ("n", "no"):
            from .installer import install_wokwi_cli

            print("正在安装 wokwi-cli...")
            success, msg = install_wokwi_cli()
            if success:
                print(f"[OK] {msg}")
            else:
                print(f"[!] {msg}")
                print("可手动安装: https://docs.wokwi.com/wokwi-ci/cli-installation")
                return False, "wokwi-cli 安装失败"
        else:
            return False, "用户取消安装"

    print("\n仿真功能需要 Wokwi CLI Token")
    print("请在 https://wokwi.com/dashboard/ci 创建 token")
    print("步骤: 登录 Wokwi → 访问 CI Dashboard → 创建 Token\n")

    has_token = input("是否已有 Wokwi CLI Token? (y/N): ").strip().lower()
    if has_token not in ("y", "yes"):
        print("\n请先访问 https://wokwi.com/dashboard/ci 创建 token")
        print("完成后重新运行此命令")
        return False, "用户选择稍后配置"

    token = input("请输入 Wokwi CLI Token: ").strip()

    if not token:
        print("Error: Token 不能为空", file=sys.stderr)
        return False, "Token 为空"

    if len(token) < 10:
        print("Warning: Token 长度较短，请确认输入正确")

    if save_wokwi_token(token):
        print(f"\nToken 已保存到 {DEFAULT_WOKWI_ENV_FILE}")
        print("现在可以使用 Wokwi 仿真功能了")
        return True, token
    else:
        print("Error: 保存 Token 失败", file=sys.stderr)
        return False, "保存失败"


def setup_wokwi_token_cli() -> bool:
    """CLI 入口：手动配置 Wokwi Token

    Returns:
        是否成功配置
    """
    success, result = check_and_setup_wokwi_token(auto_setup=True)

    if success:
        print(f"\n当前 Token: {result[:8]}...{result[-4:] if len(result) > 12 else ''}")
        return True
    else:
        print(f"\n配置失败: {result}")
        return False


def ensure_wokwi_token_for_simulation() -> Tuple[bool, str]:
    """确保仿真前 Wokwi Token 已配置

    在启动仿真前调用，自动检测并引导配置。

    Returns:
        (是否成功, token 或错误信息)
    """
    success, token_or_msg = check_and_setup_wokwi_token(auto_setup=True)

    if success:
        return True, token_or_msg  # token_or_msg 是 token

    # 失败情况
    return False, str(token_or_msg)
