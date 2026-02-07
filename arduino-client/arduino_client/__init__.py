"""
Arduino Client — Arduino 自然语言端到端开发 Client
"""
__version__ = "0.1.0"
from .client import ArduinoClient
from .errors import (
    ArduinoClientError,
    BuildError,
    ConfigurationError,
    LLMError,
    HardwareError,
    BoardDetectionError,
)

__all__ = [
    "ArduinoClient",
    "ArduinoClientError",
    "ConfigurationError",
    "BuildError",
    "LLMError",
    "HardwareError",
    "BoardDetectionError",
    "__version__",
]
