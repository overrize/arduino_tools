"""Arduino 代码生成器

负责根据项目配置生成 Arduino 代码和 Wokwi 仿真文件
"""

import logging
from pathlib import Path
from jinja2 import Template
from .models import ProjectConfig
from .templates import get_template
from .wokwi_generator import WokwiGenerator

logger = logging.getLogger(__name__)


class CodeGenerator:
    """Arduino 代码生成器类"""
    
    def __init__(self, output_dir: Path):
        """初始化代码生成器
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.wokwi_generator = WokwiGenerator()
        logger.debug(f"CodeGenerator initialized with output_dir: {output_dir}")
    
    def generate_led_blink(self, config: ProjectConfig, project_name: str, include_wokwi: bool = True) -> Path:
        """生成 LED 闪烁项目
        
        Args:
            config: 项目配置对象
            project_name: 项目名称
            include_wokwi: 是否生成 Wokwi 仿真文件
        
        Returns:
            项目目录路径
        """
        logger.info(f"Generating LED blink project: {project_name}")
        
        # 从配置中查找 LED 组件
        led = next((c for c in config.components if c.type == "led"), None)
        if not led:
            logger.error("No LED component found in config")
            raise ValueError("配置中未找到 LED 组件")
        
        logger.debug(f"LED config: pin={led.pin}, interval={config.blink_interval}ms")
        
        # 准备模板上下文数据
        context = {
            "board_fqbn": config.board_fqbn,
            "pin": led.pin,
            "interval": config.blink_interval,
            "serial_enabled": config.serial_enabled,
            "serial_baud": config.serial_baud,
        }
        
        # 使用 Jinja2 模板渲染代码
        template = Template(get_template("led_blink"))
        code = template.render(**context)
        
        # 创建项目目录结构
        project_dir = self.output_dir / project_name
        project_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        docs_dir = project_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        simulation_dir = project_dir / "simulation"
        simulation_dir.mkdir(exist_ok=True)
        
        build_dir = project_dir / "build"
        build_dir.mkdir(exist_ok=True)
        
        # 将 .ino 文件写入项目根目录
        sketch_file = project_dir / f"{project_name}.ino"
        sketch_file.write_text(code, encoding="utf-8")
        
        logger.info(f"Code generated: {sketch_file}")
        
        # 如果需要，生成 Wokwi 仿真文件
        if include_wokwi:
            self._generate_wokwi_files(project_dir, config, project_name)
        
        return project_dir
    
    def _generate_wokwi_files(self, project_dir: Path, config: ProjectConfig, project_name: str):
        """在 simulation/ 子目录中生成 Wokwi 仿真文件
        
        Args:
            project_dir: 项目根目录
            config: 项目配置
            project_name: 项目名称
        """
        logger.debug(f"Generating Wokwi files for {project_name}")
        
        # 确保 simulation 目录存在
        simulation_dir = project_dir / "simulation"
        simulation_dir.mkdir(exist_ok=True)
        
        # 生成 diagram.json（电路图）到 simulation/ 目录
        diagram = self.wokwi_generator.generate_diagram(config, project_name)
        diagram_path = simulation_dir / "diagram.json"
        self.wokwi_generator.save_diagram(diagram, str(diagram_path))
        
        # 生成 wokwi.toml（配置文件）到 simulation/ 目录
        toml_content = self.wokwi_generator.generate_wokwi_toml(config, project_name)
        toml_path = simulation_dir / "wokwi.toml"
        toml_path.write_text(toml_content, encoding="utf-8")
        
        logger.info(f"Wokwi simulation files generated: {diagram_path}, {toml_path}")
    
    def generate_button_led(self, config: ProjectConfig, project_name: str) -> Path:
        """生成按钮控制 LED 的工程"""
        # 查找组件
        button = next((c for c in config.components if c.type == "button"), None)
        led = next((c for c in config.components if c.type == "led"), None)
        
        if not button or not led:
            raise ValueError("需要按钮和 LED 组件")
        
        # 准备模板上下文
        context = {
            "board_fqbn": config.board_fqbn,
            "button_pin": button.pin,
            "led_pin": led.pin,
            "serial_enabled": config.serial_enabled,
            "serial_baud": config.serial_baud,
        }
        
        # 渲染模板
        template = Template(get_template("button_led"))
        code = template.render(**context)
        
        # 创建项目目录结构
        project_dir = self.output_dir / project_name
        project_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        docs_dir = project_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        simulation_dir = project_dir / "simulation"
        simulation_dir.mkdir(exist_ok=True)
        
        build_dir = project_dir / "build"
        build_dir.mkdir(exist_ok=True)
        
        # 在项目根目录写入 .ino 文件
        sketch_file = project_dir / f"{project_name}.ino"
        sketch_file.write_text(code, encoding="utf-8")
        
        return project_dir
