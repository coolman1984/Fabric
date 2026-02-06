use serde::{Deserialize, Serialize};
use tauri::{Window, Emitter};
use reqwest::Client;
use futures::StreamExt;
use serde_json::json;

#[derive(Deserialize)]
pub struct AIRequest {
    pub vendor: String,
    pub model: String,
    pub api_key: String,
    pub system_prompt: String,
    pub user_input: String,
    pub temperature: f32,
    pub top_p: f32,
    pub thinking_level: Option<i32>, // Added for Gemini 3
}

#[derive(Serialize, Clone)]
pub struct AIChunk {
    pub chunk: String,
}

#[tauri::command]
pub async fn run_pattern(
    window: Window,
    request: AIRequest,
) -> Result<(), String> {
    let result = match request.vendor.as_str() {
        "google" => call_gemini(window.clone(), request).await,
        "openai" => call_openai(window.clone(), request).await,
        "anthropic" => call_anthropic(window.clone(), request).await,
        _ => Err("Unsupported vendor".to_string()),
    };
    
    // Emit completion signal
    match &result {
        Ok(_) => {
            let _ = window.emit("ai-complete", json!({"success": true}));
        }
        Err(e) => {
            let _ = window.emit("ai-chunk", AIChunk { chunk: format!("\n\n❌ **Error:** {}\n", e) });
            let _ = window.emit("ai-complete", json!({"success": false, "error": e}));
        }
    }
    
    result
}

