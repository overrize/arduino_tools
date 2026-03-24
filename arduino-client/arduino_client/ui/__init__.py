"""
Arduino Client UI - Arduino 风格的终端界面

提供现代化的终端 UI 组件，包括：
- 主题系统 (theme.py)
- 统一控制台 (console.py)
- 可复用组件 (components/)
- 板卡目录选择器 (board_catalog.py)
- 串口监视器 (serial_monitor.py)
"""

try:
    from .theme import ARDUINO_THEME, get_theme
    from .console import get_console, create_console
    from .components import (
        render_splash,
        render_header,
        create_success_panel,
        create_error_panel,
        create_info_panel,
        create_progress,
        create_spinner,
        StepIndicator,
    )

    HAS_UI = True
except ImportError:
    HAS_UI = False

    def get_console():
        raise ImportError("Rich is required for UI components: pip install rich")

    def get_theme():
        raise ImportError("Rich is required for UI components: pip install rich")

# 延迟导入较重的模块
def _get_serial_monitor():
    from .serial_monitor import SerialMonitor, create_monitor, DisplayMode, LogLevel
    return SerialMonitor, create_monitor, DisplayMode, LogLevel

def _get_board_catalog():
    from .board_catalog import BoardCatalog, ArduinoBoardInfo, ArduinoFamily
    return BoardCatalog, ArduinoBoardInfo, ArduinoFamily

__all__ = [
    "ARDUINO_THEME",
    "get_theme",
    "get_console",
    "create_console",
    "HAS_UI",
    "render_splash",
    "render_header",
    "create_success_panel",
    "create_error_panel",
    "create_info_panel",
    "create_progress",
    "create_spinner",
    "StepIndicator",
]
