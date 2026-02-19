"""Arduino 代码生成器 — 使用 LLM API"""
import logging
import re
from pathlib import Path
from typing import Optional

from .errors import LLMError
from .llm_config import get_llm_config
from .models import RequirementAnalysis

log = logging.getLogger("arduino_client")

try:
    from openai import APIError, APIStatusError, OpenAI
except ImportError:
    OpenAI = None
    APIError = Exception
    APIStatusError = Exception

API_BASE_HINT = """
若使用 Kimi/Moonshot，请在 .env 中添加：
  OPENAI_API_BASE=https://api.moonshot.cn/v1
  OPENAI_MODEL=kimi-k2-0905-preview
获取 Key: https://platform.moonshot.cn/console/api-keys
"""


SYSTEM_PROMPT = """你是一名嵌入式工程师，专门使用 Arduino 开发固件。

## 代码要求
1. **标准 Arduino API**：使用 pinMode、digitalWrite、digitalRead、analogRead、analogWrite 等
2. **库引用**：
   - 如果使用了第三方库（如 U8g2、RTClib 等），必须在代码开头使用 #include 引用
   - 例如：`#include <U8g2lib.h>` 或 `#include <RTClib.h>`
   - Arduino 标准库（如 Wire、SPI）也需要显式引用
3. **代码结构**：
   - setup() 函数：初始化引脚、串口、库对象等
   - loop() 函数：主循环
   - 全局变量：在文件顶部定义引脚常量、库对象等
4. **串口输出**：
   - 使用 Serial.begin(baud_rate) 初始化（默认 9600）
   - 使用 Serial.println() 输出调试信息，帮助验证功能
   - 关键状态变化必须输出日志
5. **输出格式**：仅输出 C++ 代码，不要 markdown 标记或解释文字

## 示例（LED 闪烁，引脚 13）
```cpp
const int LED_PIN = 13;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
  Serial.println("LED Blink Started");
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  Serial.println("LED ON");
  delay(1000);
  
  digitalWrite(LED_PIN, LOW);
  Serial.println("LED OFF");
  delay(1000);
}
```

## 示例（使用库 - OLED）
```cpp
#include <U8g2lib.h>

U8G2_SSD1306_128X64_NONAME_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ SCL, /* data=*/ SDA, /* reset=*/ U8X8_PIN_NONE);

void setup() {
  Serial.begin(9600);
  u8g2.begin();
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr);
  u8g2.drawStr(0, 20, "Hello World!");
  u8g2.sendBuffer();
  Serial.println("OLED initialized");
}

void loop() {
  // 主循环
}
```

根据用户需求生成 Arduino 代码。确保包含所有必要的库引用和初始化代码。"""


def check_code_safety(code: str) -> tuple[bool, list[str]]:
    """检查 LLM 生成代码的安全性。返回 (是否安全, 警告列表)"""
    warnings: list[str] = []
    # 危险系统调用（Arduino 不应包含）
    dangerous = [
        (r"system\s*\(", "system()"),
        (r"exec[lv]?\s*\(", "exec*()"),
        (r"popen\s*\(", "popen()"),
    ]
    for pat, name in dangerous:
        if re.search(pat, code):
            warnings.append(f"检测到可疑调用: {name}")
    
    return (len(warnings) == 0, warnings)


