"""Arduino 编译模块"""
import subprocess
import logging
from pathlib import Path
from typing import Optional

from .errors import BuildError, ConfigurationError
from .models import CompileResult
from .board_detector import BoardDetector

log = logging.getLogger("arduino_client")


class Builder:
    """Arduino 项目编译器"""
    
    def __init__(self, detector: Optional[BoardDetector] = None):
        """初始化编译器
        
        Args:
            detector: 板卡检测器实例，None 时自动创建
        """
        self.detector = detector or BoardDetector()
    
    def compile_sketch(
        self,
        sketch_path: Path,
        fqbn: str,
        build_path: Optional[Path] = None
    ) -> CompileResult:
        """编译 Arduino 工程
        
        Args:
            sketch_path: 工程文件 (.ino) 路径或所在目录
            fqbn: 板卡 FQBN
            build_path: 可选，编译输出目录（默认 sketch_dir/build）
            
        Returns:
            编译结果
        """
        try:
            # 若传入的是 .ino 文件，取其所在目录
            if sketch_path.is_file():
                sketch_dir = sketch_path.parent
            else:
                sketch_dir = sketch_path
            
            # 未指定时使用 sketch_dir/build
            if build_path is None:
                build_path = sketch_dir / "build"
            
            # 创建编译目录
            build_path.mkdir(parents=True, exist_ok=True)
            
            log.info(f"编译工程: {sketch_dir} for {fqbn}")
            
            # 使用指定 build 路径编译
            result = subprocess.run(
                [
                    self.detector.cli_path, "compile",
                    "--fqbn", fqbn,
                    "--build-path", str(build_path),
                    str(sketch_dir)
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            if success:
                log.info(f"编译成功: {sketch_dir}")
            else:
                log.error(f"编译失败: {sketch_dir}")
            
            errors = []
            if not success:
                # 解析错误信息
                for line in output.split('\n'):
                    if 'error:' in line.lower():
                        errors.append(line.strip())
                        log.debug(f"编译错误: {line.strip()}")
            
            return CompileResult(
                success=success,
                output=output,
                errors=errors if errors else None,
                build_path=str(build_path) if success else None
            )
        except subprocess.TimeoutExpired:
            log.error("编译超时")
            raise BuildError("编译超时")
        except Exception as e:
            log.error(f"编译错误: {e}", exc_info=True)
            raise BuildError(f"编译错误: {e}")
