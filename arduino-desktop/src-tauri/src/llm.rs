use crate::project::LLMConfig;
use reqwest;
use serde_json::json;

const ARDUINO_SYSTEM_PROMPT: &str = r#"你是 Arduino 嵌入式开发专家。

生成 Arduino 代码必须遵循以下原则：

1. **零依赖优先** - 不依赖第三方库（U8g2、Adafruit、RTClib 等），直接操作硬件
2. **软件 I2C/SPI** - 使用 bit-bang 实现，不依赖 Wire/SPI 库
3. **setup() 必须包含**:
   - Serial.begin(115200) - 调试输出
   - 每个组件的独立初始化验证（通过 Serial 输出结果）

4. **引脚定义** - 使用清晰的宏定义，如：
   #define LED_PIN 13
   #define BUTTON_PIN 2

5. **调试输出** - 关键操作后输出状态信息到 Serial

6. **平台兼容**:
   - AVR (Uno/Nano): 标准 Arduino API
   - RP2040 (Pico): 使用 mbed_rp2040 核心
   - ESP32: 使用标准 ESP32 Arduino 核心

生成的代码必须是完整可编译的 .ino 文件。"#;

pub async fn generate_arduino_code(
    prompt: &str,
    board: &str,
    config: &LLMConfig,
) -> Result<String, String> {
    if config.api_key.is_empty() {
        return Err("API Key not configured".to_string());
    }

    let client = reqwest::Client::new();
    
    let request_body = json!({
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": ARDUINO_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": format!("Board: {}\n需求: {}\n\n请生成完整的 Arduino 代码（.ino 文件），包含所有必要的初始化和调试输出。", board, prompt)
            }
        ],
        "temperature": 0.2,
    });

    let response = client
        .post(format!("{}/chat/completions", config.base_url))
        .header("Authorization", format!("Bearer {}", config.api_key))
        .header("Content-Type", "application/json")
        .json(&request_body)
        .send()
        .await
        .map_err(|e| format!("HTTP request failed: {}", e))?;

    let status = response.status();
    let response_text = response
        .text()
        .await
        .map_err(|e| format!("Failed to read response: {}", e))?;

    if !status.is_success() {
        return Err(format!("API error ({}): {}", status, response_text));
    }

    let response_json: serde_json::Value = serde_json::from_str(&response_text)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    let content = response_json["choices"][0]["message"]["content"]
        .as_str()
        .ok_or("Invalid response format")?;

    let code = extract_code_block(content);
    Ok(code)
}

fn extract_code_block(content: &str) -> String {
    if content.contains("```cpp") {
        content.split("```cpp").nth(1)
            .and_then(|s| s.split("```").next())
            .unwrap_or(content)
            .trim()
            .to_string()
    } else if content.contains("```c") {
        content.split("```c").nth(1)
            .and_then(|s| s.split("```").next())
            .unwrap_or(content)
            .trim()
            .to_string()
    } else if content.contains("```") {
        content.split("```").nth(1)
            .and_then(|s| s.split("```").next())
            .unwrap_or(content)
            .trim()
            .to_string()
    } else {
        content.trim().to_string()
    }
}

pub async fn validate_config(config: &LLMConfig) -> Result<bool, String> {
    if config.api_key.is_empty() {
        return Ok(false);
    }

    let client = reqwest::Client::new();
    
    let request_body = json!({
        "model": config.model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5,
    });

    let response = client
        .post(format!("{}/chat/completions", config.base_url))
        .header("Authorization", format!("Bearer {}", config.api_key))
        .header("Content-Type", "application/json")
        .json(&request_body)
        .send()
        .await;

    match response {
        Ok(resp) => Ok(resp.status().is_success()),
        Err(_) => Ok(false),
    }
}

const FIX_SYSTEM_PROMPT: &str = r#"你是一名嵌入式工程师。用户提供的 Arduino C++ 代码编译失败，你需要根据编译错误修正代码。

## 修复原则
1. 使用标准 Arduino API（pinMode、digitalWrite 等）
2. 根据错误信息定位问题并修正（语法、类型、未定义变量等）
3. **禁止通过引入第三方库来解决问题** — 如果错误是缺少头文件或库，应改为零依赖实现
4. 如果错误涉及平台不兼容（如 Wire 库引脚、特定宏冲突），改用软件实现绕过
5. 变量名避免与平台宏冲突（如 RP2040 上不要用 I2C_SDA/I2C_SCL）
6. 只输出修正后的完整 C++ 代码，不要解释"#;

