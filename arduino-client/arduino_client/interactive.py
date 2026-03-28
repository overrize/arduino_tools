"""
Arduino Client 交互式终端
菜单驱动，自然语言 → 自动生成/编译/烧录（或仿真）
"""

import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .setup import setup_config
from .llm_config import is_llm_configured
from .errors import ConfigurationError
from .installer import install_arduino_cli
from .simulation import create_wokwi_project, ensure_simulation_and_run
from .code_generator import (
    generate_arduino_code_fix,
    review_and_patch_code,
    extract_includes_from_code,
    diagnose_with_serial,
)
from .monitor import Monitor

FQBN_ALIASES = {
    "uno": "arduino:avr:uno",
    "nano": "arduino:avr:nano",
    "pico": "arduino:mbed_rp2040:pico",
    "rp2040": "arduino:mbed_rp2040:pico",
    "esp32": "esp32:esp32:esp32",
}


def _has_rich() -> bool:
    try:
        import rich  # noqa: F401

        return True
    except ImportError:
        return False


def _print_banner(work_dir: Path):
    llm_ok = is_llm_configured(work_dir)
    if _has_rich():
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        status = "[green]已配置[/green]" if llm_ok else "[yellow]未配置，请选 1 配置[/yellow]"
        console.print(
            Panel.fit(
                f"[bold cyan]Arduino Client[/bold cyan] v{__version__} — 交互式终端\n"
                f"LLM API（.env）: {status}\n"
                "输入数字选择操作，或输入 [cyan]help[/cyan] / [cyan]exit[/cyan]",
                border_style="cyan",
            )
        )
    else:
        print("=" * 50)
        print(f"Arduino Client v{__version__} — 交互式终端")
        print("LLM API（.env）: " + ("已配置" if llm_ok else "未配置，请选 1 配置"))
        print("输入数字选择操作，或 help / exit")
        print("=" * 50)


def _print_menu(work_dir: Path):
    llm_ok = is_llm_configured(work_dir)
    opt1 = "配置 LLM API（API Key、Base URL、模型）"
    if _has_rich():
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold cyan")
        table.add_column(style="white")
        table.add_row(
            "1",
            opt1 + (" [green]已配置[/green]" if llm_ok else " [yellow]未配置[/yellow]"),
        )
        table.add_row("2", "生成代码（自然语言 → 运行）")
        table.add_row("3", "调试（串口诊断 + 自动修复）")
        table.add_row("4", "Demo: Blink")
        table.add_row("5", "退出")
        console.print(table)
        console.print(f"[dim]工作目录: {work_dir}[/dim]")
    else:
        suffix = " [已配置]" if llm_ok else " [未配置]"
        print("1. " + opt1 + suffix)
        print("2. 生成代码（自然语言 → 运行）")
        print("3. 调试（串口诊断 + 自动修复）")
        print("4. Demo: Blink")
        print("5. 退出")
        print(f"工作目录: {work_dir}")


