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

## 核心原则：功能优先、零依赖

**必须优先使用零依赖实现（bare-metal）**，不依赖任何第三方库。原因：
- 第三方库经常与目标平台不兼容（如 mbed_rp2040 的 Wire 库不支持自定义引脚）
- 库的驱动 IC 假设可能与实际硬件不匹配（如 SH1107 vs SSD1327）
- 零依赖代码可控、可调试、一次编译通过

### 外设实现策略
- **I2C 设备（OLED、传感器等）**：使用软件 I2C（bit-bang GPIO），不依赖 Wire 库
- **OLED 显示屏**：直接通过 I2C 发送命令/数据，自带字体数组，不使用 U8g2/Adafruit 等库
- **传感器（DHT、DS18B20 等）**：直接实现通信协议（单总线、I2C 寄存器读写）
- **SPI 设备**：优先软件 SPI（bit-bang），除非用户明确要求硬件 SPI
- **仅在用户明确要求使用某个库时**，才使用第三方库

### I2C 软件实现模板
对于 I2C 设备，必须包含以下基础设施：
1. 软件 I2C 函数：i2cSetup/i2cStart/i2cStop/i2cTx
2. setup() 中执行 I2C 总线扫描，通过 Serial 输出发现的设备地址
3. 基于扫描到的地址进行通信

### 平台特殊注意
- **RP2040 (Pico)**：避免使用 Wire 库（I2C 引脚映射有限制）；变量名避免与平台宏冲突（不要用 I2C_SDA/I2C_SCL 等名称）
- **ESP32**：Wire 库可用但仍优先软件实现以保证引脚灵活性
- **AVR (Uno/Nano)**：资源有限，更应避免大型库

## 代码结构
1. 文件顶部：引脚常量定义
2. I2C / 通信协议底层函数
3. 外设驱动函数（如 OLED 初始化、写字符）
4. 应用逻辑
5. setup()：初始化引脚 → Serial.begin → I2C 扫描 → 外设初始化
6. loop()：主循环

## 串口输出（关键）
- 使用 Serial.begin(115200) 初始化
- setup() 中输出启动信息、I2C 扫描结果
- 关键状态变化必须输出日志（便于后续调试）

## 输出格式
仅输出 C++ 代码，不要 markdown 标记或解释文字。"""


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

## 修复原则
1. 使用标准 Arduino API（pinMode、digitalWrite 等）
2. 根据错误信息定位问题并修正（语法、类型、未定义变量等）
3. **禁止通过引入第三方库来解决问题** — 如果错误是缺少头文件或库，应改为零依赖实现
4. 如果错误涉及平台不兼容（如 Wire 库引脚、特定宏冲突），改用软件实现绕过
5. 变量名避免与平台宏冲突（如 RP2040 上不要用 I2C_SDA/I2C_SCL）
6. 只输出修正后的完整 C++ 代码，不要解释
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


REVIEW_SYSTEM_PROMPT = """你是一名嵌入式工程师，负责审查 Arduino 代码是否满足用户需求。

用户会提供：
1. 需求描述（自然语言）
2. 现有 Arduino C++ 代码
3. 目标平台 FQBN

你需要判断现有代码是否已满足需求，并以 JSON 格式返回：

```json
{
  "satisfied": true/false,
  "reason": "简要说明（一句话）",
  "code": null 或 "修改后的完整 C++ 代码"
}
```

