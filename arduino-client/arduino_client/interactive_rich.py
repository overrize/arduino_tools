"""
Arduino Client 交互式终端 - Rich UI 版

对标 STLoop chat_rich.py 的端到端线性流水线。

流程：
1. 显示启动画面
2. 检查 LLM 配置（未配置则引导）
3. 输入需求（自然语言）
4. 自动检测板卡
5. 生成代码（带进度）
6. 编译（带自动修复）
7. 板卡已连接 → 烧录 → 串口验证 → 调试循环
   无板卡 → 提醒用户 → Wokwi 仿真
"""

import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text

from . import __version__
from .llm_config import is_llm_configured
from .errors import ConfigurationError

# UI 组件
from .ui import get_console
from .ui.components import (
    render_splash,
    render_header,
    create_success_panel,
    create_error_panel,
    create_info_panel,
    create_code_panel,
    StepIndicator,
)
from .ui.components.progress import create_spinner
from .ui.theme import BRAND_COLOR, BRAND_DIM


# ---------------------------------------------------------------------------
#  Step 1: LLM 配置向导（内嵌，不弹菜单）
# ---------------------------------------------------------------------------

def _setup_if_needed(console: Console, work_dir: Path) -> bool:
    """检查 LLM 配置，未配置则引导配置。返回 True 表示已配置。"""
    if is_llm_configured(work_dir):
        return True

    console.print("[yellow][!] LLM API not configured[/yellow]")
    console.print("[dim]You need an LLM API to generate Arduino code.[/dim]\n")

    from .setup import setup_config
    success = setup_config(work_dir)

    if not success:
        console.print("[yellow][!] Configuration cancelled.[/yellow]")
        console.print("[dim]Run 'arduino-client setup' later to configure.[/dim]")
        return False

    # 验证配置生效
    return is_llm_configured(work_dir)


# ---------------------------------------------------------------------------
#  Step 2: 确保 arduino-cli 可用
# ---------------------------------------------------------------------------

def _ensure_client(work_dir: Path, console: Console):
    """延迟创建 ArduinoClient，未安装 arduino-cli 时引导安装。"""
    from .client import ArduinoClient
    from .installer import install_arduino_cli

    try:
        return ArduinoClient(work_dir=work_dir)
    except ConfigurationError as e:
        error_msg = str(e)
        is_cli_missing = (
            "未找到 arduino-cli" in error_msg or "arduino-cli" in error_msg.lower()
        )

        console.print(f"[yellow][!] {e}[/yellow]")

        if is_cli_missing:
            try:
                if Confirm.ask(f"[{BRAND_COLOR}][>] Auto-install arduino-cli?[/{BRAND_COLOR}]",
                               default=True):
                    with create_spinner("Installing arduino-cli..."):
                        success, msg = install_arduino_cli()
                    if success:
                        console.print(create_success_panel(msg))
                        console.print("[dim]Please restart terminal then retry.[/dim]")
                    else:
                        console.print(f"[yellow][!] {msg}[/yellow]")
            except (EOFError, KeyboardInterrupt):
                pass

        return None


# ---------------------------------------------------------------------------
#  Step 3-7: 端到端管道
# ---------------------------------------------------------------------------

