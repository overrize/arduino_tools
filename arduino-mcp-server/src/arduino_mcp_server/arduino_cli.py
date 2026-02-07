"""Arduino CLI wrapper"""

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
    """Wrapper for arduino-cli commands"""
    
    def __init__(self, cli_path=None):
        # Try to find arduino-cli from environment variable or common locations
        if cli_path:
            self.cli_path = cli_path
        else:
            # Check environment variable first
            env_path = os.environ.get('ARDUINO_CLI_PATH')
            if env_path and Path(env_path).exists():
                self.cli_path = env_path
                logger.info(f"Using arduino-cli from ARDUINO_CLI_PATH: {env_path}")
            else:
                # Try common locations
                possible_paths = [
                    "arduino-cli",  # In PATH
                    os.path.expandvars("%LOCALAPPDATA%\\Arduino15\\arduino-cli.exe"),
                    "C:\\Program Files\\Arduino CLI\\arduino-cli.exe",
                ]
                
                self.cli_path = "arduino-cli"  # Default
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
        
        # Initialize port manager
        self.port_manager = PortManager()
        
        # Verify installation on init
        if not self.check_installation():
            logger.warning("arduino-cli not found or not working properly")
            logger.info("Please install from: https://arduino.github.io/arduino-cli/")
    
    def check_installation(self) -> bool:
        """Check if arduino-cli is installed"""
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
        """Install Arduino library
        
        Args:
            library_name: Name of the library to install
        
        Returns:
            True if installation successful, False otherwise
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
        """Search for Arduino libraries
        
        Args:
            query: Search query
        
        Returns:
            List of library information dictionaries
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
        """Detect connected Arduino boards
        
        Args:
            verify_connection: If True, verify that detected ports are actually accessible
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
            
            # Handle new JSON format (arduino-cli 1.x)
            if "detected_ports" in data:
                for item in data["detected_ports"]:
                    port_info = item.get("port", {})
                    port = port_info.get("address", "")
                    protocol = port_info.get("protocol", "")
                    
                    # Get hardware IDs for verification
                    properties = port_info.get("properties", {})
                    vid = properties.get("vid", "")
                    pid = properties.get("pid", "")
                    serial_number = properties.get("serialNumber", "")
                    
                    matching_boards = item.get("matching_boards", [])
                    
                    # Only include serial ports (not network)
                    if protocol != "serial":
                        continue
                    
                    # Only include boards that arduino-cli actually recognized
                    if matching_boards:
                        board = matching_boards[0]
                        board_info = BoardInfo(
                            port=port,
                            fqbn=board.get("fqbn"),
                            name=board.get("name")
                        )
                        
                        # Verify connection if requested
                        if verify_connection:
                            if self._verify_board_connection(port, vid, pid):
                                boards.append(board_info)
                                logger.info(f"Detected board: {board_info.name} at {port}")
                            else:
                                logger.warning(f"Port {port} detected but not accessible (may be in use)")
                        else:
                            boards.append(board_info)
                    # Skip ports without matching_boards - they're not Arduino devices
            # Handle old JSON format (arduino-cli 0.x)
            else:
                for item in data:
                    port = item.get("address", "")
                    matching_boards = item.get("matching_boards", [])
                    
                    # Only include recognized Arduino boards
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
                    # Skip ports without matching_boards
            
            logger.info(f"Found {len(boards)} board(s)")
            return boards
        except subprocess.TimeoutExpired:
            logger.error("Board detection timeout")
            return []
        except Exception as e:
            logger.error(f"Error detecting boards: {e}", exc_info=True)
            return []
    
    def _verify_board_connection(self, port: str, vid: str = "", pid: str = "") -> bool:
        """Verify that a board is actually connected and accessible
        
        Args:
            port: Serial port to verify
            vid: Vendor ID (optional, for additional verification)
            pid: Product ID (optional, for additional verification)
        
        Returns:
            True if board is accessible, False otherwise
        """
        try:
            import serial
            # Try to open the port briefly
            ser = serial.Serial(port, 9600, timeout=0.5)
            ser.close()
            logger.debug(f"Port {port} is accessible")
            return True
        except serial.SerialException as e:
            # Port exists but can't be opened (may be in use or disconnected)
            logger.debug(f"Port {port} not accessible: {e}")
            return False
        except Exception as e:
            logger.debug(f"Port {port} verification failed: {e}")
            return False
    
    def detect_board_by_type(self, board_type: str) -> Optional[BoardInfo]:
        """Detect a specific type of board (e.g., 'pico', 'uno', 'nano')
        
        Args:
            board_type: Type of board to detect (case-insensitive)
        
        Returns:
            BoardInfo if found, None otherwise
        """
        logger.debug(f"Looking for {board_type} board...")
        boards = self.detect_boards(verify_connection=True)
        board_type_lower = board_type.lower()
        
        # Try to match by name or FQBN
        for board in boards:
            if board.name and board_type_lower in board.name.lower():
                logger.info(f"Found {board_type}: {board.name} at {board.port}")
                return board
            if board.fqbn and board_type_lower in board.fqbn.lower():
                logger.info(f"Found {board_type}: {board.fqbn} at {board.port}")
                return board
        
        # No match found
        logger.warning(f"No {board_type} board found")
        return None
    
    def compile_sketch(self, sketch_path: Path, fqbn: str, build_path: Optional[Path] = None) -> CompileResult:
        """Compile Arduino sketch
        
        Args:
            sketch_path: Path to sketch file (.ino) or directory containing it
            fqbn: Board FQBN
            build_path: Optional build output directory (default: sketch_dir/build)
        
        Returns:
            CompileResult with build_path set
        """
        try:
            # If sketch_path is a .ino file, get its parent directory
            if sketch_path.is_file():
                sketch_dir = sketch_path.parent
            else:
                sketch_dir = sketch_path
            
            # Set build path to sketch_dir/build if not specified
            if build_path is None:
                build_path = sketch_dir / "build"
            
            # Create build directory
            build_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Compiling sketch: {sketch_dir} for {fqbn}")
            
            # Compile with specified build path
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
                # Parse error messages
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
        """Upload compiled sketch to board"""
        try:
            # Auto-detect port if not provided
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
            
            # Prepare port for upload (close any users)
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
        """Monitor serial output for specified duration"""
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
            # Timeout is expected for monitoring
            logger.debug("Serial monitoring timeout (expected)")
            output = e.stdout.decode() if e.stdout else ""
            lines = output.split('\n')
            return [line.strip() for line in lines if line.strip()]
        except Exception as e:
            logger.error(f"Error monitoring serial: {e}")
            return [f"Error monitoring serial: {str(e)}"]
