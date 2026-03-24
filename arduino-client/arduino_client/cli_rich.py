"""Arduino Client CLI 入口 - Rich UI 版"""

import argparse
import logging
import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from . import __version__
from .client import ArduinoClient

# UI 组件
from .ui import get_console
from .ui.components import (
    render_splash,
    render_header,
    create_success_panel,
    create_error_panel,
    create_info_panel,
    create_progress,
    StepIndicator,
)

# 保持向后兼容：优先使用 Rich 版交互终端
try:
    from .interactive_rich import run_interactive_rich as run_interactive
except ImportError:
    from .interactive import run_interactive

logging.basicConfig(
    level=logging.INFO,
    format="[arduino_client] %(levelname)s: %(message)s",
    stream=sys.stdout,
)


def _print_error(message: str, hint: str = "") -> None:
    """打印错误信息"""
    console = get_console()
    console.print(create_error_panel(message, suggestions=[hint] if hint else None))


def _print_success(message: str, **kwargs) -> None:
    """打印成功信息"""
    console = get_console()
    console.print(create_success_panel(message, details=kwargs if kwargs else None))


def main() -> int:
    console = get_console()

    parser = argparse.ArgumentParser(
        prog="arduino-client",
        description="Arduino Client - AI Firmware Engineer",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-C", "--work-dir", type=Path, default=Path.cwd(), help="Working directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable DEBUG logging")
    parser.add_argument("--simple", action="store_true", help="Use simple UI (fallback)")

    sub = parser.add_subparsers(dest="cmd", required=False)

    # chat — 交互式终端（默认）
    p_chat = sub.add_parser("chat", aliases=["interactive", "i", "shell"],
                            help="Interactive session (default)")
    p_chat.set_defaults(func=_cmd_chat)

    # setup — 配置向导
    p_setup = sub.add_parser("setup", help="Interactive configuration wizard")
    p_setup.set_defaults(func=_cmd_setup)

    # gen — 生成代码
    p_gen = sub.add_parser("gen", help="Generate project from natural language")
    p_gen.add_argument("prompt", help="Requirement description")
    p_gen.add_argument("project_name", help="Project name")
    p_gen.add_argument("-o", "--output", type=Path, help="Output directory")
    p_gen.add_argument("--build", action="store_true", help="Build after generation")
    p_gen.add_argument("--flash", action="store_true", help="Flash after build")
    p_gen.add_argument("--monitor", action="store_true", help="Start serial monitor after flash")
    p_gen.add_argument("--fqbn", type=str, help="Board FQBN (e.g. arduino:avr:uno)")
    p_gen.add_argument("--sim", action="store_true", help="Simulate with Wokwi after build")
    p_gen.set_defaults(func=_cmd_gen)

    # run — 端到端自动化
    p_run = sub.add_parser("run", help="End-to-end automation (generate -> build -> flash -> verify)")
    p_run.add_argument("prompt", help="Requirement description")
    p_run.add_argument("--project-name", default="auto_project", help="Project name (default: auto_project)")
    p_run.add_argument("--fqbn", type=str, help="Board FQBN")
    p_run.add_argument("--no-flash", action="store_true", help="Skip flashing")
    p_run.add_argument("--no-verify", action="store_true", help="Skip verification")
    p_run.add_argument("--expect", type=str, help="Expected behavior for verification")
    p_run.add_argument("--max-iter", type=int, default=5, help="Maximum auto-fix iterations (default: 5)")
    p_run.set_defaults(func=_cmd_run)

    # detect — 检测板卡
    p_detect = sub.add_parser("detect", help="Detect connected Arduino boards")
    p_detect.add_argument("--type", type=str, help="Filter by board type (e.g. 'uno', 'pico')")
    p_detect.set_defaults(func=_cmd_detect)

    # build — 编译
    p_build = sub.add_parser("build", help="Build project")
    p_build.add_argument("project", type=Path, help="Project directory")
    p_build.add_argument("--fqbn", type=str, required=True, help="Board FQBN")
    p_build.add_argument("--flash", action="store_true", help="Flash after build")
    p_build.add_argument("--monitor", action="store_true", help="Start serial monitor after flash")
    p_build.set_defaults(func=_cmd_build)

    # upload — 上传
    p_upload = sub.add_parser("upload", help="Upload firmware to board")
    p_upload.add_argument("project", type=Path, help="Project directory")
    p_upload.add_argument("--fqbn", type=str, required=True, help="Board FQBN")
    p_upload.add_argument("--port", type=str, help="Serial port (auto-detect if omitted)")
    p_upload.add_argument("--monitor", action="store_true", help="Start serial monitor after upload")
    p_upload.set_defaults(func=_cmd_upload)

    # demo
    p_demo = sub.add_parser("demo", help="Run demo")
    p_demo.add_argument("scenario", choices=["blink"], help="Demo scenario")
    p_demo.add_argument("--board", type=str, default="uno", help="Board type (default: uno)")
    p_demo.add_argument("--pin", type=int, default=13, help="LED pin (default: 13)")
    p_demo.add_argument("--interval", type=int, default=1000, help="Blink interval ms (default: 1000)")
    p_demo.add_argument("--flash", action="store_true", help="Auto-flash")
    p_demo.set_defaults(func=_cmd_demo)

    # catalog — 板卡目录
    p_catalog = sub.add_parser("catalog", help="Browse Arduino board catalog")
    p_catalog.add_argument("--family", choices=["AVR", "SAMD", "MBED_RP2040", "ESP32", "NRF52", "SAM"],
                          help="Filter by family")
    p_catalog.set_defaults(func=_cmd_catalog)

    # monitor — 串口监控
    p_monitor = sub.add_parser("monitor", help="Start real-time serial monitor")
    p_monitor.add_argument("--port", type=str, help="Serial port (e.g. COM3)")
    p_monitor.add_argument("--baud", type=int, default=115200, help="Baudrate (default: 115200)")
    p_monitor.set_defaults(func=_cmd_monitor)

    # check — 环境检查
    p_check = sub.add_parser("check", help="Check toolchain and dependencies")
    p_check.set_defaults(func=_cmd_check)

    # sim — Wokwi 仿真
    p_sim = sub.add_parser("sim", help="Start Wokwi simulation")
    p_sim.add_argument("project", type=Path, help="Project directory")
    p_sim.add_argument("--fqbn", type=str, default="arduino:avr:uno", help="Board FQBN")
    p_sim.add_argument("--timeout", type=int, default=15000, help="Simulation timeout ms")
    p_sim.set_defaults(func=_cmd_sim)

    args = parser.parse_args()

    if getattr(args, "verbose", False):
        logging.getLogger("arduino_client").setLevel(logging.DEBUG)

    # --simple 回退到旧交互终端
    if getattr(args, "simple", False):
        from .interactive import run_interactive as _plain_interactive
        return _plain_interactive(Path(args.work_dir))

    # setup 和 check 不依赖 arduino-cli
    if args.cmd in ("setup", "check", "catalog"):
        if args.cmd == "setup":
            return _cmd_setup(None, args)
        elif args.cmd == "check":
            return _cmd_check(None, args)
        elif args.cmd == "catalog":
            return _cmd_catalog(None, args)

    # 无子命令时进入交互式终端
    if args.cmd is None:
        return run_interactive(Path(args.work_dir))

    # chat/interactive 命令
    if args.cmd in ("chat", "interactive", "i", "shell"):
        return run_interactive(Path(args.work_dir))

    # 其他命令需要 ArduinoClient
    from .errors import ConfigurationError
    try:
        client = ArduinoClient(work_dir=args.work_dir)
    except ConfigurationError as e:
        _print_error(str(e), "Run 'arduino-client setup' or install arduino-cli")
        return 1

    return args.func(client, args)


# ---------------------------------------------------------------------------
#  命令处理函数
# ---------------------------------------------------------------------------

def _cmd_chat(client, args) -> int:
    """交互式会话"""
    return run_interactive(Path(args.work_dir))


def _cmd_setup(client, args) -> int:
    """配置向导"""
    from .setup import setup_config
    work_dir = Path(getattr(args, "work_dir", Path.cwd()))
    success = setup_config(work_dir)
    if success:
        _print_success("Configuration saved")
    else:
        _print_error("Configuration not saved")
    return 0 if success else 1


def _cmd_gen(client: ArduinoClient, args) -> int:
    """生成代码命令"""
    console = get_console()
    from .llm_config import is_llm_configured
    from .code_generator import generate_arduino_code_fix
    from . import _paths

    if not is_llm_configured(client.work_dir):
        _print_error("LLM API not configured", "Run 'arduino-client setup' first")
        return 1

    render_header("Code Generation", subtitle=args.project_name)

    output_dir = args.output
    if output_dir is None:
        projects_dir = _paths.get_projects_dir(client.work_dir)
        output_dir = projects_dir / "arduino_projects" / args.project_name

    # 生成代码
    try:
        from .ui.components.progress import create_spinner
        with create_spinner("Generating code..."):
            project_dir, analysis = client.generate(args.prompt, args.project_name, output_dir=output_dir)
        _print_success("Project generated", path=str(project_dir))
    except Exception as e:
        _print_error(f"Generation failed: {e}")
        return 1

    # 编译
    if args.build or args.flash:
        fqbn = args.fqbn
        if not fqbn:
            from .interactive import _infer_fqbn_for_project
            fqbn = _infer_fqbn_for_project(client, args.prompt)

        console.print(f"[cyan]Building with FQBN: {fqbn}[/cyan]")
        from .interactive import _build_with_auto_fix
        if not _build_with_auto_fix(client, project_dir, args.project_name, args.prompt, fqbn):
            _print_error("Build failed after auto-fix attempts")
            return 1
        _print_success("Build successful")

        # 仿真
        if args.sim:
            return _cmd_sim_internal(project_dir, fqbn, getattr(args, "timeout", 15000))

        # 烧录
        if args.flash:
            boards = client.detect_boards()
            if not boards:
                _print_error("No board detected", "Connect an Arduino board")
                return 1
            port = boards[0].port
            result = client.upload(project_dir, fqbn, port=port)
            if result.success:
                _print_success("Upload successful", port=result.port)
                if args.monitor:
                    _start_monitor(port, console=console)
            else:
                _print_error(f"Upload failed: {result.message}")
                return 1

    return 0


def _cmd_run(client: ArduinoClient, args) -> int:
    """端到端自动化"""
    console = get_console()
    from .llm_config import is_llm_configured

    if not is_llm_configured(client.work_dir):
        _print_error("LLM API not configured", "Run 'arduino-client setup' first")
        return 1

    render_header("End-to-End Automation", subtitle=args.project_name)

    steps = ["Detect", "Generate", "Build"]
    if not args.no_flash:
        steps.append("Flash")
    if not args.no_verify:
        steps.append("Verify")

    indicator = StepIndicator(steps, console=console)

    # Step 1: Detect
    indicator.next()
    boards = []
    try:
        boards = client.detect_boards()
    except Exception:
        pass

    if boards and boards[0].fqbn:
        fqbn = args.fqbn or boards[0].fqbn
        port = boards[0].port
        console.print(f"[green][OK] Board: {boards[0].name or fqbn} @ {port}[/green]")
    else:
        from .interactive import _infer_fqbn_for_project
        fqbn = args.fqbn or _infer_fqbn_for_project(client, args.prompt)
        port = None
        console.print(f"[yellow][!] No board detected, using FQBN: {fqbn}[/yellow]")

    # Step 2: Generate
    indicator.next()
    from . import _paths
    out = _paths.get_projects_dir(client.work_dir) / "arduino_projects" / args.project_name

    try:
        proj, analysis = client.generate(
            args.prompt, args.project_name, output_dir=out, platform_hint=fqbn
        )
        console.print(f"[green][OK] Generated: {proj}[/green]")
    except Exception as e:
        _print_error(f"Generation failed: {e}")
        return 1

    # Step 3: Build
    indicator.next()
    from .interactive import _build_with_auto_fix
    if not _build_with_auto_fix(client, proj, args.project_name, args.prompt, fqbn):
        _print_error("Build failed after auto-fix attempts")
        return 1
    console.print("[green][OK] Build successful[/green]")

    # Step 4: Flash
    if not args.no_flash and port:
        indicator.next()
        upload_result = client.upload(proj, fqbn, port=port)
        if upload_result.success:
            console.print(f"[green][OK] Flashed to {upload_result.port}[/green]")
        else:
            _print_error(f"Flash failed: {upload_result.message}")
            return 1
    elif not args.no_flash and not port:
        indicator.next(success=False)
        console.print("[yellow][!] No board connected, skipping flash[/yellow]")
        # 尝试仿真
        from .simulation import create_wokwi_project, ensure_simulation_and_run
        try:
            create_wokwi_project(proj, fqbn=fqbn)
            ok, msg = ensure_simulation_and_run(proj, fqbn=fqbn, timeout_ms=15000)
            if ok:
                _print_success("Simulation completed", output=msg[:500])
            else:
                console.print(f"[yellow][!] Simulation: {msg}[/yellow]")
        except Exception as e:
            console.print(f"[dim]Simulation skipped: {e}[/dim]")

    # Step 5: Verify
    if not args.no_verify and port:
        indicator.next()
        from .monitor import Monitor
        mon = Monitor(detector=client.board_detector)
        console.print("[cyan]Capturing serial output (8s)...[/cyan]")
        try:
            serial_out = mon.capture_serial(port, 115200, duration=8, wait_before=2.0)
        except Exception:
            serial_out = ""

        if serial_out:
            console.print(Panel(
                serial_out[:2000],
                title="[cyan]Serial Output[/cyan]",
                border_style="cyan",
            ))

        if args.expect:
            if args.expect.lower() in serial_out.lower():
                _print_success("Verification passed", expected=args.expect)
            else:
                console.print(f"[yellow][!] Expected '{args.expect}' not found in output[/yellow]")
        else:
            console.print("[green][OK] Verify step complete (manual check)[/green]")
    elif not args.no_verify:
        indicator.next(success=False)

    return 0


def _cmd_detect(client: ArduinoClient, args) -> int:
    """检测板卡"""
    console = get_console()

    render_header("Board Detection")

    if args.type:
        board = client.detect_board_by_type(args.type)
        if not board:
            _print_error(f"No {args.type} board detected")
            return 1

        table = Table(title=f"Found {args.type} board", show_header=True, header_style="bold cyan")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Port", board.port)
        if board.fqbn:
            table.add_row("FQBN", board.fqbn)
        if board.name:
            table.add_row("Name", board.name)
        console.print(table)
    else:
        boards = client.detect_boards()
        if not boards:
            _print_error("No Arduino boards detected", "Connect a board and try again")
            return 1

        table = Table(
            title=f"Detected {len(boards)} board(s)",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("#", style="cyan", width=4)
        table.add_column("Port", style="green")
        table.add_column("FQBN", style="yellow")
        table.add_column("Name", style="blue")

        for i, board in enumerate(boards, 1):
            table.add_row(str(i), board.port, board.fqbn or "-", board.name or "-")

        console.print(table)

    return 0


def _cmd_build(client: ArduinoClient, args) -> int:
    """编译命令"""
    console = get_console()
    render_header("Build", subtitle=args.fqbn)

    project_dir = Path(args.project)
    if not project_dir.is_absolute():
        project_dir = client.work_dir / project_dir
    project_dir = project_dir.resolve()

    try:
        from .ui.components.progress import create_spinner
        with create_spinner(f"Building ({args.fqbn})..."):
            result = client.build(project_dir, args.fqbn)

        if result.success:
            _print_success("Build successful", build_path=str(result.build_path))

            if args.flash:
                boards = client.detect_boards()
                if not boards:
                    _print_error("No board detected")
                    return 1
                upload_result = client.upload(project_dir, args.fqbn, port=boards[0].port)
                if upload_result.success:
                    _print_success("Upload successful", port=upload_result.port)
                    if args.monitor:
                        _start_monitor(boards[0].port, console=console)
                else:
                    _print_error(f"Upload failed: {upload_result.message}")
                    return 1
        else:
            _print_error(f"Build failed:\n{result.output[:500]}")
            return 1
    except Exception as e:
        _print_error(f"Build error: {e}")
        return 1

    return 0


def _cmd_upload(client: ArduinoClient, args) -> int:
    """上传命令"""
    console = get_console()
    render_header("Upload", subtitle=args.fqbn)

    project_dir = Path(args.project)
    if not project_dir.is_absolute():
        project_dir = client.work_dir / project_dir
    project_dir = project_dir.resolve()

    try:
        result = client.upload(project_dir, args.fqbn, port=args.port)
        if result.success:
            _print_success("Upload successful", port=result.port)
            if args.monitor:
                _start_monitor(result.port, console=console)
        else:
            _print_error(f"Upload failed: {result.message}")
            return 1
    except Exception as e:
        _print_error(f"Upload error: {e}")
        return 1

    return 0


def _cmd_demo(client: ArduinoClient, args) -> int:
    """Demo 命令"""
    console = get_console()

    if args.scenario == "blink":
        render_header("Blink Demo", subtitle=f"{args.board} pin {args.pin}")

        try:
            with create_progress() as progress:
                task = progress.add_task("Running demo...", total=100)
                project_dir = client.demo_blink(
                    board_type=args.board,
                    pin=args.pin,
                    interval=args.interval,
                    flash=args.flash,
                )
                progress.update(task, completed=100)

            _print_success("Demo completed!", path=str(project_dir))
            return 0
        except Exception as e:
            _print_error(str(e))
            return 1

    return 1


def _cmd_catalog(client, args) -> int:
    """板卡目录"""
    console = get_console()
    render_header("Board Catalog")

    from .ui.board_catalog import BoardCatalog
    catalog = BoardCatalog(console=console)

    if getattr(args, "family", None):
        catalog.filter(args.family)

    catalog.interactive_select()
    return 0


def _cmd_monitor(client, args) -> int:
    """串口监控"""
    console = get_console()

    if getattr(args, "port", None):
        # 直接连接指定端口
        _start_monitor(args.port, args.baud, console=console)
    else:
        # 自动检测
        if client:
            try:
                boards = client.detect_boards()
                if boards:
                    port = boards[0].port
                    console.print(f"[green][OK] Auto-detected: {boards[0].name or 'Board'} @ {port}[/green]")
                    _start_monitor(port, getattr(args, "baud", 115200), console=console)
                    return 0
            except Exception:
                pass

        _print_error("No port specified and no board detected",
                     "Use --port COM3 or connect a board")
        return 1

    return 0


def _cmd_check(client, args) -> int:
    """环境检查"""
    console = get_console()

    render_header("Environment Check")

    table = Table(
        title="Toolchain Status",
        border_style="cyan",
        show_header=True,
    )
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")

    # 检查 arduino-cli
    arduino_cli = shutil.which("arduino-cli")
    if arduino_cli:
        table.add_row("arduino-cli", "[green]OK[/green]", arduino_cli)
    else:
        table.add_row("arduino-cli", "[red]Missing[/red]", "Run 'arduino-client setup' or install manually")

    # 检查 Python
    import platform
    table.add_row("Python", "[green]OK[/green]", f"{platform.python_version()}")

    # 检查 openai
    try:
        import openai
        table.add_row("openai", "[green]OK[/green]", "Installed")
    except ImportError:
        table.add_row("openai", "[red]Missing[/red]", "pip install openai")

    # 检查 pyserial
    try:
        import serial
        table.add_row("pyserial", "[green]OK[/green]", "Installed")
    except ImportError:
        table.add_row("pyserial", "[red]Missing[/red]", "pip install pyserial")

    # 检查 rich
    try:
        from importlib.metadata import version as pkg_version
        rich_ver = pkg_version("rich")
        table.add_row("rich", "[green]OK[/green]", rich_ver)
    except Exception:
        table.add_row("rich", "[yellow]Optional[/yellow]", "pip install rich")

    # 检查 LLM 配置
    from .llm_config import is_llm_configured
    work_dir = Path(getattr(args, "work_dir", Path.cwd()))
    if is_llm_configured(work_dir):
        table.add_row("LLM API", "[green]Configured[/green]", ".env loaded")
    else:
        table.add_row("LLM API", "[yellow]Not configured[/yellow]", "Run 'arduino-client setup'")

    # 检查 wokwi-cli
    wokwi = shutil.which("wokwi-cli")
    if wokwi:
        table.add_row("wokwi-cli", "[green]OK[/green]", wokwi)
    else:
        table.add_row("wokwi-cli", "[dim]Optional[/dim]", "For simulation support")

    console.print(table)
    return 0


def _cmd_sim(client: ArduinoClient, args) -> int:
    """Wokwi 仿真"""
    console = get_console()
    render_header("Wokwi Simulation", subtitle=args.fqbn)

    project_dir = Path(args.project)
    if not project_dir.is_absolute():
        project_dir = client.work_dir / project_dir
    project_dir = project_dir.resolve()

    return _cmd_sim_internal(project_dir, args.fqbn, args.timeout)


def _cmd_sim_internal(project_dir: Path, fqbn: str, timeout_ms: int = 15000) -> int:
    """仿真内部实现"""
    console = get_console()
    from .simulation import create_wokwi_project, ensure_simulation_and_run

    try:
        create_wokwi_project(project_dir, fqbn=fqbn)
        ok, msg = ensure_simulation_and_run(project_dir, fqbn=fqbn, timeout_ms=timeout_ms)
        if ok:
            _print_success("Simulation completed")
            console.print(Panel(msg, title="[cyan]Serial Output[/cyan]", border_style="cyan"))
        else:
            _print_error(f"Simulation failed: {msg}",
                        "Install wokwi-cli and set WOKWI_CLI_TOKEN")
            return 1
    except Exception as e:
        _print_error(f"Simulation error: {e}")
        return 1

    return 0


# ---------------------------------------------------------------------------
#  辅助函数
# ---------------------------------------------------------------------------

def _start_monitor(port: str, baud: int = 115200, console: Console = None) -> None:
    """启动串口监视器"""
    console = console or get_console()

    from .ui.serial_monitor import SerialMonitor

    monitor = SerialMonitor(console=console)
    if monitor.connect(port, baud):
        console.print(f"[green][OK] Connected to {port} @ {baud} baud[/green]")
        console.print("[dim]Press Ctrl+C to stop monitoring[/dim]\n")

        try:
            monitor.start_live(refresh_rate=10)
        except KeyboardInterrupt:
            console.print("\n[yellow][!] Monitoring stopped[/yellow]")
        finally:
            monitor.disconnect()
            console.print("[green][OK] Disconnected[/green]")
    else:
        console.print(f"[red][X] Failed to connect to {port}[/red]")


if __name__ == "__main__":
    sys.exit(main())