def _run_e2e_pipeline(client, work_dir: Path, console: Console) -> int:
    """端到端管道：输入需求 → 检测板卡 → 生成 → 编译 → 烧录/仿真 → 验证"""
    from . import _paths
    from .code_generator import generate_arduino_code_fix, extract_includes_from_code
    from .code_generator import review_and_patch_code
    from .builder import Builder
    from .monitor import Monitor
    from .simulation import create_wokwi_project, ensure_simulation_and_run

    # ── Step 3: 输入需求 ──
    console.print(f"\n[bold {BRAND_COLOR}]Describe Your Requirement[/bold {BRAND_COLOR}]")
    console.print(
        Panel(
            "Examples:\n"
            "  - LED blink on pin 13 using Arduino Uno\n"
            "  - Pico reads DHT11 sensor, prints to Serial\n"
            "  - ESP32 WiFi web server controlling an LED",
            border_style="dim",
        )
    )

    try:
        requirement = Prompt.ask(f"[{BRAND_COLOR}][>] Your requirement[/{BRAND_COLOR}]")
    except (EOFError, KeyboardInterrupt):
        console.print("[dim]Cancelled.[/dim]")
        return 0

    if not requirement or requirement.strip().lower() in ("quit", "exit", "q"):
        console.print("[dim]Exited.[/dim]")
        return 0
    requirement = requirement.strip()

    try:
        project_name = Prompt.ask(
            f"[{BRAND_COLOR}][>] Project name[/{BRAND_COLOR}]",
            default="my_sketch",
        )
    except (EOFError, KeyboardInterrupt):
        project_name = "my_sketch"
    project_name = project_name.strip() or "my_sketch"

    # ── Step 4: 自动检测板卡 ──
    console.print(f"\n[bold {BRAND_COLOR}]Detecting Hardware[/bold {BRAND_COLOR}]")

    boards = []
    try:
        boards = client.detect_boards()
    except Exception:
        pass

    if boards and boards[0].fqbn:
        board = boards[0]
        fqbn = board.fqbn
        port = board.port
        console.print(f"[green][OK] Board: {board.name or fqbn} @ {port}[/green]")
    else:
        board = None
        port = None
        # 从需求推断 FQBN
        from .interactive import _infer_fqbn_for_project
        fqbn = _infer_fqbn_for_project(client, requirement)
        console.print(f"[yellow][!] No board detected[/yellow]")
        console.print(f"[dim]Inferred FQBN from requirement: {fqbn}[/dim]")

    console.print(f"[dim]Target: {fqbn}[/dim]")

    # ── Step 5: 生成代码 ──
    console.print(f"\n[bold {BRAND_COLOR}]Generating Code[/bold {BRAND_COLOR}]")

    out = _paths.get_projects_dir(work_dir) / "arduino_projects" / project_name
    sketch_file = out / f"{project_name}.ino"

    if sketch_file.exists():
        # 项目已存在 → 审查是否满足需求
        existing_code = sketch_file.read_text(encoding="utf-8")
        console.print(f"[dim]Project exists: {sketch_file}[/dim]")
        try:
            with create_spinner("Reviewing existing code..."):
                satisfied, patched_code, reason = review_and_patch_code(
                    requirement, existing_code, fqbn, work_dir=work_dir
                )
        except Exception as rev_err:
            console.print(f"[dim]Review failed ({rev_err}), regenerating...[/dim]")
            satisfied, patched_code, reason = False, None, ""

        if satisfied:
            console.print(f"[green][OK] Existing code satisfies requirement: {reason}[/green]")
        elif patched_code:
            console.print(f"[green][OK] Patched: {reason}[/green]")
            sketch_file.write_text(patched_code, encoding="utf-8")
        else:
            console.print(f"[dim]Regenerating: {reason}[/dim]")
            try:
                with create_spinner("Querying AI Agent..."):
                    proj, analysis = client.generate(
                        requirement, project_name, output_dir=out, platform_hint=fqbn
                    )
            except Exception as e:
                console.print(create_error_panel(f"Generation failed: {e}"))
                return 1
    else:
        try:
            with create_spinner("Querying AI Agent..."):
                proj, analysis = client.generate(
                    requirement, project_name, output_dir=out, platform_hint=fqbn
                )
            console.print(create_success_panel("Code generated", details={"Path": str(out)}))
        except Exception as e:
            console.print(create_error_panel(f"Generation failed: {e}"))
            return 1

    # 预览生成的代码
    if sketch_file.exists():
        code = sketch_file.read_text(encoding="utf-8")
        preview_lines = code.split("\n")[:25]
        preview = "\n".join(preview_lines)
        if len(code.split("\n")) > 25:
            preview += "\n..."
        console.print(create_code_panel(preview, language="cpp", title=f"{project_name}.ino (preview)"))

    # ── Step 6: 编译（带自动修复）──
    console.print(f"\n[bold {BRAND_COLOR}]Building[/bold {BRAND_COLOR}]")

    fix_prompt = f"{requirement}\n【目标平台 FQBN: {fqbn}，请确保代码兼容该平台 API。】"
    max_fix_rounds = 3
    lib_install_attempted = False
    fix_round = 0
    build_ok = False

    while fix_round <= max_fix_rounds:
        label = "Recompiling" if (fix_round > 0 or lib_install_attempted) else "Compiling"

        try:
            with create_spinner(f"{label} ({fqbn})..."):
                result = client.build(out, fqbn)
        except Exception as build_exc:
            console.print(create_error_panel(f"Build exception: {build_exc}"))
            break

        if result.success:
            console.print(create_success_panel("Build successful", details={"Output": str(result.build_path)}))
            build_ok = True
            break

        full_output = result.output or ""
        error_summary = Builder.extract_error_lines(full_output)
        console.print(f"[red][X] Build failed (attempt {fix_round + 1}/{max_fix_rounds + 1}):[/red]")
        console.print(f"[dim]{error_summary[:500]}[/dim]")

        # 检测缺库
        if not lib_install_attempted:
            missing = Builder.detect_missing_libraries(full_output)
            if missing:
                console.print(f"[cyan][>] Auto-installing libraries: {', '.join(missing)}[/cyan]")
                client.builder.install_libraries(missing)
                lib_install_attempted = True
                continue

        lib_install_attempted = True

        if fix_round >= max_fix_rounds:
            console.print(f"[red][X] Max fix rounds ({max_fix_rounds}) reached[/red]")
            break

        # LLM 修复
        try:
            current_code = sketch_file.read_text(encoding="utf-8")
            with create_spinner(f"AI fix round {fix_round + 1}..."):
                fixed = generate_arduino_code_fix(
                    fix_prompt, current_code, error_summary, work_dir=work_dir
                )
            sketch_file.write_text(fixed, encoding="utf-8")
            fix_round += 1
            console.print(f"[green][OK] Code fixed (round {fix_round})[/green]")
        except Exception as fix_e:
            console.print(create_error_panel(f"Fix failed: {fix_e}"))
            break

    if not build_ok:
        console.print(create_error_panel(
            "Build failed after all attempts.",
            suggestions=[
                f"Project: {out}",
                "Check the .ino file for errors",
                "Run 'arduino-client check' to verify toolchain",
            ],
        ))
        return 1

    # ── Step 7: 部署 ──
    console.print(f"\n[bold {BRAND_COLOR}]Deploy & Test[/bold {BRAND_COLOR}]")

    if board and port:
        # ── 有板卡：自动烧录 ──
        console.print(f"[green][OK] Board connected: {board.name or fqbn} @ {port}[/green]")
        console.print("[cyan]Flashing...[/cyan]")

        upload_result = client.upload(out, fqbn, port=port)
        if upload_result.success:
            console.print(create_success_panel("Flash completed!", details={"Port": upload_result.port}))

            # ── 串口验证 + 调试循环 ──
            _serial_verify_loop(client, out, project_name, requirement, fqbn, port, console)
        else:
            console.print(create_error_panel(f"Flash failed: {upload_result.message}"))
            # 烧录失败 → 提供仿真选项
            if Confirm.ask(f"\n[{BRAND_COLOR}][>] Try Wokwi simulation instead?[/{BRAND_COLOR}]",
                           default=True):
                _run_simulation(out, fqbn, console)
    else:
        # ── 无板卡：提醒 + 自动仿真 ──
        console.print("[yellow][!] No board connected[/yellow]")
        console.print("[dim]Connect an Arduino board to flash firmware.[/dim]")
        console.print("[dim]Starting Wokwi simulation instead...[/dim]\n")

        _run_simulation(out, fqbn, console)

    return 0


