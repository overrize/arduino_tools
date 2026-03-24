"""
Arduino 板卡目录 - 浏览和选择 Arduino 板卡

提供常见 Arduino 板卡数据库和交互式选择界面。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from .console import get_console
from .theme import BRAND_COLOR, BRAND_DIM


class ArduinoFamily(Enum):
    AVR = "AVR"
    SAMD = "SAMD"
    MBED_RP2040 = "MBED_RP2040"
    ESP32 = "ESP32"
    NRF52 = "NRF52"
    MEGAAVR = "MEGAAVR"
    SAM = "SAM"


@dataclass
class ArduinoBoardInfo:
    name: str
    display_name: str
    fqbn: str
    family: ArduinoFamily
    mcu: str
    flash_kb: int
    sram_kb: int
    clock_mhz: int
    peripherals: List[str] = field(default_factory=list)
    core_url: str = ""


# 常见 Arduino 板卡数据库
ALL_BOARDS: List[ArduinoBoardInfo] = [
    # === AVR 系列 ===
    ArduinoBoardInfo(
        name="uno", display_name="Arduino Uno",
        fqbn="arduino:avr:uno", family=ArduinoFamily.AVR,
        mcu="ATmega328P", flash_kb=32, sram_kb=2, clock_mhz=16,
        peripherals=["GPIO", "UART", "SPI", "I2C", "ADC", "PWM"],
    ),
    ArduinoBoardInfo(
        name="nano", display_name="Arduino Nano",
        fqbn="arduino:avr:nano", family=ArduinoFamily.AVR,
        mcu="ATmega328P", flash_kb=32, sram_kb=2, clock_mhz=16,
        peripherals=["GPIO", "UART", "SPI", "I2C", "ADC", "PWM"],
    ),
    ArduinoBoardInfo(
        name="mega", display_name="Arduino Mega 2560",
        fqbn="arduino:avr:mega", family=ArduinoFamily.AVR,
        mcu="ATmega2560", flash_kb=256, sram_kb=8, clock_mhz=16,
        peripherals=["GPIO", "UART x4", "SPI", "I2C", "ADC", "PWM"],
    ),
    ArduinoBoardInfo(
        name="leonardo", display_name="Arduino Leonardo",
        fqbn="arduino:avr:leonardo", family=ArduinoFamily.AVR,
        mcu="ATmega32U4", flash_kb=32, sram_kb=2, clock_mhz=16,
        peripherals=["GPIO", "UART", "SPI", "I2C", "ADC", "PWM", "USB"],
    ),
    ArduinoBoardInfo(
        name="micro", display_name="Arduino Micro",
        fqbn="arduino:avr:micro", family=ArduinoFamily.AVR,
        mcu="ATmega32U4", flash_kb=32, sram_kb=2, clock_mhz=16,
        peripherals=["GPIO", "UART", "SPI", "I2C", "ADC", "PWM", "USB"],
    ),
    # === SAMD 系列 ===
    ArduinoBoardInfo(
        name="zero", display_name="Arduino Zero",
        fqbn="arduino:samd:arduino_zero_edbg", family=ArduinoFamily.SAMD,
        mcu="ATSAMD21G18", flash_kb=256, sram_kb=32, clock_mhz=48,
        peripherals=["GPIO", "UART", "SPI", "I2C", "ADC", "DAC", "PWM", "USB"],
    ),
    ArduinoBoardInfo(
        name="mkr1000", display_name="Arduino MKR1000",
        fqbn="arduino:samd:mkr1000", family=ArduinoFamily.SAMD,
        mcu="ATSAMD21G18", flash_kb=256, sram_kb=32, clock_mhz=48,
        peripherals=["GPIO", "UART", "SPI", "I2C", "ADC", "DAC", "WiFi"],
    ),
    ArduinoBoardInfo(
        name="nano_33_iot", display_name="Arduino Nano 33 IoT",
        fqbn="arduino:samd:nano_33_iot", family=ArduinoFamily.SAMD,
        mcu="ATSAMD21G18", flash_kb=256, sram_kb=32, clock_mhz=48,
        peripherals=["GPIO", "UART", "SPI", "I2C", "ADC", "WiFi", "BLE"],
    ),
    # === RP2040 系列 ===
    ArduinoBoardInfo(
        name="pico", display_name="Raspberry Pi Pico",
        fqbn="arduino:mbed_rp2040:pico", family=ArduinoFamily.MBED_RP2040,
        mcu="RP2040", flash_kb=2048, sram_kb=264, clock_mhz=133,
        peripherals=["GPIO", "UART x2", "SPI x2", "I2C x2", "ADC", "PWM", "PIO"],
    ),
    ArduinoBoardInfo(
        name="nano_rp2040", display_name="Arduino Nano RP2040 Connect",
        fqbn="arduino:mbed_nano:nanorp2040connect", family=ArduinoFamily.MBED_RP2040,
        mcu="RP2040", flash_kb=16384, sram_kb=264, clock_mhz=133,
        peripherals=["GPIO", "UART", "SPI", "I2C", "ADC", "WiFi", "BLE", "IMU"],
    ),
    # === ESP32 系列 ===
    ArduinoBoardInfo(
        name="esp32", display_name="ESP32 DevKit",
        fqbn="esp32:esp32:esp32", family=ArduinoFamily.ESP32,
        mcu="ESP32", flash_kb=4096, sram_kb=520, clock_mhz=240,
        peripherals=["GPIO", "UART x3", "SPI", "I2C", "ADC", "DAC", "WiFi", "BLE", "PWM"],
        core_url="https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json",
    ),
    ArduinoBoardInfo(
        name="esp32s3", display_name="ESP32-S3 DevKit",
        fqbn="esp32:esp32:esp32s3", family=ArduinoFamily.ESP32,
        mcu="ESP32-S3", flash_kb=8192, sram_kb=512, clock_mhz=240,
        peripherals=["GPIO", "UART x3", "SPI", "I2C", "ADC", "WiFi", "BLE", "USB"],
        core_url="https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json",
    ),
    ArduinoBoardInfo(
        name="esp32c3", display_name="ESP32-C3 DevKit",
        fqbn="esp32:esp32:esp32c3", family=ArduinoFamily.ESP32,
        mcu="ESP32-C3", flash_kb=4096, sram_kb=400, clock_mhz=160,
        peripherals=["GPIO", "UART x2", "SPI", "I2C", "ADC", "WiFi", "BLE"],
        core_url="https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json",
    ),
    # === SAM 系列 ===
    ArduinoBoardInfo(
        name="due", display_name="Arduino Due",
        fqbn="arduino:sam:arduino_due_x_dbg", family=ArduinoFamily.SAM,
        mcu="ATSAM3X8E", flash_kb=512, sram_kb=96, clock_mhz=84,
        peripherals=["GPIO", "UART x4", "SPI", "I2C x2", "ADC", "DAC x2", "PWM", "USB", "CAN"],
    ),
    # === MEGAAVR 系列 ===
    ArduinoBoardInfo(
        name="nano_every", display_name="Arduino Nano Every",
        fqbn="arduino:megaavr:nona4809", family=ArduinoFamily.MEGAAVR,
        mcu="ATmega4809", flash_kb=48, sram_kb=6, clock_mhz=20,
        peripherals=["GPIO", "UART x4", "SPI", "I2C", "ADC", "PWM"],
    ),
    # === NRF52 系列 ===
    ArduinoBoardInfo(
        name="nano_33_ble", display_name="Arduino Nano 33 BLE",
        fqbn="arduino:mbed_nano:nano33ble", family=ArduinoFamily.NRF52,
        mcu="nRF52840", flash_kb=1024, sram_kb=256, clock_mhz=64,
        peripherals=["GPIO", "UART", "SPI", "I2C", "ADC", "BLE", "USB", "IMU"],
    ),
    ArduinoBoardInfo(
        name="nano_33_ble_sense", display_name="Arduino Nano 33 BLE Sense",
        fqbn="arduino:mbed_nano:nano33ble", family=ArduinoFamily.NRF52,
        mcu="nRF52840", flash_kb=1024, sram_kb=256, clock_mhz=64,
        peripherals=["GPIO", "UART", "SPI", "I2C", "ADC", "BLE", "USB", "IMU", "Mic", "Gesture", "Light", "Humidity"],
    ),
]


def search_boards(query: str) -> List[ArduinoBoardInfo]:
    """搜索板卡"""
    q = query.lower()
    return [b for b in ALL_BOARDS if q in b.name.lower() or q in b.display_name.lower()
            or q in b.mcu.lower() or q in b.fqbn.lower()]


def get_board(name_or_fqbn: str) -> Optional[ArduinoBoardInfo]:
    """按名称或 FQBN 获取板卡"""
    for b in ALL_BOARDS:
        if b.name == name_or_fqbn or b.fqbn == name_or_fqbn:
            return b
    return None


def get_boards_by_family(family: ArduinoFamily) -> List[ArduinoBoardInfo]:
    """按系列获取板卡"""
    return [b for b in ALL_BOARDS if b.family == family]


class BoardCatalog:
    """交互式板卡目录"""

    def __init__(self, console: Console = None):
        self.console = console or get_console()
        self.boards = ALL_BOARDS
        self.selected: Optional[ArduinoBoardInfo] = None

    def filter(self, family: Optional[str] = None) -> None:
        """按系列过滤"""
        if family:
            try:
                f = ArduinoFamily(family.upper())
                self.boards = get_boards_by_family(f)
            except ValueError:
                self.boards = ALL_BOARDS
        else:
            self.boards = ALL_BOARDS

    def render(self) -> None:
        """渲染板卡表格"""
        table = Table(
            title="Arduino Board Catalog",
            border_style=BRAND_DIM,
            show_header=True,
            header_style=f"bold {BRAND_COLOR}",
            box=box.ROUNDED,
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Board", style=f"bold {BRAND_COLOR}")
        table.add_column("FQBN", style="dim")
        table.add_column("MCU", style="cyan")
        table.add_column("Flash", style="green", justify="right")
        table.add_column("SRAM", style="green", justify="right")
        table.add_column("Clock", style="yellow", justify="right")
        table.add_column("Family", style="dim")

        for i, board in enumerate(self.boards, 1):
            table.add_row(
                str(i),
                board.display_name,
                board.fqbn,
                board.mcu,
                f"{board.flash_kb} KB",
                f"{board.sram_kb} KB",
                f"{board.clock_mhz} MHz",
                board.family.value,
            )

        self.console.print(table)

    def render_details(self, board: ArduinoBoardInfo) -> None:
        """渲染板卡详情"""
        content = Text()
        content.append(f"{board.display_name}\n", f"bold {BRAND_COLOR}")
        content.append(f"FQBN: {board.fqbn}\n", "dim")
        content.append("\n")
        content.append(f"MCU: ", "cyan")
        content.append(f"{board.mcu}\n", "white")
        content.append(f"Flash: ", "cyan")
        content.append(f"{board.flash_kb} KB\n", "green")
        content.append(f"SRAM: ", "cyan")
        content.append(f"{board.sram_kb} KB\n", "green")
        content.append(f"Clock: ", "cyan")
        content.append(f"{board.clock_mhz} MHz\n", "yellow")
        content.append("\n")
        content.append("Peripherals:\n", "cyan")
        for p in board.peripherals:
            content.append(f"  [OK] {p}\n", "green")

        if board.core_url:
            content.append(f"\nCore URL: ", "dim")
            content.append(f"{board.core_url}\n", "dim")

        self.console.print(Panel(
            content,
            title=f"[{BRAND_COLOR}]{board.display_name}[/{BRAND_COLOR}]",
            border_style=BRAND_DIM,
            box=box.ROUNDED,
            padding=(1, 2),
        ))

    def interactive_select(self) -> Optional[ArduinoBoardInfo]:
        """交互式选择板卡"""
        from rich.prompt import Prompt

        self.render()

        try:
            choice = Prompt.ask(
                f"\n[{BRAND_COLOR}][>] Select board number (or 'q' to cancel)[/{BRAND_COLOR}]",
                default="q",
            )
        except (EOFError, KeyboardInterrupt):
            return None

        if choice.lower() == "q":
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.boards):
                self.selected = self.boards[idx]
                self.render_details(self.selected)
                return self.selected
        except ValueError:
            # 尝试按名称搜索
            results = search_boards(choice)
            if results:
                self.selected = results[0]
                self.render_details(self.selected)
                return self.selected

        self.console.print("[red][X] Invalid selection[/red]")
        return None
