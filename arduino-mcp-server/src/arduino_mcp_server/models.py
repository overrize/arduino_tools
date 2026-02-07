"""Data models for Arduino MCP Server"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Component(BaseModel):
    """Hardware component definition"""
    type: Literal["led", "button", "sensor"]
    name: str
    pin: int
    mode: Optional[Literal["INPUT", "OUTPUT", "INPUT_PULLUP"]] = None


class ProjectConfig(BaseModel):
    """Arduino project configuration"""
    board_fqbn: str = Field(default="arduino:avr:uno", description="Board FQBN")
    components: List[Component] = Field(default_factory=list)
    blink_interval: int = Field(default=1000, description="Blink interval in ms")
    serial_enabled: bool = Field(default=True)
    serial_baud: int = Field(default=9600)


class CompileResult(BaseModel):
    """Compilation result"""
    success: bool
    output: str
    errors: Optional[List[str]] = None
    build_path: Optional[str] = None  # Path to compiled artifacts


class UploadResult(BaseModel):
    """Upload result"""
    success: bool
    port: str
    message: str


class BoardInfo(BaseModel):
    """Detected board information"""
    port: str
    fqbn: Optional[str] = None
    name: Optional[str] = None
