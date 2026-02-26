"""串口管理工具"""
import logging

log = logging.getLogger("arduino_client")


class PortManager:
    """管理串口访问与占用冲突"""

    def prepare_port_for_upload(self, port: str) -> bool:
        """为上传准备串口。

        不再主动检测或占用串口——arduino-cli 自己处理端口访问和
        板卡重置（如 RP2040 的 1200-baud 触发 BOOTSEL）。
        提前用 pyserial 打开串口反而会干扰 arduino-cli 的上传流程。
        """
        print(f"  [串口] {port} → 交由 arduino-cli 处理")
        return True
