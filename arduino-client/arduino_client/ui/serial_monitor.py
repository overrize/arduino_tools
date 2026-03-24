"""
串口监视器 - 实时串口数据显示

使用 Rich Live 提供实时更新的串口监控界面。
支持文本/十六进制/混合显示模式和日志级别颜色。
"""

import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .console import get_console
from .theme import BRAND_COLOR, BRAND_DIM


class DisplayMode(Enum):
    TEXT = "text"
    HEX = "hex"
    MIXED = "mixed"


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


# 日志级别匹配模式
LOG_PATTERNS = {
    LogLevel.ERROR: re.compile(r"\b(ERROR|FAIL|FATAL|PANIC|ASSERT)\b", re.IGNORECASE),
    LogLevel.WARNING: re.compile(r"\b(WARN|WARNING|CAUTION)\b", re.IGNORECASE),
    LogLevel.INFO: re.compile(r"\b(INFO|NOTICE|OK|READY)\b", re.IGNORECASE),
    LogLevel.DEBUG: re.compile(r"\b(DEBUG|TRACE|VERBOSE|DBG)\b", re.IGNORECASE),
}

LOG_STYLES = {
    LogLevel.ERROR: "red",
    LogLevel.WARNING: "yellow",
    LogLevel.INFO: "blue",
    LogLevel.DEBUG: "dim",
    LogLevel.UNKNOWN: "white",
}


@dataclass
class SerialMessage:
    timestamp: datetime
    raw: bytes
    text: str
    level: LogLevel
    line_number: int


class SerialMonitor:
    """实时串口监视器"""

    def __init__(self, console: Console = None, max_history: int = 500):
        self.console = console or get_console()
        self.history: deque = deque(maxlen=max_history)
        self.port_name: Optional[str] = None
        self.baud_rate: int = 115200
        self.mode: DisplayMode = DisplayMode.TEXT
        self._serial = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._line_count = 0
        self._bytes_received = 0
        self._start_time: Optional[datetime] = None

    def connect(self, port: str, baud: int = 115200) -> bool:
        """连接串口"""
        try:
            import serial
            self._serial = serial.Serial(port, baud, timeout=0.1)
            self.port_name = port
            self.baud_rate = baud
            self._start_time = datetime.now()
            return True
        except Exception as e:
            self.console.print(f"[red][X] Failed to connect: {e}[/red]")
            return False

    def disconnect(self) -> None:
        """断开串口"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def _detect_log_level(self, text: str) -> LogLevel:
        """检测日志级别"""
        for level, pattern in LOG_PATTERNS.items():
            if pattern.search(text):
                return level
        return LogLevel.UNKNOWN

    def _format_line(self, msg: SerialMessage) -> Text:
        """格式化一行输出"""
        style = LOG_STYLES.get(msg.level, "white")
        ts = msg.timestamp.strftime("%H:%M:%S.%f")[:-3]

        line = Text()
        line.append(f"[{ts}] ", "dim")
        line.append(f"{msg.line_number:>5} ", "dim")

        if self.mode == DisplayMode.HEX:
            hex_str = " ".join(f"{b:02X}" for b in msg.raw)
            line.append(hex_str, style)
        elif self.mode == DisplayMode.MIXED:
            line.append(msg.text, style)
            if msg.raw:
                hex_str = " ".join(f"{b:02X}" for b in msg.raw[:16])
                line.append(f"  | {hex_str}", "dim")
        else:
            line.append(msg.text, style)

        return line

    def _read_loop(self) -> None:
        """串口读取线程"""
        buffer = b""
        while self._running and self._serial and self._serial.is_open:
            try:
                data = self._serial.read(self._serial.in_waiting or 1)
                if not data:
                    continue

                self._bytes_received += len(data)
                buffer += data

                while b"\n" in buffer:
                    line_bytes, buffer = buffer.split(b"\n", 1)
                    line_text = line_bytes.decode("utf-8", errors="replace").rstrip("\r")
                    self._line_count += 1

                    msg = SerialMessage(
                        timestamp=datetime.now(),
                        raw=line_bytes,
                        text=line_text,
                        level=self._detect_log_level(line_text),
                        line_number=self._line_count,
                    )
                    self.history.append(msg)

            except Exception:
                if self._running:
                    time.sleep(0.1)

    def _render_header(self) -> Panel:
        """渲染头部状态栏"""
        elapsed = ""
        if self._start_time:
            delta = datetime.now() - self._start_time
            elapsed = f"{int(delta.total_seconds())}s"

        table = Table(show_header=False, box=None, padding=(0, 2), expand=True)
        table.add_column(ratio=1)
        table.add_column(ratio=1)
        table.add_column(ratio=1)
        table.add_column(ratio=1)

        table.add_row(
            f"[{BRAND_COLOR}]Port:[/{BRAND_COLOR}] {self.port_name}",
            f"[{BRAND_COLOR}]Baud:[/{BRAND_COLOR}] {self.baud_rate}",
            f"[{BRAND_COLOR}]Lines:[/{BRAND_COLOR}] {self._line_count}",
            f"[{BRAND_COLOR}]Bytes:[/{BRAND_COLOR}] {self._bytes_received} ({elapsed})",
        )

        return Panel(
            table,
            title=f"[bold {BRAND_COLOR}]Serial Monitor[/bold {BRAND_COLOR}]",
            border_style=BRAND_DIM,
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _render_log(self) -> Panel:
        """渲染日志区域"""
        lines = Text()
        for msg in list(self.history)[-30:]:
            lines.append_text(self._format_line(msg))
            lines.append("\n")

        if not self.history:
            lines.append("[dim]Waiting for data...[/dim]")

        return Panel(
            lines,
            title="[dim]Output[/dim]",
            border_style="dim",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def render(self) -> Layout:
        """渲染完整界面"""
        layout = Layout()
        layout.split_column(
            Layout(self._render_header(), size=5),
            Layout(self._render_log()),
        )
        return layout

    def start_live(self, refresh_rate: int = 10) -> None:
        """启动实时监控"""
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

        with Live(self.render(), console=self.console, refresh_per_second=refresh_rate) as live:
            try:
                while self._running:
                    live.update(self.render())
                    time.sleep(1.0 / refresh_rate)
            except KeyboardInterrupt:
                self._running = False

    def capture(self, duration: float = 8.0, wait_before: float = 2.0) -> str:
        """定时采集串口输出（兼容旧接口）"""
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

        time.sleep(wait_before + duration)
        self._running = False
        self._thread.join(timeout=2)

        return "\n".join(msg.text for msg in self.history)


def create_monitor(
    port: str,
    baud: int = 115200,
    console: Console = None,
) -> Optional[SerialMonitor]:
    """创建并连接串口监视器"""
    monitor = SerialMonitor(console=console)
    if monitor.connect(port, baud):
        return monitor
    return None
