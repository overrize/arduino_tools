"""包内资源路径 — 功能与业务解耦"""
from pathlib import Path

_PKG = Path(__file__).resolve().parent
ARDUINO_CLIENT_ROOT = _PKG.parent  # arduino_client 所在目录
ROOT = ARDUINO_CLIENT_ROOT  # 兼容


def get_projects_dir(work_dir: Path | None = None) -> Path:
    """生成项目根目录：与 arduino_client 同级，便于独立复制/二次开发"""
    wd = Path(work_dir or Path.cwd()).resolve()
    try:
        wd.relative_to(ARDUINO_CLIENT_ROOT)
        parent = ARDUINO_CLIENT_ROOT.parent
        if len(parent.parts) <= 1 or parent == ARDUINO_CLIENT_ROOT:
            return ARDUINO_CLIENT_ROOT
        return parent
    except ValueError:
        return wd


def get_demos_dir() -> Path:
    """Demo 目录"""
    demos = _PKG / "demos"
    return demos if demos.exists() else ROOT / "demos"