def _prompt(text: str = "请选择") -> str:
    try:
        return input(f"\n{text} [1-5 / help / exit]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return "exit"


# ---------------------------------------------------------------------------
#  辅助：FQBN 推断 / 编译自动修复 / 端到端流水线
# ---------------------------------------------------------------------------


def _normalize_fqbn(user_input: str) -> str:
    value = (user_input or "").strip()
    if not value:
        return "arduino:avr:uno"
    if ":" in value:
        return value
    return FQBN_ALIASES.get(value.lower(), value)


def _infer_fqbn_for_project(client, prompt: str) -> str:
    """优先使用已连接板卡 FQBN，其次根据需求文本推断。"""
    try:
        boards = client.detect_boards()
        if boards and boards[0].fqbn:
            return boards[0].fqbn
    except Exception:
        pass

    prompt_lower = (prompt or "").lower()
    if "pico" in prompt_lower or "rp2040" in prompt_lower:
        return "arduino:mbed_rp2040:pico"
    if "nano" in prompt_lower:
        return "arduino:avr:nano"
    if "esp32" in prompt_lower:
        return "esp32:esp32:esp32"
    return "arduino:avr:uno"


def _build_with_auto_fix(client, proj_dir: Path, project_name: str, prompt: str, fqbn: str) -> bool:
    """编译 → 缺库则安装重试 → 代码错误则 LLM 修复重试，最多 3 轮 LLM 修复。"""
    from .builder import Builder

    max_fix_rounds = 3
    sketch_file = proj_dir / f"{project_name}.ino"
    lib_install_attempted = False
    fix_round = 0

    # 让 LLM 修复时也知道目标平台
    fix_prompt = f"{prompt}\n【目标平台 FQBN: {fqbn}，请确保代码兼容该平台 API。】"

    while fix_round <= max_fix_rounds:
        label = "重新编译" if (fix_round > 0 or lib_install_attempted) else "编译"
        print(f"正在{label}（{fqbn}）...")
        try:
            result = client.build(proj_dir, fqbn)
        except Exception as build_exc:
            print(f"编译异常: {build_exc}")
            return False
        if result.success:
            print(f"编译成功: {result.build_path}")
            return True

        full_output = result.output or ""
        error_summary = Builder.extract_error_lines(full_output)
        print(f"编译失败:\n{error_summary}")

        # 优先检测是否缺库（只尝试安装一轮）
        if not lib_install_attempted:
            missing = Builder.detect_missing_libraries(full_output)
            if missing:
                print(f"  [自动] 检测到缺失库: {', '.join(missing)}")
                client.builder.install_libraries(missing)
                lib_install_attempted = True
                continue

        lib_install_attempted = True

        if fix_round >= max_fix_rounds:
            print(f"已达最大修复轮数 ({max_fix_rounds})")
            return False

        try:
            current_code = sketch_file.read_text(encoding="utf-8")
            fixed = generate_arduino_code_fix(
                fix_prompt, current_code, error_summary, work_dir=client.work_dir
            )
            sketch_file.write_text(fixed, encoding="utf-8")
            fix_round += 1
            print(f"  [修复] 第 {fix_round} 轮修正代码")
        except Exception as fix_e:
            print(f"修复失败: {fix_e}", file=sys.stderr)
            return False

    return False


def _post_upload_debug(client, proj_dir, project_name, prompt, fqbn, port):
    """烧录成功后：采集串口 → 询问用户 → 进入调试循环。"""
    mon = Monitor(detector=client.board_detector)
    sketch = proj_dir / f"{project_name}.ino"

    try:
        ans = input("\n是否采集串口输出进行验证？(Y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
    if ans in ("n", "no"):
        return

    baud = 115200
    try:
        baud_in = input(f"波特率（默认 {baud}）: ").strip()
        if baud_in:
            baud = int(baud_in)
    except (EOFError, KeyboardInterrupt, ValueError):
        pass

    print(f"  [串口] 采集 {port} @ {baud} baud，等待 8 秒...")
    try:
        serial_out = mon.capture_serial(port, baud, duration=8, wait_before=2.0)
    except Exception as e:
        print(f"  [串口] 采集失败: {e}")
        return

    if serial_out:
        print("─── 串口输出 ───")
        print(serial_out[:2000])
        if len(serial_out) > 2000:
            print(f"... (共 {len(serial_out)} 字符，已截断)")
        print("─── 结束 ───")
    else:
        print("  [串口] 无输出（MCU 可能未使用 Serial 或波特率不匹配）")

    _run_debug_loop(client, sketch, serial_out, prompt, fqbn, port)


def _run_debug_loop(client, sketch_file, serial_output, prompt, fqbn, port):
    """交互式调试循环：用户描述问题 → LLM 诊断修复 → 编译上传 → 再次采集。"""
    max_rounds = 5
    mon = Monitor(detector=client.board_detector)
    proj_dir = sketch_file.parent
    project_name = sketch_file.stem

    hw_info = f"FQBN: {fqbn}, 串口: {port}"
    if prompt:
        hw_info += f"\n原始需求: {prompt}"

    for r in range(max_rounds):
        try:
            issue = input("\n功能是否正常？(正常请按 Enter / 描述问题): ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not issue:
            print("  [调试] 验证通过，退出调试。")
            return

        current_code = sketch_file.read_text(encoding="utf-8")
        print(f"  [调试] 第 {r + 1}/{max_rounds} 轮诊断...")
        try:
            diagnosis, changes, fixed_code = diagnose_with_serial(
                current_code,
                serial_output,
                issue,
                hardware_info=hw_info,
                work_dir=client.work_dir,
            )
        except Exception as e:
            print(f"  [诊断] LLM 调用失败: {e}")
            continue

        print(f"  [诊断] {diagnosis}")
        if changes:
            print(f"  [修改] {changes}")

        if not fixed_code:
            print("  [诊断] LLM 未返回修复代码")
            continue

        sketch_file.write_text(fixed_code, encoding="utf-8")
        print("  [修复] 代码已更新，编译中...")

        if not _build_with_auto_fix(client, proj_dir, project_name, prompt, fqbn):
            print("  [修复] 编译失败，代码已回退")
            sketch_file.write_text(current_code, encoding="utf-8")
            continue

        upload_result = client.upload(proj_dir, fqbn, port=port)
        if not upload_result.success:
            print(f"  [修复] 上传失败: {upload_result.message}")
            continue

        print(f"  [修复] 上传成功，采集串口中...")
        try:
            serial_output = mon.capture_serial(port, 115200, duration=8, wait_before=2.0)
        except Exception:
            serial_output = ""

        if serial_output:
            print("─── 串口输出 ───")
            print(serial_output[:2000])
            print("─── 结束 ───")
        else:
            print("  [串口] 无输出")

    print(f"  [调试] 已达最大轮数 ({max_rounds})，退出调试。")


def _run_debug_standalone(client, work_dir: Path):
    """独立调试模式：选择已有项目 → 检测板卡 → 采集串口 → 调试循环。"""
    from . import _paths

    projects_root = _paths.get_projects_dir(work_dir) / "arduino_projects"
    if not projects_root.exists():
        print("尚无项目，请先通过选项 2 生成代码。")
        return

    dirs = sorted(
        [d for d in projects_root.iterdir() if d.is_dir() and (d / f"{d.name}.ino").exists()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    if not dirs:
        print("未找到可调试项目。")
        return

    print("\n可调试项目:")
    for i, d in enumerate(dirs[:10], 1):
        print(f"  {i}. {d.name}")

    try:
        sel = input("选择项目编号: ").strip()
        idx = int(sel) - 1
        if idx < 0 or idx >= len(dirs):
            print("无效编号")
            return
    except (ValueError, EOFError, KeyboardInterrupt):
        return

    proj_dir = dirs[idx]
    project_name = proj_dir.name
    sketch_file = proj_dir / f"{project_name}.ino"

    boards = []
    try:
        boards = client.detect_boards()
    except Exception:
        pass

    if not boards or not boards[0].fqbn:
        print("未检测到板卡，请连接后重试。")
        return

    board = boards[0]
    fqbn = board.fqbn
    port = board.port
    print(f"  [检测] {board.name or fqbn} @ {port}")

    try:
        action = input("先上传当前代码再调试？(Y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    if action not in ("n", "no"):
        if not _build_with_auto_fix(client, proj_dir, project_name, "", fqbn):
            return
        upload_result = client.upload(proj_dir, fqbn, port=port)
        if not upload_result.success:
            print(f"上传失败: {upload_result.message}")
            return
        print("上传成功。")

    mon = Monitor(detector=client.board_detector)
    baud = 115200
    try:
        baud_in = input(f"波特率（默认 {baud}）: ").strip()
        if baud_in:
            baud = int(baud_in)
    except (EOFError, KeyboardInterrupt, ValueError):
        pass

    print(f"  [串口] 采集 {port} @ {baud} baud...")
    try:
        serial_out = mon.capture_serial(port, baud, duration=8, wait_before=2.0)
    except Exception as e:
        print(f"串口采集失败: {e}")
        serial_out = ""

    if serial_out:
        print("─── 串口输出 ───")
        print(serial_out[:2000])
        print("─── 结束 ───")
    else:
        print("  [串口] 无输出")

    prompt_hint = ""
    spec_file = proj_dir / f"{project_name}.md"
    if spec_file.exists():
        prompt_hint = spec_file.read_text(encoding="utf-8")
        print(f"  [规格] 已加载 {spec_file.name}")

    _run_debug_loop(client, sketch_file, serial_out, prompt_hint, fqbn, port)


def _run_pipeline(client, work_dir: Path, prompt: str, project_name: str):
    """端到端流水线：检测板卡 → 复用/生成代码 → 安装库 → 编译(+自动修复) → 烧录 / 仿真。"""
    from . import _paths

    # 1. 先检测板卡，确定目标 FQBN
    boards = []
    try:
        boards = client.detect_boards()
    except Exception:
        pass

    if boards and boards[0].fqbn:
        fqbn = boards[0].fqbn
        board = boards[0]
        print(f"  [检测] 板卡: {board.name or board.fqbn} @ {board.port}")
    else:
        fqbn = _infer_fqbn_for_project(client, prompt)
        board = None
        print("  [检测] 未检测到板卡，编译后将尝试仿真运行")

    print(f"  [自动] 目标 FQBN: {fqbn}")

    # 2. 检查项目是否已存在 → 复用 or 全新生成
    out = _paths.get_projects_dir(work_dir) / "arduino_projects" / project_name
    sketch_file = out / f"{project_name}.ino"
    analysis = None

    if sketch_file.exists():
        existing_code = sketch_file.read_text(encoding="utf-8")
        print(f"  [复用] 项目已存在: {sketch_file}")
        try:
            satisfied, patched_code, reason = review_and_patch_code(
                prompt, existing_code, fqbn, work_dir=work_dir
            )
        except Exception as rev_err:
            print(f"  [审查] 审查失败({rev_err})，将重新生成代码")
            satisfied, patched_code, reason = False, None, ""

        if satisfied:
            print(f"  [复用] 现有代码已满足需求: {reason}")
            proj = out
        else:
            if patched_code:
                print(f"  [修改] {reason}")
                sketch_file.write_text(patched_code, encoding="utf-8")
                print(f"  [修改] 已写入修改后的代码")
            else:
                print(f"  [重生成] {reason}，LLM 未返回修改代码，将重新生成")
                proj, analysis = client.generate(
                    prompt, project_name, output_dir=out, platform_hint=fqbn
                )
            proj = out

        # 零依赖原则：不主动安装库。如果代码包含第三方 #include，
        # 编译失败时 _build_with_auto_fix 会自动检测并安装缺失库。
        final_code = sketch_file.read_text(encoding="utf-8")
        include_libs = extract_includes_from_code(final_code)
        if include_libs:
            print(f"  [提示] 代码引用了外部库: {', '.join(include_libs)}（编译时按需安装）")
    else:
        proj, analysis = client.generate(prompt, project_name, output_dir=out, platform_hint=fqbn)
        print(f"已生成: {proj}")

        # 零依赖原则：不根据需求分析预装库。
        # LLM 应生成零依赖代码；如果仍有第三方 #include，
        # 编译阶段 _build_with_auto_fix 会兜底安装。
        if analysis and analysis.libraries:
            print(f"  [提示] 需求分析识别的库: {', '.join(analysis.libraries)}（编译时按需安装）")

    # 编译（失败自动修复）
    if not _build_with_auto_fix(client, proj, project_name, prompt, fqbn):
        return

    # 有板卡 → 烧录
    if board:
        port = board.port
        upload_result = client.upload(proj, fqbn, port=port)
        if upload_result.success:
            print(f"烧录成功: {upload_result.port}")
            _post_upload_debug(client, proj, project_name, prompt, fqbn, port)
        else:
            print(f"烧录失败: {upload_result.message}")
        return

    # 无板卡 → 仿真
    print("  [仿真] 正在启动 Wokwi 仿真...")

    # 先检查/配置 Token
    from .wokwi_setup import check_and_setup_wokwi_token

    token_ok, token_or_msg = check_and_setup_wokwi_token(auto_setup=True)
    if not token_ok:
        print(f"  [!] Wokwi Token 未配置: {token_or_msg}")
        print("  [提示] 可通过 'arduino-client wokwi-setup' 手动配置")
        print("  [提示] 代码已编译成功，配置 Token 后可重新运行进行仿真")
        return

    try:
        create_wokwi_project(proj, fqbn=fqbn)
        ok, msg = ensure_simulation_and_run(proj, fqbn=fqbn, timeout_ms=15000)
        if ok:
            if _has_rich():
                from rich.console import Console

                c = Console()
                c.print("[green]仿真完成[/green]")
                c.print("[dim]串口输出：[/dim]")
                c.print(msg)
            else:
                print("仿真完成。串口输出：")
                print(msg)
        else:
            print(f"仿真未成功: {msg}")
    except Exception as e:
        print(f"仿真跳过: {e}")
        print("代码已生成并编译成功，连接板卡后可重新运行以烧录。")


# ---------------------------------------------------------------------------
#  主交互循环
# ---------------------------------------------------------------------------


def _ensure_client(work_dir: Path):
    """延迟创建 ArduinoClient，未安装 arduino-cli 时引导安装。"""
    from .client import ArduinoClient

    try:
        return ArduinoClient(work_dir=work_dir)
    except ConfigurationError as e:
        error_msg = str(e)
        is_cli_missing = "未找到 arduino-cli" in error_msg or "arduino-cli" in error_msg.lower()

        if _has_rich():
            from rich.console import Console
            from rich.prompt import Confirm

            console = Console()
            console.print(f"[red]需要 arduino-cli: {e}[/red]")
            if is_cli_missing:
                console.print("[yellow]是否自动安装 arduino-cli？[/yellow]")
                try:
                    if Confirm.ask("自动安装", default=True):
                        console.print("[cyan]正在安装 arduino-cli...[/cyan]")
                        success, msg = install_arduino_cli()
                        if success:
                            console.print(f"[green]{msg}[/green]")
                            console.print(
                                "[dim]安装完成后请重新启动终端或刷新 PATH，然后重试[/dim]"
                            )
                        else:
                            console.print(f"[yellow]{msg}[/yellow]")
                except Exception:
                    console.print("[dim]可先使用 1 配置 API，或手动安装 arduino-cli 后重试[/dim]")
        else:
            print(f"需要 arduino-cli: {e}")
            if is_cli_missing:
                answer = input("是否自动安装 arduino-cli？(Y/n): ").strip().lower()
                if answer in ("", "y", "yes"):
                    print("正在安装 arduino-cli...")
                    success, msg = install_arduino_cli()
                    print(msg)
                    if success:
                        print("安装完成后请重新启动终端或刷新 PATH，然后重试")
                else:
                    print("可先使用 1 配置 API，或手动安装 arduino-cli 后重试")

        return None


def run_interactive(work_dir: Optional[Path] = None) -> int:
    """运行交互式终端"""
    work_dir = Path(work_dir or Path.cwd())
    client = None

    _print_banner(work_dir)

    while True:
        try:
            _print_menu(work_dir)
            choice = _prompt()

            if not choice:
                continue
            if choice.lower() in ("exit", "quit", "q", "5"):
                if _has_rich():
                    from rich.console import Console

                    Console().print("[cyan]再见[/cyan]")
                else:
                    print("再见")
                return 0
            if choice.lower() == "help":
                print("输入 1-5 执行对应操作，exit 退出。")
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

            # 2 — 生成代码（自然语言 → 运行）
            if choice == "2":
                if not is_llm_configured(work_dir):
                    print("请先执行 1 配置 LLM API")
                    continue
                if client is None:
                    client = _ensure_client(work_dir)
                    if client is None:
                        continue

                prompt = input("描述需求（如：用 pico 做 LED 闪烁，GP10 引脚）: ").strip()
                if not prompt:
                    continue
                name = input("项目名称（默认: my_sketch）: ").strip() or "my_sketch"

                try:
                    _run_pipeline(client, work_dir, prompt, name)
                except Exception as e:
                    print(f"失败: {e}", file=sys.stderr)
                continue

            # 3 — 调试（串口诊断 + 自动修复）
            if choice == "3":
                if not is_llm_configured(work_dir):
                    print("请先执行 1 配置 LLM API")
                    continue
                if client is None:
                    client = _ensure_client(work_dir)
                    if client is None:
                        continue
                try:
                    _run_debug_standalone(client, work_dir)
                except Exception as e:
                    print(f"调试失败: {e}", file=sys.stderr)
                continue

            # 4 — Demo: Blink
            if choice == "4":
                if not is_llm_configured(work_dir):
                    print("请先执行 1 配置 LLM API")
                    continue
                if client is None:
                    client = _ensure_client(work_dir)
                    if client is None:
                        continue

                demo_prompt = "用 Arduino Uno 做一个 LED 闪烁，13 号引脚，每 1000 毫秒闪烁一次"
                try:
                    _run_pipeline(client, work_dir, demo_prompt, "blink_demo")
                except Exception as e:
                    print(f"Demo 失败: {e}", file=sys.stderr)
                continue

            if _has_rich():
                from rich.console import Console

                Console().print("[yellow]请输入 1-5 或 help/exit[/yellow]")
            else:
                print("请输入 1-5 或 help/exit")

        except KeyboardInterrupt:
            print("\n再见")
            return 0
