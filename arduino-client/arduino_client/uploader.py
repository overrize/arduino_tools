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
        self.detector = detector or BoardDetector()
        self.port_manager = PortManager()

    def upload_sketch(
        self,
        sketch_path: Path,
        fqbn: str,
        port: Optional[str] = None,
        auto_close_port: bool = True,
        build_path: Optional[Path] = None,
    ) -> UploadResult:
        """将编译好的工程上传到板卡"""
        try:
            if not port:
                log.debug("自动检测板卡...")
                boards = self.detector.detect_boards()
                if not boards:
                    raise HardwareError("未检测到 Arduino 板卡")
                port = boards[0].port
                log.info("使用自动检测的串口: %s", port)

            if auto_close_port:
                self.port_manager.prepare_port_for_upload(port)

            sketch_dir = Path(sketch_path)
            if sketch_dir.is_file():
                sketch_dir = sketch_dir.parent
            if build_path is None:
                candidate = sketch_dir / "build"
                if candidate.is_dir():
                    build_path = candidate

            print(f"  [烧录] 正在上传到 {port}（{fqbn}）...")
            cmd = [
                self.detector.cli_path, "upload",
                "-p", port,
                "--fqbn", fqbn,
            ]
            if build_path and build_path.is_dir():
                cmd += ["--input-dir", str(build_path)]
            cmd.append(str(sketch_path))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                encoding="utf-8",
                errors="replace",
            )

            success = result.returncode == 0
            message = (result.stdout or "") + (result.stderr or "")

            if success:
                log.info("上传成功到 %s", port)
            else:
                log.error("上传失败到 %s", port)

            return UploadResult(
                success=success,
                port=port,
                message=message if success else f"上传失败: {message}",
            )
        except subprocess.TimeoutExpired:
            log.error("上传超时")
            raise HardwareError("上传超时（120s），请检查板卡连接")
        except HardwareError:
            raise
        except Exception as e:
            log.error("上传错误: %s", e, exc_info=True)
            raise HardwareError(f"上传错误: {e}")
