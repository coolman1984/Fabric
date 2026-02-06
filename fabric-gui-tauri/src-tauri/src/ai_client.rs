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
    match request.vendor.as_str() {
        "google" => call_gemini(window, request).await,
        "openai" => call_openai(window, request).await,
        "anthropic" => call_anthropic(window, request).await,
        _ => Err("Unsupported vendor".to_string()),
    }
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

    // Add thinkingLevel if provided (Gemini 3 Pro reasoning)
    if let Some(level) = req.thinking_level {
        if let Some(config) = payload.get_mut("generationConfig") {
            if let Some(config_obj) = config.as_object_mut() {
                config_obj.insert("thinkingLevel".to_string(), json!(level));
            }
        }
    }

    let res = client.post(url)
        .json(&payload)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    let mut stream = res.bytes_stream();

    while let Some(item) = stream.next().await {
        let chunk = item.map_err(|e| e.to_string())?;
        let text = String::from_utf8_lossy(&chunk);
        
        for line in text.lines() {
            if line.starts_with("data: ") {
                let json_str = &line[6..];
                if let Ok(json) = serde_json::from_str::<serde_json::Value>(json_str) {
                    if let Some(candidates) = json.get("candidates") {
                        if let Some(content) = candidates[0].get("content") {
                            if let Some(parts) = content.get("parts") {
                                if let Some(text_part) = parts[0].get("text") {
                                    if let Some(chunk_text) = text_part.as_str() {
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

    Ok(())
}

async fn call_openai(window: Window, req: AIRequest) -> Result<(), String> {
    // Basic OpenAI implementation
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
        .map_err(|e| e.to_string())?;

    let mut stream = res.bytes_stream();

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
                                    window.emit("ai-chunk", AIChunk { chunk: chunk_text.to_string() }).map_err(|e| e.to_string())?;
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Ok(())
}

async fn call_anthropic(window: Window, req: AIRequest) -> Result<(), String> {
    // Basic Anthropic implementation
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
        .map_err(|e| e.to_string())?;

    let mut stream = res.bytes_stream();

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

    Ok(())
}
