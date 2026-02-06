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

    let mut script_path = python_script;
    if !script_path.exists() {
         let mut dev_path = PathBuf::from("src-tauri");
         dev_path.push("resources");
         dev_path.push("youtube_transcript.py");
         if dev_path.exists() {
             script_path = dev_path;
         } else {
             return Err(format!("YouTube script not found at {:?}", script_path));
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
