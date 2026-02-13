"""
Arduino Client 交互式终端
类似可停留的客户端，菜单驱动 + 可选命令输入
"""
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .setup import setup_config
from .llm_config import is_llm_configured


def _has_rich() -> bool:
    try:
        import rich  # noqa: F401
        return True
    except ImportError:
        return False


def _print_banner(work_dir: Path):
    """显示欢迎与 env 配置状态"""
    llm_ok = is_llm_configured(work_dir)
    if _has_rich():
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        status = "[green]已配置[/green]" if llm_ok else "[yellow]未配置，请选 1 配置[/yellow]"
        console.print(Panel.fit(
            f"[bold cyan]Arduino Client[/bold cyan] v{__version__} — 交互式终端\n"
            f"LLM API（.env）: {status}\n"
            "输入数字选择操作，或输入 [cyan]help[/cyan] / [cyan]exit[/cyan]",
            border_style="cyan"
        ))
    else:
        print("=" * 50)
        print(f"Arduino Client v{__version__} — 交互式终端")
        print("LLM API（.env）: " + ("已配置" if llm_ok else "未配置，请选 1 配置"))
        print("输入数字选择操作，或 help / exit")
        print("=" * 50)


def _print_menu(work_dir: Path, has_client: bool):
    """显示菜单，并自动检测 env 是否已配置"""
    llm_ok = is_llm_configured(work_dir)
    opt1 = "配置 LLM API（API Key、Base URL、模型）"
    opt1_suffix = " [已配置]" if llm_ok else " [未配置]"
    if _has_rich():
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold cyan")
        table.add_column(style="white")
        table.add_row("1", opt1 + (" [green]已配置[/green]" if llm_ok else " [yellow]未配置[/yellow]"))
        table.add_row("2", "检测板卡" + ("" if has_client else " [需先安装 arduino-cli]"))
        table.add_row("3", "生成代码（自然语言 → 工程）")
        table.add_row("4", "编译工程")
        table.add_row("5", "上传固件")
        table.add_row("6", "Demo: Blink")
        table.add_row("7", "退出")
        console.print(table)
        console.print(f"[dim]工作目录: {work_dir}[/dim]")
    else:
        print("1. " + opt1 + opt1_suffix)
        print("2. 检测板卡" + ("" if has_client else " (需先安装 arduino-cli)"))
        print("3. 生成代码（自然语言 → 工程）")
        print("4. 编译工程")
        print("5. 上传固件")
        print("6. Demo: Blink")
        print("7. 退出")
        print(f"工作目录: {work_dir}")


