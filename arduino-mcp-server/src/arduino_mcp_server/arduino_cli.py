"""Arduino CLI 封装"""

import subprocess
import json
import logging
import os
from pathlib import Path
from typing import List, Optional
from .models import BoardInfo, CompileResult, UploadResult
from .port_manager import PortManager

logger = logging.getLogger(__name__)


class ArduinoCLI:
    """arduino-cli 命令封装"""
    
    def __init__(self, cli_path=None):
        # 优先从环境变量或常见路径查找 arduino-cli
        if cli_path:
            self.cli_path = cli_path
        else:
            # 先检查环境变量
            env_path = os.environ.get('ARDUINO_CLI_PATH')
            if env_path and Path(env_path).exists():
                self.cli_path = env_path
                logger.info(f"Using arduino-cli from ARDUINO_CLI_PATH: {env_path}")
            else:
                # 尝试常见安装路径
                possible_paths = [
                    "arduino-cli",  # PATH 中
                    os.path.expandvars("%LOCALAPPDATA%\\Arduino15\\arduino-cli.exe"),
                    "C:\\Program Files\\Arduino CLI\\arduino-cli.exe",
                ]
                
                self.cli_path = "arduino-cli"  # 默认
                for path in possible_paths:
                    try:
                        result = subprocess.run(
                            [path, "version"],
                            capture_output=True,
                            timeout=2
                        )
                        if result.returncode == 0:
                            self.cli_path = path
                            logger.info(f"Found arduino-cli at: {path}")
                            break
                    except:
                        continue
        
        # 初始化串口管理器
        self.port_manager = PortManager()
        
        # 初始化时验证安装
        if not self.check_installation():
            logger.warning("arduino-cli not found or not working properly")
            logger.info("Please install from: https://arduino.github.io/arduino-cli/")
    
    def check_installation(self) -> bool:
        """检查 arduino-cli 是否已安装"""
        try:
            result = subprocess.run(
                [self.cli_path, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.debug(f"arduino-cli version: {result.stdout.strip()}")
                return True
            return False
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Failed to check arduino-cli installation: {e}")
            return False
    
    def install_library(self, library_name: str) -> bool:
        """安装 Arduino 库
        
        Args:
            library_name: 要安装的库名称
        
        Returns:
            安装成功返回 True，否则返回 False
        """
        try:
            logger.info(f"Installing library: {library_name}")
            result = subprocess.run(
                [self.cli_path, "lib", "install", library_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Library {library_name} installed successfully")
                return True
            else:
                logger.error(f"Failed to install {library_name}: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"Library installation timeout for {library_name}")
            return False
        except Exception as e:
            logger.error(f"Error installing library: {e}")
            return False
    
    def search_library(self, query: str) -> List[dict]:
        """搜索 Arduino 库
        
        Args:
            query: 搜索关键词
        
        Returns:
            库信息字典列表
        """
        try:
            result = subprocess.run(
                [self.cli_path, "lib", "search", query, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("libraries", [])
            return []
        except subprocess.TimeoutExpired:
            logger.error(f"Library search timeout for query: {query}")
            return []
        except Exception as e:
            logger.error(f"Error searching libraries: {e}")
            return []
    
    def detect_boards(self, verify_connection: bool = True) -> List[BoardInfo]:
        """检测已连接的 Arduino 板卡
        
        Args:
            verify_connection: 为 True 时验证检测到的串口是否实际可访问
        """
        try:
            logger.debug("Detecting Arduino boards...")
            result = subprocess.run(
                [self.cli_path, "board", "list", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"Board detection failed: {result.stderr}")
                return []
            
            data = json.loads(result.stdout)
            boards = []
            
            # 处理新 JSON 格式 (arduino-cli 1.x)
            if "detected_ports" in data:
                for item in data["detected_ports"]:
                    port_info = item.get("port", {})
                    port = port_info.get("address", "")
                    protocol = port_info.get("protocol", "")
                    
                    # 获取硬件 ID 用于验证
                    properties = port_info.get("properties", {})
                    vid = properties.get("vid", "")
                    pid = properties.get("pid", "")
                    serial_number = properties.get("serialNumber", "")
                    
                    matching_boards = item.get("matching_boards", [])
                    
                    # 仅包含串口（不含网络）
                    if protocol != "serial":
                        continue
                    
                    # 仅包含 arduino-cli 实际识别到的板卡
                    if matching_boards:
                        board = matching_boards[0]
                        board_info = BoardInfo(
                            port=port,
                            fqbn=board.get("fqbn"),
                            name=board.get("name")
                        )
                        
                        # 如需则验证连接
                        if verify_connection:
                            if self._verify_board_connection(port, vid, pid):
                                boards.append(board_info)
                                logger.info(f"Detected board: {board_info.name} at {port}")
                            else:
                                logger.warning(f"Port {port} detected but not accessible (may be in use)")
                        else:
                            boards.append(board_info)
                    # 跳过无匹配板卡的端口（非 Arduino 设备）
            # 处理旧 JSON 格式 (arduino-cli 0.x)
            else:
                for item in data:
                    port = item.get("address", "")
                    matching_boards = item.get("matching_boards", [])
                    
                    # 仅包含已识别的 Arduino 板卡
                    if matching_boards:
                        board = matching_boards[0]
                        board_info = BoardInfo(
                            port=port,
                            fqbn=board.get("fqbn"),
                            name=board.get("name")
                        )
                        
                        if verify_connection:
                            if self._verify_board_connection(port, "", ""):
                                boards.append(board_info)
                        else:
                            boards.append(board_info)
                    # 跳过无匹配板卡的端口
            
            logger.info(f"Found {len(boards)} board(s)")
            return boards
        except subprocess.TimeoutExpired:
            logger.error("Board detection timeout")
            return []
        except Exception as e:
            logger.error(f"Error detecting boards: {e}", exc_info=True)
            return []
    
    def _verify_board_connection(self, port: str, vid: str = "", pid: str = "") -> bool:
        """验证板卡是否实际连接且可访问
        
        Args:
            port: 要验证的串口
            vid: 厂商 ID（可选，用于额外验证）
            pid: 产品 ID（可选，用于额外验证）
        
        Returns:
            板卡可访问返回 True，否则返回 False
        """
        try:
            import serial
            # 短暂尝试打开串口
            ser = serial.Serial(port, 9600, timeout=0.5)
            ser.close()
            logger.debug(f"Port {port} is accessible")
            return True
        except serial.SerialException as e:
            # 串口存在但无法打开（可能被占用或已断开）
            logger.debug(f"Port {port} not accessible: {e}")
            return False
        except Exception as e:
            logger.debug(f"Port {port} verification failed: {e}")
            return False
    
    def detect_board_by_type(self, board_type: str) -> Optional[BoardInfo]:
        """按类型检测板卡（如 'pico', 'uno', 'nano'）
        
        Args:
            board_type: 要检测的板卡类型（不区分大小写）
        
        Returns:
            找到返回 BoardInfo，否则返回 None
        """
        logger.debug(f"Looking for {board_type} board...")
        boards = self.detect_boards(verify_connection=True)
        board_type_lower = board_type.lower()
        
        # 按名称或 FQBN 匹配
        for board in boards:
            if board.name and board_type_lower in board.name.lower():
                logger.info(f"Found {board_type}: {board.name} at {board.port}")
                return board
            if board.fqbn and board_type_lower in board.fqbn.lower():
                logger.info(f"Found {board_type}: {board.fqbn} at {board.port}")
                return board
        
        # 未找到匹配
        logger.warning(f"No {board_type} board found")
        return None
    
    def compile_sketch(self, sketch_path: Path, fqbn: str, build_path: Optional[Path] = None) -> CompileResult:
        """编译 Arduino 工程
        
        Args:
            sketch_path: 工程文件 (.ino) 路径或所在目录
            fqbn: 板卡 FQBN
            build_path: 可选，编译输出目录（默认 sketch_dir/build）
        
        Returns:
            带 build_path 的 CompileResult
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
            
            logger.info(f"Compiling sketch: {sketch_dir} for {fqbn}")
            
            # 使用指定 build 路径编译
            result = subprocess.run(
                [
                    self.cli_path, "compile", 
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
                logger.info(f"Compilation successful: {sketch_dir}")
            else:
                logger.error(f"Compilation failed: {sketch_dir}")
            
            errors = []
            if not success:
                # 解析错误信息
                for line in output.split('\n'):
                    if 'error:' in line.lower():
                        errors.append(line.strip())
                        logger.debug(f"Compile error: {line.strip()}")
            
            return CompileResult(
                success=success,
                output=output,
                errors=errors if errors else None,
                build_path=str(build_path) if success else None
            )
        except subprocess.TimeoutExpired:
            logger.error("Compilation timeout")
            return CompileResult(
                success=False,
                output="Compilation timeout",
                errors=["Compilation took too long"]
            )
        except Exception as e:
            logger.error(f"Compilation error: {e}", exc_info=True)
            return CompileResult(
                success=False,
                output=str(e),
                errors=[str(e)]
            )
    
    def upload_sketch(
        self, 
        sketch_path: Path, 
        fqbn: str, 
        port: Optional[str] = None,
        auto_close_port: bool = True
    ) -> UploadResult:
        """将编译好的工程上传到板卡"""
        try:
            # 未指定端口时自动检测
            if not port:
                logger.debug("Auto-detecting board for upload...")
                boards = self.detect_boards()
                if not boards:
                    logger.error("No board detected for upload")
                    return UploadResult(
                        success=False,
                        port="",
                        message="No Arduino board detected"
                    )
                port = boards[0].port
                logger.info(f"Using auto-detected port: {port}")
            
            # 上传前准备串口（关闭占用进程）
            if auto_close_port:
                logger.info(f"Preparing {port} for upload...")
                if not self.port_manager.prepare_port_for_upload(port):
                    logger.error(f"Port {port} is busy and could not be released")
                    return UploadResult(
                        success=False,
                        port=port,
                        message=f"Port {port} is busy and could not be released. "
                                f"Please close any programs using the port (Arduino IDE, serial monitors, etc.)"
                    )
            
            logger.info(f"Uploading to {port} with FQBN {fqbn}")
            cmd = [
                self.cli_path, "upload",
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
                logger.info(f"Upload successful to {port}")
            else:
                logger.error(f"Upload failed to {port}")
            
            return UploadResult(
                success=success,
                port=port,
                message=message if success else f"Upload failed: {message}"
            )
        except subprocess.TimeoutExpired:
            logger.error("Upload timeout")
            return UploadResult(
                success=False,
                port=port or "",
                message="Upload timeout"
            )
        except Exception as e:
            logger.error(f"Upload error: {e}", exc_info=True)
            return UploadResult(
                success=False,
                port=port or "",
                message=f"Upload error: {str(e)}"
            )
    
    def monitor_serial(
        self, 
        port: str, 
        baud_rate: int = 9600, 
        duration: int = 10
    ) -> List[str]:
        """在指定时长内监控串口输出"""
        try:
            logger.info(f"Monitoring serial port {port} at {baud_rate} baud for {duration}s")
            cmd = [
                self.cli_path, "monitor",
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
            logger.debug(f"Captured {len(filtered_lines)} lines from serial")
            return filtered_lines
        except subprocess.TimeoutExpired as e:
            # 监控超时是预期行为
            logger.debug("Serial monitoring timeout (expected)")
            output = e.stdout.decode() if e.stdout else ""
            lines = output.split('\n')
            return [line.strip() for line in lines if line.strip()]
        except Exception as e:
            logger.error(f"Error monitoring serial: {e}")
            return [f"Error monitoring serial: {str(e)}"]