# ---------------------------------------------------------------------------
#  串口验证 + 调试循环
# ---------------------------------------------------------------------------

def _serial_verify_loop(client, proj_dir, project_name, requirement, fqbn, port, console):
    """烧录后的串口验证和交互式调试循环。"""
    from .monitor import Monitor
    from .code_generator import diagnose_with_serial, generate_arduino_code_fix
    from .builder import Builder

    mon = Monitor(detector=client.board_detector)
    sketch = proj_dir / f"{project_name}.ino"

    # 采集串口
    console.print(f"\n[cyan]Capturing serial output ({port} @ 115200, 8s)...[/cyan]")
    try:
        serial_out = mon.capture_serial(port, 115200, duration=8, wait_before=2.0)
    except Exception as e:
        console.print(f"[yellow][!] Serial capture failed: {e}[/yellow]")
        return

    if serial_out:
        console.print(Panel(
            serial_out[:2000] + ("..." if len(serial_out) > 2000 else ""),
            title="[cyan]Serial Output[/cyan]",
            border_style="cyan",
        ))
    else:
        console.print("[dim]No serial output (MCU may not use Serial or baud mismatch)[/dim]")

    # 调试循环
    max_rounds = 5
    hw_info = f"FQBN: {fqbn}, Port: {port}\nRequirement: {requirement}"

    for r in range(max_rounds):
        try:
            issue = Prompt.ask(
                f"\n[{BRAND_COLOR}][>] Working correctly? (Enter=yes / describe issue)[/{BRAND_COLOR}]",
                default="",
                show_default=False,
            )
        except (EOFError, KeyboardInterrupt):
            break

        if not issue.strip():
            console.print(create_success_panel("Verification passed!"))
            return

        # LLM 诊断
        current_code = sketch.read_text(encoding="utf-8")
        console.print(f"[cyan]Diagnosing (round {r + 1}/{max_rounds})...[/cyan]")

        try:
            with create_spinner("AI diagnosing..."):
                diagnosis, changes, fixed_code = diagnose_with_serial(
                    current_code, serial_out, issue.strip(),
                    hardware_info=hw_info, work_dir=client.work_dir,
                )
        except Exception as e:
            console.print(f"[yellow][!] Diagnosis failed: {e}[/yellow]")
            continue

        console.print(f"[dim]Diagnosis: {diagnosis}[/dim]")
        if changes:
            console.print(f"[dim]Changes: {changes}[/dim]")

        if not fixed_code:
            console.print("[yellow][!] No fix code returned[/yellow]")
            continue

        # 写入修复代码 → 编译 → 烧录
        sketch.write_text(fixed_code, encoding="utf-8")

        try:
            with create_spinner("Rebuilding..."):
                build_result = client.build(proj_dir, fqbn)
        except Exception:
            console.print("[red][X] Rebuild failed[/red]")
            sketch.write_text(current_code, encoding="utf-8")
            continue

        if not build_result.success:
            console.print("[red][X] Rebuild failed, reverting[/red]")
            sketch.write_text(current_code, encoding="utf-8")
            continue

        upload_result = client.upload(proj_dir, fqbn, port=port)
        if not upload_result.success:
            console.print(f"[red][X] Upload failed: {upload_result.message}[/red]")
            continue

        console.print("[green][OK] Fixed code uploaded[/green]")

        # 重新采集串口
        console.print("[cyan]Recapturing serial output...[/cyan]")
        try:
            serial_out = mon.capture_serial(port, 115200, duration=8, wait_before=2.0)
        except Exception:
            serial_out = ""

        if serial_out:
            console.print(Panel(serial_out[:2000], title="[cyan]Serial Output[/cyan]", border_style="cyan"))
        else:
            console.print("[dim]No serial output[/dim]")

    console.print(f"[dim]Max debug rounds ({max_rounds}) reached.[/dim]")


