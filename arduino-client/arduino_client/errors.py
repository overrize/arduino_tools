"""Arduino Client 异常层次 — 统一错误处理"""


class ArduinoClientError(Exception):
    """Arduino Client 基础异常"""
    pass


class ConfigurationError(ArduinoClientError):
    """配置错误（用户可修复，如 arduino-cli 未安装、API Key 缺失）"""
    pass


class BuildError(ArduinoClientError):
    """编译错误（arduino-cli 编译失败）"""
    pass


class LLMError(ArduinoClientError):
    """LLM 相关错误（API 调用失败、认证失败等）"""
    pass


class HardwareError(ArduinoClientError):
    """硬件相关错误（上传失败、板卡未检测到等）"""
    pass


class BoardDetectionError(ArduinoClientError):
    """板卡检测错误"""
    pass
