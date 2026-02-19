"""Arduino Client 数据模型"""
from typing import List, Optional, Literal, Dict
from enum import Enum
from pydantic import BaseModel, Field


class Component(BaseModel):
    """硬件组件定义"""
    type: Literal["led", "button", "sensor"]
    name: str
    pin: int
    mode: Optional[Literal["INPUT", "OUTPUT", "INPUT_PULLUP"]] = None


class ProjectConfig(BaseModel):
    """Arduino 项目配置"""
    board_fqbn: str = Field(default="arduino:avr:uno", description="板卡 FQBN")
    components: List[Component] = Field(default_factory=list)
    blink_interval: int = Field(default=1000, description="闪烁间隔（毫秒）")
    serial_enabled: bool = Field(default=True)
    serial_baud: int = Field(default=9600)


class CompileResult(BaseModel):
    """编译结果"""
    success: bool
    output: str
    errors: Optional[List[str]] = None
    build_path: Optional[str] = None  # 编译产物路径


class UploadResult(BaseModel):
    """上传结果"""
    success: bool
    port: str
    message: str


class BoardInfo(BaseModel):
    """检测到的板卡信息"""
    port: str
    fqbn: Optional[str] = None
    name: Optional[str] = None


class BoardType(str, Enum):
    """支持的开发板类型"""
    UNO = "arduino:avr:uno"
    NANO = "arduino:avr:nano"
    PICO = "rp2040:rp2040:rpipico"
    ESP32 = "esp32:esp32:esp32"
    CUSTOM = "custom"  # 自定义板子


class RequirementAnalysis(BaseModel):
    """需求分析结果"""
    board_type: BoardType = Field(..., description="识别的板卡类型")
    components: List[str] = Field(default_factory=list, description="识别的组件列表")
    libraries: List[str] = Field(default_factory=list, description="需要的库")
    pins: Dict[str, int] = Field(default_factory=dict, description="引脚需求")
    functions: List[str] = Field(default_factory=list, description="功能列表")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="识别置信度 (0-1)")
    needs_clarification: bool = Field(False, description="是否需要澄清")
    clarification_questions: List[str] = Field(default_factory=list, description="澄清问题列表")
    raw_analysis: Optional[str] = Field(None, description="原始分析文本")


class MonitorResult(BaseModel):
    """监控结果"""
    output: List[str] = Field(default_factory=list, description="串口输出")
    duration: float = Field(0.0, description="监控时长（秒）")
    matched_patterns: List[str] = Field(default_factory=list, description="匹配的期望模式")
