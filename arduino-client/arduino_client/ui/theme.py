"""
Arduino 风格的配色主题

灵感来源于 Arduino 官方品牌色：
- 青绿品牌色 (#00979D)
- 深色背景适配
- 硬件状态颜色编码
"""

from rich.theme import Theme

# Arduino 品牌色
BRAND_COLOR = "#00979D"
BRAND_DIM = "#006468"
ACCENT_COLOR = "#E47128"

# Arduino 风格主题定义
ARDUINO_THEME = Theme(
    {
        # === 品牌与基础 ===
        "brand": f"bold {BRAND_COLOR}",
        "brand_dim": BRAND_DIM,
        "accent": ACCENT_COLOR,
        "title": f"bold {BRAND_COLOR}",
        "subtitle": "dim cyan",
        # === 硬件相关 ===
        "mcu": BRAND_COLOR,
        "mcu_dim": BRAND_DIM,
        "core": "white",
        "frequency": "yellow",
        "package": "dim",
        "memory": "green",
        "peripheral.on": "green",
        "peripheral.off": "dim",
        "peripheral.active": "bold green",
        "register.name": "cyan",
        "register.addr": "dim",
        "register.value": "yellow",
        "register.changed": "bold red",
        # === 接口状态 ===
        "serial": "#3498DB",
        "jtag": "#F39C12",
        "swd": "#E67E22",
        "logic": "#1ABC9C",
        "scope": "#9B59B6",
        "interface.connected": "green",
        "interface.disconnected": "red",
        "interface.active": "bold green",
        # === 代码与输出 ===
        "code": "green",
        "code.keyword": "magenta",
        "code.function": "cyan",
        "code.comment": "dim green",
        "code.string": "yellow",
        "code.number": "blue",
        "output.info": "blue",
        "output.success": "green",
        "output.warning": "yellow",
        "output.error": "red",
        "output.debug": "dim",
        # === 交互元素 ===
        "prompt": "bold yellow",
        "cursor": "bold white on cyan",
        "selected": "bold cyan",
        "highlight": "bold white",
        "border": BRAND_DIM,
        "border.focused": BRAND_COLOR,
        # === 状态指示 ===
        "status.ok": "green",
        "status.warn": "yellow",
        "status.error": "red",
        "status.pending": "yellow",
        "status.running": "cyan",
        # === 日志级别 ===
        "log.debug": "dim",
        "log.info": "blue",
        "log.warning": "yellow",
        "log.error": "red",
        "log.critical": "bold red",
    }
)


def get_theme() -> Theme:
    """获取 Arduino 主题"""
    return ARDUINO_THEME


# 颜色常量（用于直接引用）
COLORS = {
    "brand": BRAND_COLOR,
    "brand_dim": BRAND_DIM,
    "accent": ACCENT_COLOR,
    "success": "#2ECC71",
    "warning": "#F1C40F",
    "error": "#E74C3C",
    "info": "#3498DB",
    "text": "#ECF0F1",
    "text_dim": "#7F8C8D",
    "panel_bg": "#1A1A2E",
    "border": "#2D3748",
}


def get_color(name: str) -> str:
    """获取颜色值"""
    return COLORS.get(name, "white")
