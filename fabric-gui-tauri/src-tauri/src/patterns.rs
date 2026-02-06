use serde::Serialize;
use std::fs;
use std::path::PathBuf;
use home::home_dir;

#[derive(Serialize)]
pub struct Pattern {
    pub name: String,
    pub path: String,
}

pub fn get_patterns_dir() -> PathBuf {
    // 1. Check environment variable
    if let Ok(env_path) = std::env::var("FABRIC_PATTERNS_DIR") {
        let path = PathBuf::from(env_path);
        if path.exists() {
            return path;
        }
    }

    // 2. Check standard ~/.config/fabric/patterns
    if let Some(mut path) = home_dir() {
        path.push(".config");
        path.push("fabric");
        path.push("patterns");
        if path.exists() {
            return path;
        }
    }

    // 3. Check ~/.fabric/patterns
    if let Some(mut path) = home_dir() {
        path.push(".fabric");
        path.push("patterns");
        if path.exists() {
            return path;
        }
    }

    // 4. Check repo data/patterns (specific to this user's setup)
    let repo_path = PathBuf::from("G:\\Fabric\\data\\patterns");
    if repo_path.exists() {
        return repo_path;
    }

    // Default fallback
    home_dir()
        .map(|p| p.join(".config").join("fabric").join("patterns"))
        .unwrap_or_else(|| PathBuf::from(".config/fabric/patterns"))
}

#[tauri::command]
pub async fn list_patterns() -> Result<Vec<String>, String> {
    let patterns_dir = get_patterns_dir();
    
    if !patterns_dir.exists() {
        return Err("Fabric patterns directory not found. Please install Fabric first.".to_string());
    }

    let mut patterns = Vec::new();
    let entries = fs::read_dir(patterns_dir).map_err(|e| e.to_string())?;

    for entry in entries {
        if let Ok(entry) = entry {
            let path = entry.path();
            if path.is_dir() {
                if let Some(name) = path.file_name() {
                    if let Some(name_str) = name.to_str() {
                        patterns.push(name_str.to_string());
                    }
                }
            }
        }
    }

    patterns.sort();
    Ok(patterns)
}

#[tauri::command]
pub async fn get_pattern_content(name: String) -> Result<String, String> {
    let mut path = get_patterns_dir();
    path.push(name);
    path.push("system.md");

    if !path.exists() {
        return Err("Pattern content (system.md) not found.".to_string());
    }

    fs::read_to_string(path).map_err(|e| e.to_string())
}
