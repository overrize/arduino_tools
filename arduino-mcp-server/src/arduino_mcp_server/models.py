"""Arduino MCP Server 数据模型"""

from typing import List, Optional, Literal
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