规则：
- 如果代码已经满足需求（功能、引脚、组件都匹配）→ satisfied=true, code=null
- 如果代码需要修改 → satisfied=false, code="修改后的完整代码"
- **零依赖原则**：修改时不得引入新的第三方库；外设驱动应直接实现（软件 I2C、直接寄存器操作）
- code 字段只放纯 C++ 代码，不要 markdown 标记
- 代码必须兼容指定的目标平台 FQBN
- 只返回 JSON，不要其他文字"""


def review_and_patch_code(
    user_prompt: str,
    existing_code: str,
    target_fqbn: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    work_dir: Optional[Path] = None,
) -> tuple[bool, Optional[str], str]:
    """审查现有代码是否满足需求，不满足则返回修改后的代码。

    Returns:
        (satisfied, patched_code_or_none, reason)
    """
    import json as _json

    if OpenAI is None:
        raise RuntimeError("请安装 openai: pip install openai")

    cfg_key, cfg_base, cfg_model = get_llm_config(work_dir)
    api_key = api_key or cfg_key
    base_url = base_url or cfg_base
    model = model or cfg_model

    if not api_key:
        raise ValueError("未设置 OPENAI_API_KEY 或 ARDUINO_CLIENT_API_KEY")

    user_content = f"""【需求描述】
{user_prompt}

【目标平台 FQBN】
{target_fqbn}

【现有代码】
```cpp
{existing_code}
```

请判断现有代码是否满足上述需求，返回 JSON。"""

    client_kw = {"api_key": api_key}
    if base_url:
        client_kw["base_url"] = base_url.rstrip("/")
    client = OpenAI(**client_kw)

    log.info("审查现有代码，模型: %s", model)
    print("  [审查] 正在检查现有代码是否满足需求...")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
    )

    raw = resp.choices[0].message.content or ""
    log.debug("审查响应: %s", raw[:500])

    # 提取 JSON
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not json_match:
        log.warning("审查响应不是 JSON，视为不满足")
        return False, None, "无法解析审查结果"

    try:
        data = _json.loads(json_match.group(0))
    except _json.JSONDecodeError:
        log.warning("审查 JSON 解析失败")
        return False, None, "无法解析审查结果"

    satisfied = data.get("satisfied", False)
    reason = data.get("reason", "")
    code = data.get("code")

    # 清理 code 中可能的 markdown 包裹
    if code and "```" in code:
        if "```cpp" in code:
            code = code.split("```cpp", 1)[1].split("```", 1)[0].strip()
        elif "```c" in code:
            code = code.split("```c", 1)[1].split("```", 1)[0].strip()
        elif "```" in code:
            code = code.split("```", 1)[1].split("```", 1)[0].strip()

    return satisfied, code if not satisfied else None, reason


DEBUG_SYSTEM_PROMPT = """你是一名嵌入式硬件调试工程师。

用户提供：
1. 当前 Arduino 代码
2. 串口输出（Serial Monitor 捕获）
3. 用户描述的问题现象
4. 硬件信息（板卡 FQBN、引脚接线等）

## 调试原则
1. **功能优先**：先确保每个组件能独立工作，再整合
2. **零依赖**：修复代码时不得引入新的第三方库；如果问题是库导致的，应改为直接实现
3. **增量验证**：如果多个组件不工作，先隔离测试单个组件
4. **诊断输出**：在关键节点增加 Serial.println，便于定位问题
5. **平台感知**：注意目标平台的限制（如 RP2040 的 Wire 引脚限制、宏名冲突等）

## 常见陷阱
- I2C 库（Wire）在某些平台上不支持自定义引脚 → 用软件 I2C
- OLED 驱动 IC 猜错（SH1107 vs SSD1306 vs SSD1327）→ 先用 0xA5（全亮）测试通信
- 变量名与平台宏冲突 → 使用独特前缀（如 OLED_SDA 而非 I2C_SDA）
- 按键去抖逻辑 bug → 分离 raw 状态和 debounced 状态

返回格式（JSON）：
```json
{
  "diagnosis": "根因分析（2-3 句话）",
  "changes": "做了哪些修改（简要列表）",
  "code": "修复后的完整 C++ 代码"
}
```

