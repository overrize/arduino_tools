"""Wokwi 仿真电路图生成器

负责生成 Wokwi 仿真所需的 diagram.json 和 wokwi.toml 文件
"""

import json
from typing import Dict, List, Any
from .models import ProjectConfig, Component


class WokwiGenerator:
    """Wokwi 电路图生成器类"""
    
    # 板卡类型映射表：Arduino FQBN → Wokwi 板卡类型
    BOARD_TYPES = {
        "arduino:avr:uno": "board-arduino-uno",
        "arduino:avr:nano": "board-arduino-nano",
        "arduino:mbed_rp2040:pico": "board-pi-pico",
        "esp32:esp32:esp32": "board-esp32-devkit-c-v4",
    }
    
    def __init__(self):
        """初始化生成器"""
        self.parts = []  # 电路元件列表
        self.connections = []  # 连接线列表
        self.next_id = 1  # 下一个元件 ID
    
    def generate_diagram(self, config: ProjectConfig, project_name: str) -> Dict[str, Any]:
        """生成完整的 Wokwi 电路图
        
        Args:
            config: 项目配置
            project_name: 项目名称
        
        Returns:
            diagram.json 的字典数据
        """
        # 重置状态
        self.parts = []
        self.connections = []
        self.next_id = 1
        
        # 添加主控板
        board_type = self.BOARD_TYPES.get(config.board_fqbn, "board-arduino-uno")
        board_id = "mcu"
        self.parts.append({
            "type": board_type,
            "id": board_id,
            "top": 0,
            "left": 0,
            "attrs": {}
        })
        
        # 添加串口监视器连接
        self.connections.append([f"{board_id}:TX", "$serialMonitor:RX", "", []])
        self.connections.append([f"{board_id}:RX", "$serialMonitor:TX", "", []])
        
        # 根据配置添加各种组件
        for component in config.components:
            if component.type == "led":
                self._add_led(board_id, component, config.board_fqbn)
            elif component.type == "button":
                self._add_button(board_id, component)
            elif component.type == "sensor":
                self._add_sensor(board_id, component)
        
        # 返回完整的 diagram.json 结构
        return {
            "version": 1,
            "author": "Arduino MCP Server",
            "editor": "wokwi",
            "parts": self.parts,
            "connections": self.connections,
            "dependencies": {}
        }
    
    def _add_led(self, board_id: str, led: Component, board_fqbn: str):
        """添加 LED 组件到电路图
        
        Args:
            board_id: 主控板 ID
            led: LED 组件配置
            board_fqbn: 板卡 FQBN（用于确定引脚命名）
        """
        led_id = f"led{self.next_id}"
        resistor_id = f"r{self.next_id}"
        self.next_id += 1
        
        # 计算元件位置（从板卡偏移）
        y_offset = 100 + (self.next_id - 1) * 50
        
        # 添加 LED 元件
        self.parts.append({
            "type": "wokwi-led",
            "id": led_id,
            "top": y_offset,
            "left": 200,
            "attrs": {"color": "red"}  # 红色 LED
        })
        
        # 添加限流电阻（220Ω）
        self.parts.append({
            "type": "wokwi-resistor",
            "id": resistor_id,
            "top": y_offset + 10,
            "left": 150,
            "attrs": {"value": "220"}  # 220 欧姆
        })
        
        # 根据板卡类型获取引脚名称
        pin_name = self._get_pin_name(board_fqbn, led.pin)
        
        # 连接：主控板引脚 → 电阻 → LED 阳极
        self.connections.append([
            f"{board_id}:{pin_name}",
            f"{resistor_id}:1",
            "green",  # 绿色连线
            []
        ])
        self.connections.append([
            f"{resistor_id}:2",
            f"{led_id}:A",  # A 为阳极
            "green",
            []
        ])
        
        # 连接：LED 阴极 → GND
        self.connections.append([
            f"{led_id}:C",  # C 为阴极
            f"{board_id}:GND",
            "black",  # 黑色连线（GND）
            []
        ])
    
    def _add_button(self, board_id: str, button: Component):
        """添加按钮组件到电路图
        
        Args:
            board_id: 主控板 ID
            button: 按钮组件配置
        """
        button_id = f"btn{self.next_id}"
        self.next_id += 1
        
        y_offset = 100 + (self.next_id - 1) * 50
        
        # 添加按钮元件
        self.parts.append({
            "type": "wokwi-pushbutton",
            "id": button_id,
            "top": y_offset,
            "left": 200,
            "attrs": {"color": "blue"}  # 蓝色按钮
        })
        
        # 连接按钮
        pin_name = f"GPIO{button.pin}" if "pico" in board_id else str(button.pin)
        self.connections.append([
            f"{button_id}:1.l",
            f"{board_id}:{pin_name}",
            "green",
            []
        ])
        self.connections.append([
            f"{button_id}:2.l",
            f"{board_id}:GND",
            "black",
            []
        ])
    
    def _add_sensor(self, board_id: str, sensor: Component):
        """添加传感器组件到电路图
        
        Args:
            board_id: 主控板 ID
            sensor: 传感器组件配置
        """
        sensor_id = f"sensor{self.next_id}"
        self.next_id += 1
        
        y_offset = 100 + (self.next_id - 1) * 80
        
        # 添加 DHT22 温湿度传感器
        if sensor.name.upper() == "DHT22":
            self.parts.append({
                "type": "wokwi-dht22",
                "id": sensor_id,
                "top": y_offset,
                "left": 200,
                "attrs": {}
            })
            
            pin_name = self._get_pin_name("", sensor.pin)
            
            # 连接 DHT22
            self.connections.append([
                f"{sensor_id}:VCC",
                f"{board_id}:3V3",
                "red",
                []
            ])
            self.connections.append([
                f"{sensor_id}:GND",
                f"{board_id}:GND",
                "black",
                []
            ])
            self.connections.append([
                f"{sensor_id}:SDA",
                f"{board_id}:{pin_name}",
                "green",
                []
            ])
    
    def _get_pin_name(self, board_fqbn: str, pin: int) -> str:
        """根据板卡类型获取引脚名称
        
        Args:
            board_fqbn: 板卡 FQBN
            pin: 引脚号
        
        Returns:
            Wokwi 中的引脚名称
        """
        if "pico" in board_fqbn.lower():
            return f"GP{pin}"  # Pico 引脚：GP0, GP1, ...
        elif "esp32" in board_fqbn.lower():
            return f"GPIO{pin}"  # ESP32 引脚：GPIO0, GPIO1, ...
        else:
            # Arduino Uno/Nano 直接使用数字
            return str(pin)
    
    def save_diagram(self, diagram: Dict[str, Any], output_path: str):
        """保存电路图到文件
        
        Args:
            diagram: 电路图数据
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(diagram, f, indent=2)
    
    def generate_wokwi_toml(self, config: ProjectConfig, project_name: str) -> str:
        """生成 wokwi.toml 配置文件
        
        这个文件告诉 Wokwi 仿真器在哪里找到编译好的固件文件
        
        Args:
            config: 项目配置
            project_name: 项目名称（用于固件文件名）
        
        Returns:
            wokwi.toml 文件内容
        """
        # 根据板卡类型确定固件文件扩展名
        if "pico" in config.board_fqbn:
            firmware_ext = "uf2"  # Pico 使用 UF2 格式
        elif "esp32" in config.board_fqbn:
            firmware_ext = "bin"  # ESP32 使用 BIN 格式
        else:  # AVR 板卡（Uno, Nano）
            firmware_ext = "hex"  # AVR 使用 HEX 格式
        
        # 固件路径相对于 wokwi.toml（位于 simulation/ 目录）
        # 编译产物在 ../build/ 目录
        firmware_filename = f"{project_name}.ino.{firmware_ext}"
        firmware_path = f"../build/{firmware_filename}"
        
        return f"""[wokwi]
version = 1
firmware = '{firmware_path}'
elf = '{firmware_path}'
"""
    
    def get_simulation_url(self, project_path: str) -> str:
        """获取 Wokwi 在线仿真 URL（用于在线版本）
        
        Args:
            project_path: 项目路径
        
        Returns:
            Wokwi 在线仿真 URL
        """
        # 这会生成一个可分享的 URL（如果使用 Wokwi 在线版）
        return f"https://wokwi.com/projects/new"
