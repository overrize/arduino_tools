"""Arduino 串口监控模块"""
import subprocess
import time
import logging
import threading
from typing import List, Optional

from .errors import HardwareError
from .board_detector import BoardDetector

log = logging.getLogger("arduino_client")


class Monitor:
    """Arduino 串口监控器"""

    def __init__(self, detector: Optional[BoardDetector] = None):
        self.detector = detector or BoardDetector()

    def capture_serial(
        self,
        port: str,
        baud_rate: int = 115200,
        duration: int = 8,
        wait_before: float = 2.0,
    ) -> str:
        """上传后定时采集串口输出，返回原始文本。

        Args:
            port: 串口号
            baud_rate: 波特率
            duration: 采集秒数
            wait_before: 采集前等待秒数（等 MCU 启动 / USB 枚举）
        """
        if wait_before > 0:
            log.info("等待 %.1fs 让 MCU 启动...", wait_before)
            time.sleep(wait_before)

        cmd = [
            self.detector.cli_path, "monitor",
            "-p", port,
            "-c", f"baudrate={baud_rate}",
            "--raw",
        ]
        log.info("采集串口 %s (%d baud) %d 秒", port, baud_rate, duration)
        buf: list[str] = []

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                errors="replace",
            )

            def _reader():
                assert proc.stdout is not None
                for line in proc.stdout:
                    buf.append(line)

            t = threading.Thread(target=_reader, daemon=True)
            t.start()
            t.join(timeout=duration)

            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        except FileNotFoundError:
            raise HardwareError("arduino-cli 未找到，无法启动串口监控")
        except Exception as e:
            log.error("串口采集异常: %s", e)
            raise HardwareError(f"串口采集异常: {e}")

        output = "".join(buf).strip()
        lines = [l for l in output.splitlines() if l.strip()]
        log.info("采集到 %d 行", len(lines))
        return output

    def monitor_serial(
        self,
        port: str,
        baud_rate: int = 9600,
        duration: int = 10,
    ) -> List[str]:
        """兼容旧接口"""
        text = self.capture_serial(port, baud_rate, duration, wait_before=0)
        return [l.strip() for l in text.splitlines() if l.strip()]
