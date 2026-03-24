use crate::llm::{generate_arduino_code, validate_config};
use crate::project::{
    BuildResult, DeployResult, DetectedBoard, EndToEndRequest, LLMConfig, Project,
    ProjectFile, ProjectInfo,
};
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use tauri::Window;
use uuid::Uuid;

fn get_config_dir() -> PathBuf {
    dirs::config_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("arduino-desktop")
}

fn get_projects_dir() -> PathBuf {
    dirs::document_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("arduino-tools")
        .join("projects")
}

#[tauri::command]
pub fn get_llm_config() -> Result<LLMConfig, String> {
    let config_path = get_config_dir().join("config.json");

    if !config_path.exists() {
        return Ok(LLMConfig {
            api_key: String::new(),
            base_url: "https://api.moonshot.cn/v1".to_string(),
            model: "kimi-k2-0905-preview".to_string(),
        });
    }

    let content = fs::read_to_string(&config_path).map_err(|e| e.to_string())?;
    let config: LLMConfig = serde_json::from_str(&content).map_err(|e| e.to_string())?;
    Ok(config)
}

#[tauri::command]
pub fn save_llm_config(config: LLMConfig) -> Result<(), String> {
    let config_dir = get_config_dir();
    fs::create_dir_all(&config_dir).map_err(|e| e.to_string())?;

    let config_path = config_dir.join("config.json");
    let content = serde_json::to_string_pretty(&config).map_err(|e| e.to_string())?;
    fs::write(&config_path, content).map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub async fn validate_llm_config(config: LLMConfig) -> Result<bool, String> {
    validate_config(&config).await
}

#[tauri::command]
pub fn detect_board() -> Result<Option<DetectedBoard>, String> {
    detect_board_internal()
}

fn detect_board_internal() -> Result<Option<DetectedBoard>, String> {
    let output = Command::new("arduino-cli")
        .args(&["board", "list", "--format", "json"])
        .output();

    let output = match output {
        Ok(o) => o,
        Err(_) => return Ok(None),
    };

    if !output.status.success() {
        return Ok(None);
    }

    let json: serde_json::Value =
        serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())?;

    // arduino-cli board list returns detected_ports array
    let ports = json
        .as_array()
        .or_else(|| json.get("detected_ports").and_then(|v| v.as_array()));

    if let Some(ports) = ports {
        for port_entry in ports {
            // Try to find a port with matching boards
            let address = port_entry
                .get("port")
                .and_then(|p| p.get("address"))
                .and_then(|a| a.as_str())
                .or_else(|| port_entry.get("address").and_then(|a| a.as_str()));

            let boards = port_entry
                .get("matching_boards")
                .and_then(|b| b.as_array())
                .or_else(|| {
                    port_entry
                        .get("boards")
                        .and_then(|b| b.as_array())
                });

            if let (Some(address), Some(boards)) = (address, boards) {
                if let Some(board) = boards.first() {
                    let fqbn = board
                        .get("fqbn")
                        .and_then(|f| f.as_str())
                        .unwrap_or("")
                        .to_string();
                    let name = board
                        .get("name")
                        .and_then(|n| n.as_str())
                        .unwrap_or("Unknown Board")
                        .to_string();

                    if !fqbn.is_empty() {
                        return Ok(Some(DetectedBoard {
                            port: address.to_string(),
                            fqbn,
                            name,
                        }));
                    }
                }
            }
        }
    }

    Ok(None)
}

fn has_wokwi_cli() -> bool {
    which::which("wokwi-cli").is_ok()
}