规则：
- code 字段放纯 C++ 代码，不要 markdown 标记
- 保留或增加 Serial.println 输出
- 只返回 JSON"""


def diagnose_with_serial(
    current_code: str,
    serial_output: str,
    issue_description: str,
    hardware_info: str = "",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    work_dir: Optional[Path] = None,
) -> tuple[str, str, Optional[str]]:
    """根据串口输出和问题描述诊断并修复代码。

    Returns:
        (diagnosis, changes_summary, fixed_code_or_none)
    """
    import json as _json

    if OpenAI is None:
        raise RuntimeError("请安装 openai: pip install openai")

    cfg_key, cfg_base, cfg_model = get_llm_config(work_dir)
    api_key = api_key or cfg_key
    base_url = base_url or cfg_base
    model = model or cfg_model

    if not api_key:
        raise ValueError("未设置 OPENAI_API_KEY 或 ARDUINO_CLIENT_API_KEY")

    serial_section = serial_output.strip() if serial_output.strip() else "（无串口输出）"

    user_content = f"""【当前代码】
```cpp
{current_code}
```

【串口输出】
{serial_section}

【问题描述】
{issue_description}

【硬件信息】
{hardware_info}

请诊断问题并返回修复后的完整代码（JSON 格式）。"""

    client_kw = {"api_key": api_key}
    if base_url:
        client_kw["base_url"] = base_url.rstrip("/")
    client = OpenAI(**client_kw)

    log.info("串口诊断，模型: %s", model)
    print("  [诊断] 正在分析串口输出和问题...")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": DEBUG_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
    )

    raw = resp.choices[0].message.content or ""
    log.debug("诊断响应: %s", raw[:500])

    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not json_match:
        return "无法解析诊断结果", "", None

    try:
        data = _json.loads(json_match.group(0))
    except _json.JSONDecodeError:
        return "诊断 JSON 解析失败", "", None

    diagnosis = data.get("diagnosis", "")
    changes = data.get("changes", "")
    code = data.get("code")

    if code and "```" in code:
        if "```cpp" in code:
            code = code.split("```cpp", 1)[1].split("```", 1)[0].strip()
        elif "```c" in code:
            code = code.split("```c", 1)[1].split("```", 1)[0].strip()
        elif "```" in code:
            code = code.split("```", 1)[1].split("```", 1)[0].strip()

    return diagnosis, changes, code


_HEADER_TO_LIB = {
    "U8g2lib.h": "U8g2",
    "U8x8lib.h": "U8g2",
    "RTClib.h": "RTClib",
    "Adafruit_GFX.h": "Adafruit GFX Library",
    "Adafruit_SSD1306.h": "Adafruit SSD1306",
    "Adafruit_NeoPixel.h": "Adafruit NeoPixel",
    "DHT.h": "DHT sensor library",
    "OneWire.h": "OneWire",
    "DallasTemperature.h": "DallasTemperature",
    "LiquidCrystal_I2C.h": "LiquidCrystal I2C",
    "IRremote.h": "IRremote",
    "Stepper.h": "Stepper",
    "AccelStepper.h": "AccelStepper",
    "FastLED.h": "FastLED",
    "SD.h": "SD",
    "WiFi.h": "WiFi",
    "PubSubClient.h": "PubSubClient",
    "ArduinoJson.h": "ArduinoJson",
}

_BUILTIN_HEADERS = {
    "Arduino.h", "Wire.h", "SPI.h", "Serial.h", "Servo.h",
    "EEPROM.h", "SoftwareSerial.h", "HardwareSerial.h",
    "math.h", "string.h", "stdlib.h", "stdio.h", "stdint.h",
}


def extract_includes_from_code(code: str) -> list[str]:
    """从 Arduino 代码的 #include 行提取库名（映射为 arduino-cli 可安装名称）。"""
    seen: set[str] = set()
    libs: list[str] = []
    for match in re.finditer(r'#include\s*[<"](\S+?)[>"]', code):
        header = match.group(1)
        if header in _BUILTIN_HEADERS:
            continue
        lib_name = _HEADER_TO_LIB.get(header, header.replace(".h", ""))
        if lib_name not in seen:
            seen.add(lib_name)
            libs.append(lib_name)
    return libs