# ---------------------------------------------------------------------------
#  Wokwi 仿真
# ---------------------------------------------------------------------------

def _run_simulation(proj_dir: Path, fqbn: str, console: Console):
    """运行 Wokwi 仿真"""
    from .simulation import create_wokwi_project, ensure_simulation_and_run

    try:
        create_wokwi_project(proj_dir, fqbn=fqbn)
        console.print("[cyan]Running Wokwi simulation...[/cyan]")

        ok, msg = ensure_simulation_and_run(proj_dir, fqbn=fqbn, timeout_ms=15000)
        if ok:
            console.print(create_success_panel("Simulation completed"))
            console.print(Panel(msg, title="[cyan]Serial Output[/cyan]", border_style="cyan"))
        else:
            console.print(f"[yellow][!] Simulation: {msg}[/yellow]")
            console.print("[dim]Tip: install wokwi-cli and set WOKWI_CLI_TOKEN[/dim]")
    except Exception as e:
        console.print(f"[yellow][!] Simulation skipped: {e}[/yellow]")
        console.print("[dim]Code is compiled. Connect a board to flash, or install wokwi-cli to simulate.[/dim]")


# ---------------------------------------------------------------------------
#  入口
# ---------------------------------------------------------------------------

def run_interactive_rich(work_dir: Optional[Path] = None) -> int:
    """运行端到端交互式管道"""
    work_dir = Path(work_dir or Path.cwd())
    console = get_console()

    # 1. 启动画面
    try:
        console.clear()
    except Exception:
        pass
    render_splash(console)

    # 2. 检查 LLM 配置
    if not _setup_if_needed(console, work_dir):
        return 1

    # 3. 确保 arduino-cli 可用
    client = _ensure_client(work_dir, console)
    if client is None:
        return 1

    # 4-7. 端到端管道（可循环）
    while True:
        ret = _run_e2e_pipeline(client, work_dir, console)

        try:
            again = Confirm.ask(
                f"\n[{BRAND_COLOR}][>] Start another project?[/{BRAND_COLOR}]",
                default=False,
            )
        except (EOFError, KeyboardInterrupt):
            break

        if not again:
            break

    console.print(f"\n[{BRAND_COLOR}]Bye![/{BRAND_COLOR}]")
    return 0
