"""Arduino 上传模块"""
import subprocess
import logging
from pathlib import Path
from typing import Optional

from .errors import HardwareError
from .models import UploadResult
from .board_detector import BoardDetector
from .port_manager import PortManager

log = logging.getLogger("arduino_client")


class Uploader:
    """Arduino 固件上传器"""
    
    def __init__(self, detector: Optional[BoardDetector] = None):
        """初始化上传器
        
        Args:
            detector: 板卡检测器实例，None 时自动创建
        """
        self.detector = detector or BoardDetector()
        self.port_manager = PortManager()
    
    def upload_sketch(
        self,
        sketch_path: Path,
        fqbn: str,
        port: Optional[str] = None,
        auto_close_port: bool = True
    ) -> UploadResult:
        """将编译好的工程上传到板卡
        
        Args:
            sketch_path: 工程路径
            fqbn: 板卡 FQBN
            port: 串口，None 时自动检测
            auto_close_port: 是否自动关闭占用串口的进程
            
        Returns:
            上传结果
        """
        try:
            # 未指定端口时自动检测
            if not port:
                log.debug("自动检测板卡...")
                boards = self.detector.detect_boards()
                if not boards:
                    log.error("未检测到板卡")
                    raise HardwareError("未检测到 Arduino 板卡")
                port = boards[0].port
                log.info(f"使用自动检测的串口: {port}")
            
            # 上传前准备串口（关闭占用进程）
            if auto_close_port:
                log.info(f"准备串口 {port} 用于上传...")
                if not self.port_manager.prepare_port_for_upload(port):
                    log.error(f"串口 {port} 忙碌且无法释放")
                    raise HardwareError(
                        f"串口 {port} 忙碌且无法释放。"
                        f"请关闭占用该串口的程序（Arduino IDE、串口监视器等）"
                    )
            
            log.info(f"上传到 {port}，FQBN: {fqbn}")
            cmd = [
                self.detector.cli_path, "upload",
                "-p", port,
                "--fqbn", fqbn,
                str(sketch_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            message = result.stdout + result.stderr
            
            if success:
                log.info(f"上传成功到 {port}")
            else:
                log.error(f"上传失败到 {port}")
            
            return UploadResult(
                success=success,
                port=port,
                message=message if success else f"上传失败: {message}"
            )
        except subprocess.TimeoutExpired:
            log.error("上传超时")
            raise HardwareError("上传超时")
        except Exception as e:
            log.error(f"上传错误: {e}", exc_info=True)
            raise HardwareError(f"上传错误: {e}")
