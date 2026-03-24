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