async fn call_gemini(window: Window, req: AIRequest) -> Result<(), String> {
    let client = Client::new();
    let url = format!(
        "https://generativelanguage.googleapis.com/v1beta/models/{}:streamGenerateContent?key={}&alt=sse",
        req.model, req.api_key
    );

    let mut payload = json!({
        "contents": [
            {
                "parts": [
                    {"text": req.system_prompt},
                    {"text": req.user_input}
                ]
            }
        ],
        "generationConfig": {
            "temperature": req.temperature,
            "topP": req.top_p,
        }
    });

    // Add thinkingConfig if reasoning is enabled (Gemini 3)
    // Values: HIGH (deep), MEDIUM, LOW, MINIMAL (Flash only)
    if let Some(level) = req.thinking_level {
        if level > 0 {
            if let Some(config) = payload.get_mut("generationConfig") {
                if let Some(config_obj) = config.as_object_mut() {
                    let thinking_level = match level {
                        2 => "HIGH",      // Deep reasoning
                        1 => "MEDIUM",    // Normal reasoning
                        _ => "LOW",       // Minimal reasoning
                    };
                    config_obj.insert("thinkingConfig".to_string(), json!({
                        "thinkingLevel": thinking_level
                    }));
                }
            }
        }
    }

    let res = client.post(&url)
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("Network error: {}", e))?;

    // Check HTTP status
    let status = res.status();
    if !status.is_success() {
        let error_text = res.text().await.unwrap_or_default();
        
        // Parse error for user-friendly message
        let friendly_error = if error_text.contains("API_KEY") || error_text.contains("api_key") {
            format!("Invalid Google API Key. Please check your API key in Settings (Ctrl+S).")
        } else if error_text.contains("404") || error_text.contains("not found") || error_text.contains("NOT_FOUND") {
            format!("Model '{}' not found. Please select a different model.", req.model)
        } else if error_text.contains("RATE_LIMIT") || error_text.contains("429") {
            "API rate limit exceeded. Please wait a moment and try again.".to_string()
        } else if error_text.contains("quota") || error_text.contains("QUOTA") {
            "API quota exceeded. Please check your Google Cloud billing.".to_string()
        } else {
            format!("API Error ({}): {}", status, &error_text[..error_text.len().min(300)])
        };
        
        return Err(friendly_error);
    }

    let mut stream = res.bytes_stream();
    let mut has_content = false;

    while let Some(item) = stream.next().await {
        let chunk = item.map_err(|e| format!("Stream error: {}", e))?;
        let text = String::from_utf8_lossy(&chunk);
        
        for line in text.lines() {
            if line.starts_with("data: ") {
                let json_str = &line[6..];
                if let Ok(json) = serde_json::from_str::<serde_json::Value>(json_str) {
                    // Check for API error in response
                    if let Some(error) = json.get("error") {
                        let msg = error.get("message")
                            .and_then(|m| m.as_str())
                            .unwrap_or("Unknown API error");
                        return Err(msg.to_string());
                    }
                    
                    if let Some(candidates) = json.get("candidates") {
                        if let Some(content) = candidates[0].get("content") {
                            if let Some(parts) = content.get("parts") {
                                if let Some(text_part) = parts[0].get("text") {
                                    if let Some(chunk_text) = text_part.as_str() {
                                        has_content = true;
                                        window.emit("ai-chunk", AIChunk { chunk: chunk_text.to_string() }).map_err(|e| e.to_string())?;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    if !has_content {
        return Err("No response received from AI. Please check your API key and model selection.".to_string());
    }

    Ok(())
}

async fn call_openai(window: Window, req: AIRequest) -> Result<(), String> {
    let client = Client::new();
    let url = "https://api.openai.com/v1/chat/completions";

    let payload = json!({
        "model": req.model,
        "messages": [
            {"role": "system", "content": req.system_prompt},
            {"role": "user", "content": req.user_input}
        ],
        "temperature": req.temperature,
        "top_p": req.top_p,
        "stream": true
    });

    let res = client.post(url)
        .header("Authorization", format!("Bearer {}", req.api_key))
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("Network error: {}", e))?;

    let status = res.status();
    if !status.is_success() {
        let error_text = res.text().await.unwrap_or_default();
        return Err(format!("OpenAI API Error ({}): {}", status, &error_text[..error_text.len().min(300)]));
    }

    let mut stream = res.bytes_stream();
    let mut has_content = false;

    while let Some(item) = stream.next().await {
        let chunk = item.map_err(|e| e.to_string())?;
        let text = String::from_utf8_lossy(&chunk);
        
        for line in text.lines() {
            if line.starts_with("data: ") {
                let json_str = &line[6..];
                if json_str == "[DONE]" { break; }
                if let Ok(json) = serde_json::from_str::<serde_json::Value>(json_str) {
                    if let Some(choices) = json.get("choices") {
                        if let Some(delta) = choices[0].get("delta") {
                            if let Some(content) = delta.get("content") {
                                if let Some(chunk_text) = content.as_str() {
                                    has_content = true;
                                    window.emit("ai-chunk", AIChunk { chunk: chunk_text.to_string() }).map_err(|e| e.to_string())?;
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    if !has_content {
        return Err("No response received from OpenAI. Please check your API key.".to_string());
    }

    Ok(())
}

async fn call_anthropic(window: Window, req: AIRequest) -> Result<(), String> {
    let client = Client::new();
    let url = "https://api.anthropic.com/v1/messages";

    let payload = json!({
        "model": req.model,
        "system": req.system_prompt,
        "messages": [
            {"role": "user", "content": req.user_input}
        ],
        "max_tokens": 4096,
        "stream": true
    });

    let res = client.post(url)
        .header("x-api-key", &req.api_key)
        .header("anthropic-version", "2023-06-01")
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("Network error: {}", e))?;

    let status = res.status();
    if !status.is_success() {
        let error_text = res.text().await.unwrap_or_default();
        return Err(format!("Anthropic API Error ({}): {}", status, &error_text[..error_text.len().min(300)]));
    }

    let mut stream = res.bytes_stream();
    let mut has_content = false;

    while let Some(item) = stream.next().await {
        let chunk = item.map_err(|e| e.to_string())?;
        let text = String::from_utf8_lossy(&chunk);
        
        for line in text.lines() {
            if line.starts_with("data: ") {
                let json_str = &line[6..];
                if let Ok(json) = serde_json::from_str::<serde_json::Value>(json_str) {
                    if let Some(type_val) = json.get("type") {
                        if type_val == "content_block_delta" {
                            if let Some(delta) = json.get("delta") {
                                if let Some(content_text) = delta.get("text") {
                                    if let Some(chunk_text) = content_text.as_str() {
                                        has_content = true;
                                        window.emit("ai-chunk", AIChunk { chunk: chunk_text.to_string() }).map_err(|e| e.to_string())?;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    if !has_content {
        return Err("No response received from Anthropic. Please check your API key.".to_string());
    }

    Ok(())
}
