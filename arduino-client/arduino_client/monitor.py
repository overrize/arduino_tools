"""Arduino 串口监控模块"""
import subprocess
import logging
from typing import List, Optional

from .errors import HardwareError
from .board_detector import BoardDetector

log = logging.getLogger("arduino_client")


class Monitor:
    """Arduino 串口监控器"""
    
    def __init__(self, detector: Optional[BoardDetector] = None):
        """初始化监控器
        
        Args:
            detector: 板卡检测器实例，None 时自动创建
        """
        self.detector = detector or BoardDetector()
    
    def monitor_serial(
        self,
        port: str,
        baud_rate: int = 9600,
        duration: int = 10
    ) -> List[str]:
        """在指定时长内监控串口输出
        
        Args:
            port: 串口
            baud_rate: 波特率
            duration: 监控时长（秒）
            
        Returns:
            接收到的串口输出行列表
        """
        try:
            log.info(f"监控串口 {port}，波特率 {baud_rate}，时长 {duration}秒")
            cmd = [
                self.detector.cli_path, "monitor",
                "-p", port,
                "-c", f"baudrate={baud_rate}"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration
            )
            
            lines = result.stdout.split('\n')
            filtered_lines = [line.strip() for line in lines if line.strip()]
            log.debug(f"接收到 {len(filtered_lines)} 行")
            return filtered_lines
        except subprocess.TimeoutExpired as e:
            # 监控超时是预期行为
            log.debug("串口监控超时（预期）")
            output = e.stdout.decode() if e.stdout else ""
            lines = output.split('\n')
            return [line.strip() for line in lines if line.strip()]
        except Exception as e:
            log.error(f"串口监控错误: {e}")
            raise HardwareError(f"串口监控错误: {e}")
