"""项目配置管理"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ProjectConfig:
    """项目配置"""
    board: str              # pico, uno, nano, esp32
    board_fqbn: str         # arduino:mbed_rp2040:pico
    project_type: str       # led_blink, button_led, sensor
    pin: int                # LED 引脚
    interval: int           # 闪烁间隔（秒）
    project_name: str       # 项目名称
    
    # 板型映射
    BOARD_MAPPING: Dict = None
    
    def __post_init__(self):
        """初始化后设置板型映射"""
        if ProjectConfig.BOARD_MAPPING is None:
            ProjectConfig.BOARD_MAPPING = {
                "pico": {
                    "name": "Raspberry Pi Pico",
                    "fqbn": "arduino:mbed_rp2040:pico",
                    "default_pin": 25
                },
                "uno": {
                    "name": "Arduino Uno",
                    "fqbn": "arduino:avr:uno",
                    "default_pin": 13
                },
                "nano": {
                    "name": "Arduino Nano",
                    "fqbn": "arduino:avr:nano",
                    "default_pin": 13
                },
                "esp32": {
                    "name": "ESP32",
                    "fqbn": "esp32:esp32:esp32",
                    "default_pin": 2
                }
            }
    
    @classmethod
    def from_user_input(cls, board: str, project_type: str, 
                       pin: int, interval: int, name: str):
        """从用户输入创建配置"""
        # 确保映射已初始化
        if cls.BOARD_MAPPING is None:
            temp = cls(board="pico", board_fqbn="", project_type="led_blink",
                      pin=25, interval=1, project_name="temp")
        
        board_info = cls.BOARD_MAPPING[board]
        return cls(
            board=board,
            board_fqbn=board_info["fqbn"],
            project_type=project_type,
            pin=pin,
            interval=interval,
            project_name=name
        )
    
    def get_board_name(self) -> str:
        """获取板型名称"""
        return self.BOARD_MAPPING[self.board]["name"]
    
    def get_project_type_name(self) -> str:
        """获取项目类型名称"""
        type_names = {
            "led_blink": "LED 闪烁",
            "button_led": "按钮控制 LED",
            "sensor": "传感器读取",
            "custom": "自定义"
        }
        return type_names.get(self.project_type, self.project_type)
    
    def to_natural_language(self) -> str:
        """转换为自然语言描述"""
        board_name = self.get_board_name()
        
        if self.project_type == "led_blink":
            return (f"用 {board_name} 做一个 LED 闪烁，"
                   f"{self.pin} 号引脚，每 {self.interval} 秒闪一次")
        elif self.project_type == "button_led":
            return f"用 {board_name} 做一个按钮控制 LED，{self.pin} 号引脚"
        elif self.project_type == "sensor":
            return f"用 {board_name} 读取传感器数据，{self.pin} 号引脚"
        else:
            return f"用 {board_name} 创建项目"
