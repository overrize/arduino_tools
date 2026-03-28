fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            arduino_desktop::commands::get_llm_config,
            arduino_desktop::commands::save_llm_config,
            arduino_desktop::commands::validate_llm_config,
            arduino_desktop::commands::detect_board,
            arduino_desktop::commands::list_projects,
            arduino_desktop::commands::get_project,
            arduino_desktop::commands::delete_project,
            arduino_desktop::commands::run_end_to_end,
            arduino_desktop::commands::build_project,
            arduino_desktop::commands::flash_project,
            arduino_desktop::commands::check_environment,
            arduino_desktop::commands::capture_serial_output,
            arduino_desktop::commands::debug_and_fix,
            arduino_desktop::commands::get_wokwi_config,
            arduino_desktop::commands::save_wokwi_config,
            arduino_desktop::commands::install_wokwi_cli,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
