// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod patterns;
mod ai_client;
mod youtube;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            patterns::list_patterns,
            patterns::get_pattern_content,
            ai_client::run_pattern,
            youtube::get_youtube_transcript
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