fn run_simulation(window: &Window, project_dir: &PathBuf, fqbn: &str) -> Result<DeployResult, String> {
    emit_log(window, "No board detected, switching to Wokwi simulation...");

    if !has_wokwi_cli() {
        return Ok(DeployResult {
            method: "simulation".to_string(),
            success: false,
            port: None,
            message: "wokwi-cli not installed. Install it to enable simulation: npm i -g @anthropic/wokwi-cli".to_string(),
        });
    }

    // Create wokwi.toml config if missing
    let wokwi_toml = project_dir.join("wokwi.toml");
    if !wokwi_toml.exists() {
        let board_id = fqbn_to_wokwi_id(fqbn);
        let toml_content = format!(
            "[wokwi]\nversion = 1\n\n[[chip]]\nname = \"{}\"\n",
            board_id
        );
        let _ = fs::write(&wokwi_toml, toml_content);
    }

    // Create diagram.json if missing
    let diagram_json = project_dir.join("diagram.json");
    if !diagram_json.exists() {
        let board_id = fqbn_to_wokwi_id(fqbn);
        let diagram = serde_json::json!({
            "version": 1,
            "author": "Arduino Desktop",
            "editor": "wokwi",
            "parts": [{"type": board_id, "id": "board", "top": 0, "left": 0, "attrs": {}}],
            "connections": []
        });
        let _ = fs::write(&diagram_json, serde_json::to_string_pretty(&diagram).unwrap_or_default());
    }

    let output = Command::new("wokwi-cli")
        .args(&["--timeout", "10000"])
        .current_dir(project_dir)
        .output()
        .map_err(|e| format!("Failed to run wokwi-cli: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let combined = format!("{}\n{}", stdout, stderr).trim().to_string();

    emit_log(window, &format!("Simulation output:\n{}", combined));

    Ok(DeployResult {
        method: "simulation".to_string(),
        success: output.status.success(),
        port: None,
        message: if output.status.success() {
            "Simulation completed successfully".to_string()
        } else {
            format!("Simulation finished: {}", combined)
        },
    })
}

fn fqbn_to_wokwi_id(fqbn: &str) -> &str {
    match fqbn {
        "arduino:avr:uno" => "wokwi-arduino-uno",
        "arduino:avr:nano" => "wokwi-arduino-nano",
        "arduino:avr:mega" => "wokwi-arduino-mega",
        "arduino:mbed_rp2040:pico" => "wokwi-pi-pico",
        "esp32:esp32:esp32" => "wokwi-esp32-devkit-v1",
        _ => "wokwi-arduino-uno",
    }
}

#[tauri::command]
pub fn list_projects() -> Result<Vec<ProjectInfo>, String> {
    let projects_dir = get_projects_dir();

    if !projects_dir.exists() {
        return Ok(Vec::new());
    }

    let mut projects = Vec::new();

    for entry in fs::read_dir(&projects_dir).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();

        if path.is_dir() {
            let project_file = path.join("project.json");
            if project_file.exists() {
                let content = fs::read_to_string(&project_file).map_err(|e| e.to_string())?;
                let mut info: ProjectInfo =
                    serde_json::from_str(&content).map_err(|e| e.to_string())?;
                info.path = path;
                projects.push(info);
            }
        }
    }

    projects.sort_by(|a, b| b.created_at.cmp(&a.created_at));
    Ok(projects)
}

#[tauri::command]
pub fn get_project(project_id: String) -> Result<Project, String> {
    let project_dir = get_projects_dir().join(&project_id);
    let project_file = project_dir.join("project.json");

    if !project_file.exists() {
        return Err("Project not found".to_string());
    }

    let content = fs::read_to_string(&project_file).map_err(|e| e.to_string())?;
    let project: Project = serde_json::from_str(&content).map_err(|e| e.to_string())?;

    Ok(project)
}

#[tauri::command]
pub fn delete_project(project_id: String) -> Result<(), String> {
    let project_dir = get_projects_dir().join(&project_id);

    if project_dir.exists() {
        fs::remove_dir_all(&project_dir).map_err(|e| e.to_string())?;
    }

    Ok(())
}

#[tauri::command]
pub async fn run_end_to_end(
    window: Window,
    request: EndToEndRequest,
) -> Result<Project, String> {
    let config = get_llm_config()?;
    let projects_dir = get_projects_dir();
    fs::create_dir_all(&projects_dir).map_err(|e| e.to_string())?;

    // Step 1: Auto-detect board
    emit_status(&window, "detecting");
    emit_log(&window, "Detecting Arduino board...");

    let detected = detect_board_internal()?;
    let (fqbn, board_name, port) = match &detected {
        Some(board) => {
            emit_log(
                &window,
                &format!("Board detected: {} at {} ({})", board.name, board.port, board.fqbn),
            );
            (board.fqbn.clone(), board.name.clone(), Some(board.port.clone()))
        }
        None => {
            let fallback_fqbn = request.board.clone().unwrap_or_else(|| "arduino:avr:uno".to_string());
            emit_log(
                &window,
                &format!("No board detected. Using {} for code generation. Will simulate after build.", fallback_fqbn),
            );
            (fallback_fqbn, "No board (simulation)".to_string(), None)
        }
    };

    // Step 2: Generate code
    emit_status(&window, "generating");
    emit_log(&window, "Generating Arduino code...");

    let code = generate_arduino_code(&request.prompt, &fqbn, &config).await?;

    let project_name = request.name.unwrap_or_else(|| {
        format!("project_{}", Uuid::new_v4().to_string()[..8].to_string())
    });

    let project_id = Uuid::new_v4().to_string();
    let project_dir = projects_dir.join(&project_id);
    fs::create_dir_all(&project_dir).map_err(|e| e.to_string())?;

    let ino_filename = format!("{}.ino", project_name);
    let ino_path = project_dir.join(&ino_filename);
    fs::write(&ino_path, &code).map_err(|e| e.to_string())?;

    emit_log(&window, &format!("Created: {}", project_name));

    // Step 3: Build
    emit_status(&window, "building");
    emit_log(&window, &format!("Building with FQBN: {}", fqbn));

    let build_output = Command::new("arduino-cli")
        .args(&["compile", "--fqbn", &fqbn, "--output-dir", "build"])
        .current_dir(&project_dir)
        .output()
        .map_err(|e| format!("Failed to execute arduino-cli: {}", e))?;

    let stdout = String::from_utf8_lossy(&build_output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&build_output.stderr).to_string();
    emit_log(&window, &format!("{}\n{}", stdout, stderr));

    if !build_output.status.success() {
        // Save project even if build fails
        save_project_file(&project_dir, &project_id, &project_name, &fqbn, &request.prompt)?;
        return Err(format!("Build failed:\n{}\n{}", stdout, stderr));
    }

    emit_log(&window, "Build successful!");

    // Step 4: Deploy — flash if board detected, simulate if not
    emit_status(&window, "deploying");

    if let Some(port_addr) = port {
        // Flash to real board
        emit_log(&window, &format!("Flashing to {} at {}...", board_name, port_addr));

        let flash_output = Command::new("arduino-cli")
            .args(&[
                "upload", "--fqbn", &fqbn, "--port", &port_addr, "--input-dir", "build",
            ])
            .current_dir(&project_dir)
            .output()
            .map_err(|e| format!("Failed to flash: {}", e))?;

        let flash_stdout = String::from_utf8_lossy(&flash_output.stdout).to_string();
        let flash_stderr = String::from_utf8_lossy(&flash_output.stderr).to_string();
        emit_log(&window, &format!("{}\n{}", flash_stdout, flash_stderr));

        if flash_output.status.success() {
            emit_log(&window, &format!("Flashed to {} successfully!", board_name));
        } else {
            emit_log(&window, &format!("Flash failed, output:\n{}\n{}", flash_stdout, flash_stderr));
        }
    } else {
        // No board — run simulation
        let sim_result = run_simulation(&window, &project_dir, &fqbn)?;
        emit_log(&window, &sim_result.message);
    }

    // Save project
    let project = Project {
        id: project_id.clone(),
        name: project_name.clone(),
        board: fqbn.clone(),
        description: request.prompt.clone(),
        files: vec![ProjectFile {
            path: ino_filename,
            content: code,
        }],
        created_at: chrono::Local::now().to_rfc3339(),
    };

    save_project_file(&project_dir, &project_id, &project_name, &fqbn, &request.prompt)?;

    emit_status(&window, "completed");
    emit_log(&window, "Pipeline complete!");

    Ok(project)
}

fn save_project_file(
    project_dir: &PathBuf,
    project_id: &str,
    project_name: &str,
    board: &str,
    description: &str,
) -> Result<(), String> {
    let project_info = ProjectInfo {
        id: project_id.to_string(),
        name: project_name.to_string(),
        board: board.to_string(),
        description: description.to_string(),
        created_at: chrono::Local::now().to_rfc3339(),
        path: project_dir.clone(),
    };
    let content = serde_json::to_string_pretty(&project_info).map_err(|e| e.to_string())?;
    fs::write(project_dir.join("project.json"), content).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn build_project(
    window: Window,
    project_dir: String,
    fqbn: String,
) -> Result<BuildResult, String> {
    emit_status(&window, "building");
    emit_log(&window, &format!("Building with FQBN: {}", fqbn));

    let proj_path = get_projects_dir().join(&project_dir);

    let output = Command::new("arduino-cli")
        .args(&["compile", "--fqbn", &fqbn, "--output-dir", "build"])
        .current_dir(&proj_path)
        .output()
        .map_err(|e| format!("Failed to execute arduino-cli: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let combined = format!("{}\n{}", stdout, stderr);

    emit_log(&window, &combined);

    let result = if output.status.success() {
        emit_status(&window, "completed");
        BuildResult {
            success: true,
            output: combined,
            error: None,
        }
    } else {
        BuildResult {
            success: false,
            output: combined.clone(),
            error: Some(combined),
        }
    };

    Ok(result)
}

#[tauri::command]
pub async fn flash_project(
    window: Window,
    project_dir: String,
    fqbn: String,
) -> Result<DeployResult, String> {
    emit_status(&window, "deploying");
    emit_log(&window, "Auto-detecting board...");

    let detected = detect_board_internal()?;
    let proj_path = get_projects_dir().join(&project_dir);

    match detected {
        Some(board) => {
            emit_log(
                &window,
                &format!("Board detected: {} at {}", board.name, board.port),
            );

            let output = Command::new("arduino-cli")
                .args(&[
                    "upload", "--fqbn", &board.fqbn, "--port", &board.port, "--input-dir", "build",
                ])
                .current_dir(&proj_path)
                .output()
                .map_err(|e| format!("Failed to execute arduino-cli: {}", e))?;

            let stdout = String::from_utf8_lossy(&output.stdout).to_string();
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();
            let combined = format!("{}\n{}", stdout, stderr);

            emit_log(&window, &combined);

            if output.status.success() {
                emit_status(&window, "completed");
                Ok(DeployResult {
                    method: "flash".to_string(),
                    success: true,
                    port: Some(board.port),
                    message: format!("Flashed to {} successfully!", board.name),
                })
            } else {
                Ok(DeployResult {
                    method: "flash".to_string(),
                    success: false,
                    port: None,
                    message: format!("Flash failed: {}", combined),
                })
            }
        }
        None => {
            emit_log(&window, "No board detected, switching to simulation...");
            run_simulation(&window, &proj_path, &fqbn)
        }
    }
}

#[tauri::command]
pub fn check_environment() -> Result<serde_json::Value, String> {
    let mut result = serde_json::Map::new();

    let arduino_cli = which::which("arduino-cli").is_ok();
    result.insert("arduino_cli".to_string(), serde_json::json!(arduino_cli));

    let config = get_llm_config()?;
    result.insert(
        "llm_configured".to_string(),
        serde_json::json!(!config.api_key.is_empty()),
    );

    let board = detect_board_internal().unwrap_or(None);
    result.insert("board_detected".to_string(), serde_json::json!(board.is_some()));
    if let Some(b) = board {
        result.insert("board_name".to_string(), serde_json::json!(b.name));
        result.insert("board_port".to_string(), serde_json::json!(b.port));
        result.insert("board_fqbn".to_string(), serde_json::json!(b.fqbn));
    }

    let wokwi = has_wokwi_cli();
    result.insert("wokwi_cli".to_string(), serde_json::json!(wokwi));

    Ok(serde_json::Value::Object(result))
}

fn emit_status(window: &Window, status: &str) {
    let _ = window.emit("e2e-status", status);
}

fn emit_log(window: &Window, log: &str) {
    let _ = window.emit("e2e-log", log);
}
