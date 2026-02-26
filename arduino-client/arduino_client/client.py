"""
ArduinoClient — 可编程 API
支持 CLI 与 Python 脚本调用
"""
import logging
from pathlib import Path
from typing import Optional, List

from . import _paths
from .board_detector import BoardDetector
from .builder import Builder
from .uploader import Uploader
from .monitor import Monitor
from .code_generator import generate_arduino_code, generate_arduino_code_fix
from .requirement_analyzer import analyze_requirement
from .models import BoardInfo, CompileResult, UploadResult, ProjectConfig, RequirementAnalysis

log = logging.getLogger("arduino_client")


class ArduinoClient:
    """
    Arduino Client — 端到端 Arduino 开发
    
    示例:
        client = ArduinoClient(work_dir=".")
        boards = client.detect_boards()
        client.generate("用 Arduino Uno 做一个 LED 闪烁，13 号引脚", "led_blink")
        client.build("led_blink", "arduino:avr:uno")
        client.upload("led_blink", "arduino:avr:uno")
    """
    
    def __init__(self, work_dir: Optional[Path] = None):
        """初始化 Arduino Client
        
        Args:
            work_dir: 工作目录，None 时使用当前目录
        """
        self.work_dir = Path(work_dir or Path.cwd())
        self.detector = BoardDetector()
        self.builder = Builder(self.detector)
        self.uploader = Uploader(self.detector)
        self.monitor = Monitor(self.detector)
    
    def detect_boards(self, verify_connection: bool = True) -> List[BoardInfo]:
        """检测已连接的 Arduino 板卡
        
        Args:
            verify_connection: 是否验证串口连接
            
        Returns:
            检测到的板卡列表
        """
        return self.detector.detect_boards(verify_connection=verify_connection)
    
    def detect_board_by_type(self, board_type: str) -> Optional[BoardInfo]:
        """按类型检测板卡
        
        Args:
            board_type: 板卡类型（如 'pico', 'uno', 'nano'）
            
        Returns:
            找到的板卡信息，否则返回 None
        """
        return self.detector.detect_board_by_type(board_type)
    
    def generate(
        self,
        prompt: str,
        project_name: str,
        output_dir: Optional[Path] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        platform_hint: Optional[str] = None,
    ) -> "tuple[Path, Optional[RequirementAnalysis]]":
        """根据自然语言生成 Arduino 工程
        
        Args:
            platform_hint: 平台 FQBN 提示，仅注入到代码生成（不影响需求分析）
            
        Returns:
            (项目目录路径, 需求分析结果 or None)
        """
        if output_dir is None:
            projects_dir = _paths.get_projects_dir(self.work_dir)
            output_dir = projects_dir / "arduino_projects" / project_name
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 需求分析用原始 prompt（不注入平台提示，保持分析纯净）
        requirement_analysis = None
        try:
            print("  [分析] 正在分析需求...")
            requirement_analysis = analyze_requirement(
                prompt,
                api_key=api_key,
                base_url=base_url,
                model=model,
                work_dir=self.work_dir,
            )
            print(f"  [分析] 识别到板卡: {requirement_analysis.board_type.value}")
            if requirement_analysis.components:
                print(f"  [分析] 组件: {', '.join(requirement_analysis.components)}")
            if requirement_analysis.libraries:
                print(f"  [分析] 需要的库: {', '.join(requirement_analysis.libraries)}")
            
            # 如果需要澄清，输出警告
            if requirement_analysis.needs_clarification:
                print("  [警告] 需求可能需要澄清:")
                for q in requirement_analysis.clarification_questions:
                    print(f"    - {q}")
        except Exception as e:
            log.warning("需求分析失败，继续使用原始 prompt: %s", str(e))
            print(f"  [警告] 需求分析失败，使用原始 prompt: {str(e)}")
        
        # 代码生成阶段注入平台提示
        gen_prompt = prompt
        if platform_hint:
            gen_prompt = (
                f"{prompt}\n\n"
                f"【重要：目标平台 FQBN 为 {platform_hint}，请确保代码兼容该平台的 API。"
                f"不同平台的 Wire/I2C 接口可能不同，请使用该平台支持的标准写法。】"
            )
        code = generate_arduino_code(
            gen_prompt,
            api_key=api_key,
            base_url=base_url,
            model=model,
            work_dir=self.work_dir,
            requirement_analysis=requirement_analysis,
        )
        
        # 写入 .ino 文件
        sketch_file = output_dir / f"{project_name}.ino"
        sketch_file.write_text(code, encoding="utf-8")
        log.info(f"工程已生成: {output_dir}")
        print(f"工程已生成: {output_dir}")
        
        return output_dir, requirement_analysis
    
    def build(
        self,
        project_dir: Path,
        fqbn: str,
        build_path: Optional[Path] = None,
    ) -> CompileResult:
        """编译 Arduino 工程
        
        Args:
            project_dir: 工程目录（包含 .ino 文件）
            fqbn: 板卡 FQBN
            build_path: 编译输出目录，None 时使用 project_dir/build
            
        Returns:
            编译结果
        """
        project_dir = Path(project_dir)
        if not project_dir.is_absolute():
            project_dir = self.work_dir / project_dir
        project_dir = project_dir.resolve()
        
        return self.builder.compile_sketch(project_dir, fqbn, build_path)
    
    def upload(
        self,
        project_dir: Path,
        fqbn: str,
        port: Optional[str] = None,
        auto_close_port: bool = True,
    ) -> UploadResult:
        """上传固件到板卡
        
        Args:
            project_dir: 工程目录（包含 .ino 文件）
            fqbn: 板卡 FQBN
            port: 串口，None 时自动检测
            auto_close_port: 是否自动关闭占用串口的进程
            
        Returns:
            上传结果
        """
        project_dir = Path(project_dir)
        if not project_dir.is_absolute():
            project_dir = self.work_dir / project_dir
        
        return self.uploader.upload_sketch(
            project_dir,
            fqbn,
            port=port,
            auto_close_port=auto_close_port,
        )
    
    def monitor_serial(
        self,
        port: str,
        baud_rate: int = 9600,
        duration: int = 10,
    ) -> List[str]:
        """监控串口输出
        
        Args:
            port: 串口
            baud_rate: 波特率
            duration: 监控时长（秒）
            
        Returns:
            接收到的串口输出行列表
        """
        return self.monitor.monitor_serial(port, baud_rate, duration)
    
    def demo_blink(
        self,
        board_type: str = "uno",
        pin: int = 13,
        interval: int = 1000,
        flash: bool = False,
    ) -> Path:
        """运行 LED 闪烁 Demo
        
        Args:
            board_type: 板卡类型（如 'uno', 'pico', 'nano'）
            pin: LED 引脚
            interval: 闪烁间隔（毫秒）
            flash: 是否自动上传
            
        Returns:
            生成的项目目录路径
        """
        # 检测板卡
        board = self.detect_board_by_type(board_type)
        if not board:
            raise ValueError(f"未检测到 {board_type} 板卡")
        
        fqbn = board.fqbn or f"arduino:avr:{board_type}"
        
        # 生成代码
        prompt = f"用 Arduino {board_type} 做一个 LED 闪烁，{pin} 号引脚，每 {interval} 毫秒闪烁一次"
        project_dir, _ = self.generate(prompt, "blink_demo")
        
        # 编译
        result = self.build(project_dir, fqbn)
        if not result.success:
            raise RuntimeError(f"编译失败: {result.output}")
        
        # 上传（如果需要）
        if flash:
            upload_result = self.upload(project_dir, fqbn, port=board.port)
            if not upload_result.success:
                raise RuntimeError(f"上传失败: {upload_result.message}")
        
        return project_dir