pub async fn fix_arduino_code(
    original_prompt: &str,
    current_code: &str,
    build_error: &str,
    board: &str,
    config: &LLMConfig,
) -> Result<String, String> {
    if config.api_key.is_empty() {
        return Err("API Key not configured".to_string());
    }

    let client = reqwest::Client::new();
    
    let user_content = format!(r#"【原始需求】
{}

【目标平台】
{}

【当前代码（编译失败）】
```cpp
{}
```

【编译错误】
{}

请根据上述编译错误修正代码，只输出修正后的完整 C++ 代码，不要解释。"#,
        original_prompt, board, current_code, build_error
    );
    
    let request_body = json!({
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": FIX_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
        "temperature": 0.1,
    });

    let response = client
        .post(format!("{}/chat/completions", config.base_url))
        .header("Authorization", format!("Bearer {}", config.api_key))
        .header("Content-Type", "application/json")
        .json(&request_body)
        .send()
        .await
        .map_err(|e| format!("HTTP request failed: {}", e))?;

    let status = response.status();
    let response_text = response
        .text()
        .await
        .map_err(|e| format!("Failed to read response: {}", e))?;

    if !status.is_success() {
        return Err(format!("API error ({}): {}", status, response_text));
    }

    let response_json: serde_json::Value = serde_json::from_str(&response_text)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    let content = response_json["choices"][0]["message"]["content"]
        .as_str()
        .ok_or("Invalid response format")?;

    let code = extract_code_block(content);
    Ok(code)
}

const DEBUG_SYSTEM_PROMPT: &str = r#"你是一名嵌入式硬件调试工程师。

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
- 只返回 JSON"#;

#[derive(Debug, serde::Serialize)]
pub struct DiagnosisResult {
    pub diagnosis: String,
    pub changes: String,
    pub code: String,
}

pub async fn diagnose_with_serial(
    current_code: &str,
    serial_output: &str,
    issue_description: &str,
    hardware_info: &str,
    config: &LLMConfig,
) -> Result<DiagnosisResult, String> {
    if config.api_key.is_empty() {
        return Err("API Key not configured".to_string());
    }

    let client = reqwest::Client::new();
    
    let serial_section = if serial_output.trim().is_empty() {
        "（无串口输出）".to_string()
    } else {
        serial_output.to_string()
    };
    
    let user_content = format!(r#"【当前代码】
```cpp
{}
```

【串口输出】
{}

【问题描述】
{}

【硬件信息】
{}

请诊断问题并返回修复后的完整代码（JSON 格式）。"#,
        current_code, serial_section, issue_description, hardware_info
    );

    let request_body = json!({
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": DEBUG_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
        "temperature": 0.1,
    });

    let response = client
        .post(format!("{}/chat/completions", config.base_url))
        .header("Authorization", format!("Bearer {}", config.api_key))
        .header("Content-Type", "application/json")
        .json(&request_body)
        .send()
        .await
        .map_err(|e| format!("HTTP request failed: {}", e))?;

    let status = response.status();
    let response_text = response
        .text()
        .await
        .map_err(|e| format!("Failed to read response: {}", e))?;

    if !status.is_success() {
        return Err(format!("API error ({}): {}", status, response_text));
    }

    let response_json: serde_json::Value = serde_json::from_str(&response_text)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    let content = response_json["choices"][0]["message"]["content"]
        .as_str()
        .ok_or("Invalid response format")?;

    // Extract JSON from response
    let json_str = extract_json_block(content);
    let diagnosis_json: serde_json::Value = serde_json::from_str(&json_str)
        .map_err(|e| format!("Failed to parse diagnosis JSON: {}", e))?;

    let diagnosis = diagnosis_json["diagnosis"].as_str().unwrap_or("").to_string();
    let changes = diagnosis_json["changes"].as_str().unwrap_or("").to_string();
    let code = diagnosis_json["code"].as_str().unwrap_or("").to_string();
    
    // Clean up code if it has markdown
    let code = extract_code_block(&code);

    Ok(DiagnosisResult {
        diagnosis,
        changes,
        code,
    })
}

fn extract_json_block(content: &str) -> String {
    // Find JSON block between curly braces
    if let Some(start) = content.find('{') {
        if let Some(end) = content.rfind('}') {
            return content[start..=end].to_string();
        }
    }
    content.to_string()
}
