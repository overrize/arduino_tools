"""板卡检测模块"""
import subprocess
import logging
import os
from pathlib import Path
from typing import List, Optional

from .errors import BoardDetectionError, ConfigurationError
from .models import BoardInfo

log = logging.getLogger("arduino_client")


class BoardDetector:
    """Arduino 板卡检测器"""

    def __init__(self, cli_path: Optional[str] = None):
        """初始化板卡检测器

        Args:
            cli_path: arduino-cli 可执行文件路径，None 时自动查找
        """
        self.cli_path = self._find_arduino_cli(cli_path)
        if not self.cli_path:
            raise ConfigurationError(
                "未找到 arduino-cli。请安装: "
                "Windows: winget install ArduinoSA.CLI\n"
                "或访问: https://arduino.github.io/arduino-cli/"
            )
        log.info(f"使用 arduino-cli: {self.cli_path}")

    def _find_arduino_cli(self, cli_path: Optional[str] = None) -> Optional[str]:
        """查找 arduino-cli 可执行文件"""
        if cli_path:
            if Path(cli_path).exists():
                return cli_path
            return None

        # 检查环境变量
        env_path = os.environ.get('ARDUINO_CLI_PATH')
        if env_path and Path(env_path).exists():
            return env_path

        # 尝试常见路径
        possible_paths = [
            "arduino-cli",  # PATH 中
            os.path.expandvars("%LOCALAPPDATA%\\Arduino15\\arduino-cli.exe"),
            "C:\\Program Files\\Arduino CLI\\arduino-cli.exe",
        ]

        for path in possible_paths:
            try:
                result = subprocess.run(
                    [path, "version"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return path
            except:
                continue

        return None

    def check_installation(self) -> bool:
        """检查 arduino-cli 是否已安装"""
        try:
            result = subprocess.run(
                [self.cli_path, "version"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
                errors="replace",
            )
            return result.returncode == 0
        except:
            return False

    def detect_boards(self, verify_connection: bool = True) -> List[BoardInfo]:
        """检测已连接的 Arduino 板卡

        Args:
            verify_connection: 是否验证串口连接

        Returns:
            检测到的板卡列表
        """
        try:
            log.debug("检测 Arduino 板卡...")
            result = subprocess.run(
                [self.cli_path, "board", "list", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="replace",
            )

            if result.returncode != 0:
                log.error(f"板卡检测失败: {result.stderr}")
                raise BoardDetectionError(f"板卡检测失败: {result.stderr}")

            import json
            data = json.loads(result.stdout)
            boards = []

            # 处理新 JSON 格式 (arduino-cli 1.x)
            if "detected_ports" in data:
                for item in data["detected_ports"]:
                    port_info = item.get("port", {})
                    port = port_info.get("address", "")
                    protocol = port_info.get("protocol", "")

                    # 仅包含串口
                    if protocol != "serial":
                        continue

                    matching_boards = item.get("matching_boards", [])
                    if matching_boards:
                        board = matching_boards[0]
                        board_info = BoardInfo(
                            port=port,
                            fqbn=board.get("fqbn"),
                            name=board.get("name")
                        )
                        boards.append(board_info)
                        log.info(f"检测到板卡: {board_info.name} at {port}")
            # 处理旧 JSON 格式 (arduino-cli 0.x)
            else:
                for item in data:
                    port = item.get("address", "")
                    matching_boards = item.get("matching_boards", [])

                    if matching_boards:
                        board = matching_boards[0]
                        board_info = BoardInfo(
                            port=port,
                            fqbn=board.get("fqbn"),
                            name=board.get("name")
                        )
                        boards.append(board_info)

            log.info(f"检测到 {len(boards)} 个板卡")
            return boards
        except subprocess.TimeoutExpired:
            raise BoardDetectionError("板卡检测超时")
        except Exception as e:
            log.error(f"板卡检测错误: {e}", exc_info=True)
            raise BoardDetectionError(f"板卡检测错误: {e}")

    def detect_board_by_type(self, board_type: str) -> Optional[BoardInfo]:
        """按类型检测板卡（如 'pico', 'uno', 'nano'）

        Args:
            board_type: 板卡类型（不区分大小写）

        Returns:
            找到的板卡信息，否则返回 None
        """
        log.debug(f"查找 {board_type} 板卡...")
        boards = self.detect_boards(verify_connection=True)
        board_type_lower = board_type.lower()

        for board in boards:
            if board.name and board_type_lower in board.name.lower():
                log.info(f"找到 {board_type}: {board.name} at {board.port}")
                return board
            if board.fqbn and board_type_lower in board.fqbn.lower():
                log.info(f"找到 {board_type}: {board.fqbn} at {board.port}")
                return board

        log.warning(f"未找到 {board_type} 板卡")
        return None

    def _verify_board_connection(self, port: str) -> bool:
        """验证板卡是否实际连接且可访问"""
        try:
            import serial
            ser = serial.Serial(port, 9600, timeout=0.5)
            ser.close()
            log.debug(f"串口 {port} 可访问")
            return True
        except Exception as e:
            log.debug(f"串口 {port} 不可访问: {e}")
            return False
