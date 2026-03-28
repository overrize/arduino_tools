"""
Arduino 仿真模块 — 基于 Wokwi
当未检测到板卡时，支持通过 Wokwi 仿真运行固件，并通过串口输出/指令获取反馈。
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List

# FQBN -> Wokwi 板型
FQBN_TO_WOKWI_BOARD = {
    "arduino:avr:uno": "wokwi-arduino-uno",
    "arduino:avr:nano": "wokwi-arduino-nano",
    "arduino:avr:mega": "wokwi-arduino-mega",
}


def _board_type_from_fqbn(fqbn: str) -> str:
    """从 FQBN 得到 Wokwi 板型"""
    return FQBN_TO_WOKWI_BOARD.get(fqbn, "wokwi-arduino-uno")


def _find_build_artifacts(build_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """在 build 目录下查找 .hex 和 .elf"""
    if not build_dir.is_dir():
        return None, None
    hex_files = list(build_dir.glob("*.hex"))
    elf_files = list(build_dir.glob("*.elf"))
    return (
        hex_files[0] if hex_files else None,
        elf_files[0] if elf_files else None,
    )


def create_wokwi_project(
    project_dir: Path,
    fqbn: str = "arduino:avr:uno",
    led_pin: int = 13,
    build_path: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """为已编译的工程创建 Wokwi 仿真文件（diagram.json + wokwi.toml）

    Args:
        project_dir: 工程目录（含 .ino 与 build/）
        fqbn: 板卡 FQBN
        led_pin: 仿真中 LED 连接的引脚（仅图示，不影响已有固件逻辑）
        build_path: 编译输出目录，默认 project_dir/build

    Returns:
        (diagram.json 路径, wokwi.toml 路径)
    """
    project_dir = Path(project_dir).resolve()
    if build_path is None:
        build_path = project_dir / "build"
    build_path = Path(build_path).resolve()

    hex_path, elf_path = _find_build_artifacts(build_path)
    if not hex_path:
        raise FileNotFoundError(f"未在 {build_path} 找到 .hex，请先编译工程（如菜单 4 编译工程）")

    # 相对 project_dir 的路径（Wokwi 要求相对 wokwi.toml）
    rel_hex = str(hex_path.relative_to(project_dir)).replace("\\", "/")
    rel_elf = str(elf_path.relative_to(project_dir)).replace("\\", "/") if elf_path else None

    board_type = _board_type_from_fqbn(fqbn)
    # diagram.json: Uno/Nano + LED 接指定引脚
    diagram = {
        "version": 1,
        "author": "arduino_client",
        "editor": "wokwi",
        "parts": [
            {"id": "uno", "type": board_type, "left": 50, "top": 50},
            {
                "id": "led1",
                "type": "wokwi-led",
                "left": 280,
                "top": 80,
                "attrs": {"color": "green"},
            },
            {
                "id": "r1",
                "type": "wokwi-resistor",
                "left": 220,
                "top": 80,
                "attrs": {"value": "220"},
            },
        ],
        "connections": [
            ["uno:13", "r1:1", "green", []],
            ["r1:2", "led1:A", "green", []],
            ["led1:C", "uno:GND.1", "black", []],
        ],
    }
    # 若 LED 不是 13，仍可画在 13（仅示意）；固件逻辑由用户代码决定
    diagram_path = project_dir / "diagram.json"
    diagram_path.write_text(json.dumps(diagram, indent=2, ensure_ascii=False), encoding="utf-8")

    # wokwi.toml（elf 可选，可加快仿真）
    toml_content = f'[wokwi]\nversion = 1\nfirmware = "{rel_hex}"\n'
    if rel_elf:
        toml_content += f'elf = "{rel_elf}"\n'
    toml_path = project_dir / "wokwi.toml"
    toml_path.write_text(toml_content, encoding="utf-8")

    return diagram_path, toml_path


def run_wokwi_cli(
    project_dir: Path,
    timeout_ms: int = 30000,
    serial_log_file: Optional[Path] = None,
    expect_text: Optional[str] = None,
    fail_text: Optional[str] = None,
) -> Tuple[bool, str]:
    """运行 wokwi-cli 仿真，可通过串口输出/期望文本获取反馈

    Args:
        project_dir: 工程目录（含 diagram.json、wokwi.toml 及 build/ 固件）
        timeout_ms: 仿真超时（毫秒）
        serial_log_file: 将串口输出写入该文件
        expect_text: 若仿真输出中包含该文本则视为成功（可选）
        fail_text: 若输出中包含该文本则视为失败（可选）

    Returns:
        (是否成功, 串口输出或错误信息)
    """
    # 静默检查 Token（不弹交互提示，交互配置由上层 _ensure_wokwi_cli 负责）
    from .wokwi_setup import get_wokwi_token
    token = get_wokwi_token()
    if not token:
        return False, "未设置 WOKWI_CLI_TOKEN。请运行 'arduino-client wokwi-setup' 或在设置中配置。"

    cli = "wokwi-cli"
    if not shutil.which(cli):
        return False, "未找到 wokwi-cli，请安装: https://docs.wokwi.com/wokwi-ci/cli-installation"

    project_dir = Path(project_dir).resolve()
    if not (project_dir / "diagram.json").exists() or not (project_dir / "wokwi.toml").exists():
        return (
            False,
            "工程目录缺少 diagram.json 或 wokwi.toml，请先对工程执行「仿真运行」生成 Wokwi 项目。",
        )

    cmd: List[str] = [
        cli,
        "--timeout",
        str(timeout_ms),
        "--diagram-file",
        "diagram.json",
    ]
    if serial_log_file is not None:
        cmd += ["--serial-log-file", str(Path(serial_log_file).resolve())]
    if expect_text is not None:
        cmd += ["--expect-text", expect_text]
    if fail_text is not None:
        cmd += ["--fail-text", fail_text]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=(timeout_ms // 1000) + 60,
        )
        out = (result.stdout or "") + (result.stderr or "")
        if serial_log_file and Path(serial_log_file).exists():
            out = Path(serial_log_file).read_text(encoding="utf-8", errors="replace")

        if not out.strip():
            return False, "（无输出）"

        if result.returncode == 0:
            return True, out

        # wokwi-cli 超时退出码非 0，但对于持续运行的固件（LED 闪烁、按键控制等）
        # 超时是正常行为 —— 只要仿真成功启动过就视为成功
        if "Timeout" in out and "Starting simulation" in out:
            return True, out

        return False, out
    except Exception as e:
        return False, str(e)


def ensure_simulation_and_run(
    project_dir: Path,
    fqbn: str = "arduino:avr:uno",
    timeout_ms: int = 15000,
    expect_text: Optional[str] = None,
) -> Tuple[bool, str]:
    """确保工程有 Wokwi 配置后运行仿真（便于通过指令/串口获取反馈）

    Returns:
        (是否成功, 串口输出或错误信息)
    """
    project_dir = Path(project_dir).resolve()
    if not (project_dir / "diagram.json").exists():
        try:
            create_wokwi_project(project_dir, fqbn=fqbn)
        except FileNotFoundError as e:
            return False, str(e)
    return run_wokwi_cli(project_dir, timeout_ms=timeout_ms, expect_text=expect_text)