def _prompt(text: str = "请选择") -> str:
    try:
        return input(f"\n{text} [1-7 / help / exit]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return "exit"


def run_interactive(work_dir: Optional[Path] = None) -> int:
    """运行交互式终端"""
    work_dir = Path(work_dir or Path.cwd())
    client = None  # 延迟创建，避免未安装 arduino-cli 时无法进入交互

    _print_banner(work_dir)

    while True:
        try:
            has_client = client is not None
            _print_menu(work_dir, has_client)
            choice = _prompt()

            if not choice:
                continue
            if choice.lower() in ("exit", "quit", "q", "7"):
                if _has_rich():
                    from rich.console import Console
                    Console().print("[cyan]再见[/cyan]")
                else:
                    print("再见")
                return 0
            if choice.lower() == "help":
                print("输入 1-7 执行对应操作，exit 退出。")
                continue

            # 1 — 配置 API
            if choice == "1":
                success = setup_config(work_dir)
                if _has_rich():
                    from rich.console import Console
                    c = Console()
                    if success:
                        c.print("[green]配置已保存[/green]")
                    else:
                        c.print("[yellow]未保存或失败[/yellow]")
                else:
                    print("配置已保存" if success else "未保存或失败")
                continue

            # 2–6 需要 ArduinoClient
            if client is None:
                try:
                    from .client import ArduinoClient
                    client = ArduinoClient(work_dir=work_dir)
                except Exception as e:
                    if _has_rich():
                        from rich.console import Console
                        Console().print(f"[red]需要 arduino-cli: {e}[/red]")
                        Console().print("[dim]可先使用 1 配置 API，或安装 arduino-cli 后重试[/dim]")
                    else:
                        print(f"需要 arduino-cli: {e}")
                        print("可先使用 1 配置 API，或安装 arduino-cli 后重试")
                    continue

            # 2 — 检测板卡
            if choice == "2":
                try:
                    boards = client.detect_boards()
                    if _has_rich():
                        from rich.console import Console
                        from rich.table import Table
                        c = Console()
                        if not boards:
                            c.print("[yellow]未检测到板卡[/yellow]")
                        else:
                            t = Table(title=f"检测到 {len(boards)} 个板卡")
                            t.add_column("串口", style="cyan")
                            t.add_column("FQBN", style="green")
                            t.add_column("名称", style="white")
                            for b in boards:
                                t.add_row(b.port, b.fqbn or "-", b.name or "-")
                            c.print(t)
                    else:
                        if not boards:
                            print("未检测到板卡")
                        else:
                            for i, b in enumerate(boards, 1):
                                print(f"{i}. {b.port}  FQBN: {b.fqbn or '-'}  名称: {b.name or '-'}")
                except Exception as e:
                    print(f"检测失败: {e}", file=sys.stderr)
                continue

            # 3 — 生成代码
            if choice == "3":
                if not is_llm_configured(work_dir):
                    print("请先执行 1 配置 LLM API")
                    continue
                prompt = input("描述需求（如：用 Arduino Uno 做 LED 闪烁，13 号引脚）: ").strip()
                if not prompt:
                    continue
                name = input("项目名称（默认: my_sketch）: ").strip() or "my_sketch"
                try:
                    from . import _paths
                    out = _paths.get_projects_dir(work_dir) / "arduino_projects" / name
                    proj = client.generate(prompt, name, output_dir=out)
                    print(f"已生成: {proj}")
                except Exception as e:
                    print(f"生成失败: {e}", file=sys.stderr)
                continue

            # 4 — 编译
            if choice == "4":
                path = input("工程目录或名称（如 arduino_projects/my_sketch）: ").strip()
                if not path:
                    continue
                from . import _paths
                projects_dir = _paths.get_projects_dir(work_dir) / "arduino_projects"
                proj_dir = Path(path) if Path(path).is_absolute() else projects_dir / path
                proj_dir = proj_dir.resolve()
                fqbn = input("FQBN（默认 arduino:avr:uno）: ").strip() or "arduino:avr:uno"
                try:
                    result = client.build(proj_dir, fqbn)
                    if result.success:
                        print(f"编译成功: {result.build_path}")
                    else:
                        print(f"编译失败: {result.output[:500]}")
                except Exception as e:
                    print(f"编译错误: {e}", file=sys.stderr)
                continue

            # 5 — 上传
            if choice == "5":
                path = input("工程目录或名称: ").strip()
                if not path:
                    continue
                from . import _paths
                projects_dir = _paths.get_projects_dir(work_dir) / "arduino_projects"
                proj_dir = Path(path) if Path(path).is_absolute() else projects_dir / path
                proj_dir = proj_dir.resolve()
                fqbn = input("FQBN（默认 arduino:avr:uno）: ").strip() or "arduino:avr:uno"
                try:
                    result = client.upload(proj_dir, fqbn)
                    if result.success:
                        print(f"上传成功: {result.port}")
                    else:
                        print(f"上传失败: {result.message}")
                except Exception as e:
                    print(f"上传错误: {e}", file=sys.stderr)
                continue

            # 6 — Demo Blink
            if choice == "6":
                try:
                    proj_dir = client.demo_blink(board_type="uno", pin=13, interval=1000, flash=True)
                    print(f"Demo 完成: {proj_dir}")
                except Exception as e:
                    print(f"Demo 失败: {e}", file=sys.stderr)
                continue

            if _has_rich():
                from rich.console import Console
                Console().print("[yellow]请输入 1-7 或 help/exit[/yellow]")
            else:
                print("请输入 1-7 或 help/exit")

        except KeyboardInterrupt:
            print("\n再见")
            return 0