def generate_arduino_code(
    user_prompt: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    work_dir: Optional[Path] = None,
    requirement_analysis: Optional[RequirementAnalysis] = None,
) -> str:
    """根据自然语言需求生成 Arduino 代码。支持 OpenAI、Kimi(Moonshot) 等兼容 API"""
    if OpenAI is None:
        raise RuntimeError("请安装 openai: pip install openai")
    
    cfg_key, cfg_base, cfg_model = get_llm_config(work_dir)
    api_key = api_key or cfg_key
    base_url = base_url or cfg_base
    model = model or cfg_model
    
    if not api_key:
        raise ValueError(
            "未设置 OPENAI_API_KEY 或 ARDUINO_CLIENT_API_KEY，请先配置。"
            "运行 python -m arduino_client 查看配置说明。"
        )
    
    client_kw = {"api_key": api_key}
    if base_url:
        client_kw["base_url"] = base_url.rstrip("/")
    
    client = OpenAI(**client_kw)
    log.info("模型: %s, base: %s", model, base_url or "default")
    print(f"  [生成] 使用模型: {model}")
    
    # 如果有需求分析结果，增强 prompt
    enhanced_prompt = user_prompt
    if requirement_analysis:
        analysis_info = []
        if requirement_analysis.libraries:
            analysis_info.append(f"需要的库: {', '.join(requirement_analysis.libraries)}")
        if requirement_analysis.components:
            analysis_info.append(f"组件: {', '.join(requirement_analysis.components)}")
        if requirement_analysis.pins:
            pin_info = ", ".join([f"{k}={v}" for k, v in requirement_analysis.pins.items()])
            analysis_info.append(f"引脚配置: {pin_info}")
        
        if analysis_info:
            enhanced_prompt = f"""{user_prompt}

【需求分析信息】
{chr(10).join(analysis_info)}

请确保代码中包含上述库的引用（使用 #include），并正确使用指定的引脚配置。"""
        log.info("使用需求分析结果增强 prompt")
    
    print("  [生成] 正在调用 API...")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": enhanced_prompt},
            ],
            temperature=0.2,
        )
    except (APIStatusError, APIError) as e:
        err_msg = str(e).lower()
        if "401" in err_msg or "invalid_api_key" in err_msg:
            if not base_url:
                raise LLMError(
                    f"API Key 无效或未设置。\n"
                    f"请在 .env 中配置 OPENAI_API_KEY。{API_BASE_HINT}"
                ) from e
            raise LLMError(
                f"API Key 无效（{base_url}）。请检查 .env 中的 OPENAI_API_KEY 是否正确。"
            ) from e
        if "429" in str(e) or "rate_limit" in err_msg:
            raise LLMError("API 请求频率超限，请稍后重试。") from e
        if "timeout" in err_msg:
            raise LLMError("API 请求超时，请检查网络连接。") from e
        raise LLMError(f"API 调用失败: {str(e)[:200]}") from e
    
    content = resp.choices[0].message.content or ""
    log.debug("原始响应长度: %d", len(content))
    print(f"  [生成] 收到响应 ({len(content)} 字符)")
    
    # 去除 markdown 代码块
    if "```cpp" in content:
        content = content.split("```cpp", 1)[1].split("```", 1)[0].strip()
    elif "```c" in content:
        content = content.split("```c", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()
    
    log.info("解析后代码长度: %d", len(content))
    lines = content.count("\n") + 1 if content else 0
    print(f"  [生成] 解析代码块完成，输出 {lines} 行")
    
    safe, warnings = check_code_safety(content)
    if not safe:
        for w in warnings:
            log.warning("生成代码安全检查: %s", w)
            print(f"  [警告] {w}")
    
    return content


FIX_SYSTEM_PROMPT = """你是一名嵌入式工程师。用户提供的 Arduino C++ 代码编译失败，你需要根据编译错误修正代码。
- 使用标准 Arduino API（pinMode、digitalWrite 等）
- 根据错误信息定位问题并修正（如语法、类型、未定义变量等）
- 只输出修正后的完整 C++ 代码，不要解释
"""


def generate_arduino_code_fix(
    original_prompt: str,
    current_code: str,
    build_error: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    work_dir: Optional[Path] = None,
) -> str:
    """根据编译错误修正 Arduino 代码，返回修正后的代码"""
    if OpenAI is None:
        raise RuntimeError("请安装 openai: pip install openai")
    
    cfg_key, cfg_base, cfg_model = get_llm_config(work_dir)
    api_key = api_key or cfg_key
    base_url = base_url or cfg_base
    model = model or cfg_model
    
    if not api_key:
        raise ValueError("未设置 OPENAI_API_KEY 或 ARDUINO_CLIENT_API_KEY")
    
    user_content = f"""【原始需求】
{original_prompt}

【当前代码（编译失败）】
```cpp
{current_code}
```

【编译错误】
{build_error}

请根据上述编译错误修正代码，只输出修正后的完整 C++ 代码，不要解释。"""
    
    client_kw = {"api_key": api_key}
    if base_url:
        client_kw["base_url"] = base_url.rstrip("/")
    client = OpenAI(**client_kw)
    
    log.info("修复编译错误，模型: %s", model)
    print("  [修复] 根据编译错误请求模型修正...")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": FIX_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
    )
    content = resp.choices[0].message.content or ""
    if "```cpp" in content:
        content = content.split("```cpp", 1)[1].split("```", 1)[0].strip()
    elif "```c" in content:
        content = content.split("```c", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()
    log.info("修复后代码长度: %d", len(content))
    print(f"  [修复] 收到修正代码 ({len(content)} 字符)")
    return content
