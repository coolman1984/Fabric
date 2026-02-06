use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use std::process::Command;
use std::path::PathBuf;

#[tauri::command]
pub async fn get_youtube_transcript(
    app_handle: tauri::AppHandle,
    url: String,
    include_timestamps: bool,
) -> Result<String, String> {
    let python_script = app_handle
        .path()
        .resource_dir()
        .map_err(|e: tauri::Error| e.to_string())?
        .join("resources")
        .join("youtube_transcript.py");

    let mut script_path = python_script.clone();
    
    if !script_path.exists() {
         // Try project root relative paths
         let fallbacks = [
             PathBuf::from("src-tauri").join("resources").join("youtube_transcript.py"),
             PathBuf::from("resources").join("youtube_transcript.py"),
         ];
         
         let mut found = false;
         for fallback in fallbacks {
             if fallback.exists() {
                 script_path = fallback;
                 found = true;
                 break;
             }
         }
         
         if !found {
             return Err(format!("YouTube script not found. Tried: {:?} and fallbacks.", python_script));
         }
    }

    let mut cmd = Command::new("py");
    cmd.arg("-3").arg(script_path).arg("--url").arg(url);
    
    if include_timestamps {
        cmd.arg("--timestamps");
    }

    let output = cmd.output().map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}
