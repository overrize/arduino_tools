"""需求分析模块 — 使用 LLM 分析用户需求，提取板卡类型、组件、库等信息"""
import json
import logging
import re
from pathlib import Path
from typing import Optional

from .errors import LLMError
from .llm_config import get_llm_config
from .models import RequirementAnalysis, BoardType

log = logging.getLogger("arduino_client")

try:
    from openai import APIError, APIStatusError, OpenAI
except ImportError:
    OpenAI = None
    APIError = Exception
    APIStatusError = Exception


ANALYSIS_SYSTEM_PROMPT = """你是一名 Arduino 需求分析专家。分析用户需求，提取以下信息并以 JSON 格式返回：

{
  "board_type": "arduino:avr:uno" | "arduino:avr:nano" | "rp2040:rp2040:rpipico" | "esp32:esp32:esp32" | "custom",
  "components": ["LED", "麦克风", "OLED", "蜂鸣器", ...],
  "libraries": ["库名1", "库名2", ...],
  "pins": {"LED": 13, "麦克风": "A0", ...},
  "functions": ["LED控制", "音频输入", "显示输出", ...],
  "confidence": 0.0-1.0,
  "needs_clarification": false,
  "clarification_questions": []
}

## 板卡类型识别规则：
- "arduino" / "uno" → arduino:avr:uno
- "nano" → arduino:avr:nano
- "pico" / "raspberry pi pico" → rp2040:rp2040:rpipico
- "esp32" → esp32:esp32:esp32
- 未明确指定 → 根据组件复杂度推断，默认 arduino:avr:uno

## 组件识别：
识别需求中提到的所有硬件组件：
- 传感器：麦克风、温度传感器、湿度传感器、光敏传感器等
- 执行器：LED、蜂鸣器、电机、舵机等
- 显示：OLED、LCD、LED矩阵等
- 其他：按钮、电位器、RTC模块等

## 库识别：
根据组件推断需要的库：
- OLED → "U8g2" 或 "Adafruit_SSD1306"
- 麦克风/音频 → "arduinoFFT" 或相关音频库
- RTC → "RTClib" 或 "DS1307RTC"
- WiFi/网络（ESP32）→ "WiFi"、"HTTPClient" 等

## 引脚识别：
从需求中提取明确的引脚号，如 "13号引脚" → {"LED": 13}

## 置信度：
- 1.0: 需求非常清晰，所有信息都明确
- 0.8-0.9: 需求清晰，部分信息可推断
- 0.6-0.7: 需求较模糊，需要推断
- <0.6: 需求不清晰，需要澄清

## 澄清问题：
如果需求不清晰（如未指定板卡类型、引脚不明确、功能描述模糊），设置 needs_clarification=true 并提供澄清问题。

只返回 JSON，不要其他解释文字。"""


def parse_board_type(board_str: str) -> BoardType:
    """从字符串解析板卡类型"""
    board_str_lower = board_str.lower()
    if "uno" in board_str_lower or board_str == "arduino:avr:uno":
        return BoardType.UNO
    elif "nano" in board_str_lower or board_str == "arduino:avr:nano":
        return BoardType.NANO
    elif "pico" in board_str_lower or "rp2040" in board_str_lower:
        return BoardType.PICO
    elif "esp32" in board_str_lower:
        return BoardType.ESP32
    elif "custom" in board_str_lower:
        return BoardType.CUSTOM
    else:
        return BoardType.UNO  # 默认


def analyze_requirement(
    prompt: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    work_dir: Optional[Path] = None,
) -> RequirementAnalysis:
    """分析用户需求，提取板卡类型、组件、库等信息
    
    Args:
        prompt: 用户需求描述
        api_key: LLM API Key
        base_url: LLM API Base URL
        model: LLM 模型名称
        work_dir: 工作目录（用于读取配置）
        
    Returns:
        RequirementAnalysis 对象
        
    Raises:
        LLMError: API 调用失败
        ValueError: 解析失败
    """
    if OpenAI is None:
        raise RuntimeError("请安装 openai: pip install openai")
    
    cfg_key, cfg_base, cfg_model = get_llm_config(work_dir)
    api_key = api_key or cfg_key
    base_url = base_url or cfg_base
    model = model or cfg_model
    
    if not api_key:
        raise ValueError(
            "未设置 OPENAI_API_KEY 或 ARDUINO_CLIENT_API_KEY，请先配置。"
        )
    
    client_kw = {"api_key": api_key}
    if base_url:
        client_kw["base_url"] = base_url.rstrip("/")
    
    client = OpenAI(**client_kw)
    log.info("分析需求，模型: %s", model)
    
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # 低温度确保一致性
            response_format={"type": "json_object"},  # 强制 JSON 输出
        )
    except (APIStatusError, APIError) as e:
        err_msg = str(e).lower()
        if "401" in err_msg or "invalid_api_key" in err_msg:
            raise LLMError("API Key 无效或未设置。") from e
        if "429" in str(e) or "rate_limit" in err_msg:
            raise LLMError("API 请求频率超限，请稍后重试。") from e
        if "timeout" in err_msg:
            raise LLMError("API 请求超时，请检查网络连接。") from e
        raise LLMError(f"API 调用失败: {str(e)[:200]}") from e
    
    content = resp.choices[0].message.content or ""
    log.debug("分析响应: %s", content[:200])
    
    # 解析 JSON
    try:
        # 尝试提取 JSON（可能被 markdown 包裹）
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        data = json.loads(content)
    except json.JSONDecodeError as e:
        log.error("JSON 解析失败: %s", content[:500])
        raise ValueError(f"无法解析分析结果: {str(e)}") from e
    
    # 转换为 RequirementAnalysis 对象
    try:
        board_type_str = data.get("board_type", "arduino:avr:uno")
        board_type = parse_board_type(board_type_str)
        
        # 处理引脚：确保值是整数
        pins = {}
        for key, value in data.get("pins", {}).items():
            if isinstance(value, (int, str)):
                # 如果是字符串，尝试提取数字（如 "A0" -> 0, "13" -> 13）
                if isinstance(value, str):
                    # 提取数字部分
                    num_match = re.search(r'\d+', value)
                    if num_match:
                        pins[key] = int(num_match.group())
                    elif value.startswith("A"):  # 模拟引脚 A0-A5
                        pins[key] = value  # 保留模拟引脚标识
                else:
                    pins[key] = value
        
        analysis = RequirementAnalysis(
            board_type=board_type,
            components=data.get("components", []),
            libraries=data.get("libraries", []),
            pins=pins,
            functions=data.get("functions", []),
            confidence=data.get("confidence", 0.8),
            needs_clarification=data.get("needs_clarification", False),
            clarification_questions=data.get("clarification_questions", []),
            raw_analysis=content,
        )
        
        log.info(
            "需求分析完成: 板卡=%s, 组件=%d, 库=%d, 置信度=%.2f",
            board_type.value,
            len(analysis.components),
            len(analysis.libraries),
            analysis.confidence,
        )
        
        return analysis
        
    except Exception as e:
        log.error("构建 RequirementAnalysis 失败: %s", str(e))
        raise ValueError(f"分析结果格式错误: {str(e)}") from e
