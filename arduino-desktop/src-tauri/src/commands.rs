use crate::llm::{generate_arduino_code, validate_config, fix_arduino_code, diagnose_with_serial, generate_diagram_json};
use base64::Engine as _;
use crate::project::{
    BuildResult, DeployResult, DetectedBoard, EndToEndRequest, LLMConfig, Project,
    ProjectFile, ProjectInfo, WokwiConfig, SimulationFiles, SimulationFile,
};
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use std::time::Duration;
use tauri::Window;
use uuid::Uuid;
use regex::Regex;
use std::io::{self, BufRead};
use std::thread;
use serialport;

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
pub fn get_wokwi_config() -> Result<WokwiConfig, String> {
    let config_path = get_config_dir().join("wokwi.json");

    if !config_path.exists() {
        return Ok(WokwiConfig {
            token: String::new(),
        });
    }

    let content = fs::read_to_string(&config_path).map_err(|e| e.to_string())?;
    let config: WokwiConfig = serde_json::from_str(&content).map_err(|e| e.to_string())?;
    Ok(config)
}

#[tauri::command]
pub fn save_wokwi_config(config: WokwiConfig) -> Result<(), String> {
    let config_dir = get_config_dir();
    fs::create_dir_all(&config_dir).map_err(|e| e.to_string())?;

    let config_path = config_dir.join("wokwi.json");
    let content = serde_json::to_string_pretty(&config).map_err(|e| e.to_string())?;
    fs::write(&config_path, content).map_err(|e| e.to_string())?;

    Ok(())
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

fn has_npm() -> bool {
    which::which("npm").is_ok()
}

/// 根据当前平台返回 wokwi-cli GitHub Release 资产文件名
fn wokwi_cli_asset_name() -> Result<(&'static str, &'static str), String> {
    let arch = std::env::consts::ARCH;
    match (std::env::consts::OS, arch) {
        ("windows", "x86_64") => Ok(("wokwi-cli-win-x64.exe", "wokwi-cli.exe")),
        ("linux", "x86_64") => Ok(("wokwi-cli-linuxstatic-x64", "wokwi-cli")),
        ("linux", "aarch64") => Ok(("wokwi-cli-linuxstatic-arm64", "wokwi-cli")),
        ("macos", "x86_64") => Ok(("wokwi-cli-macos-x64", "wokwi-cli")),
        ("macos", "aarch64") => Ok(("wokwi-cli-macos-arm64", "wokwi-cli")),
        _ => Err(format!("不支持的平台: {} {}", std::env::consts::OS, arch)),
    }
}

/// 获取安装目录
fn wokwi_install_dir() -> PathBuf {
    if cfg!(target_os = "windows") {
        if let Some(local) = std::env::var_os("LOCALAPPDATA") {
            PathBuf::from(local).join("Programs").join("wokwi-cli")
        } else {
            dirs::home_dir().unwrap_or_else(|| PathBuf::from(".")).join(".local").join("bin")
        }
    } else {
        dirs::home_dir().unwrap_or_else(|| PathBuf::from(".")).join(".local").join("bin")
    }
}

/// 将目录加入当前进程 PATH，Windows 下同时写入用户注册表
fn add_to_path(dir: &PathBuf) {
    let dir_str = dir.to_string_lossy().to_string();
    let sep = if cfg!(target_os = "windows") { ";" } else { ":" };
    if let Ok(path) = std::env::var("PATH") {
        if !path.contains(&dir_str) {
            std::env::set_var("PATH", format!("{}{}{}", dir_str, sep, path));
        }
    }
    #[cfg(target_os = "windows")]
    {
        // 写入用户级 PATH 注册表
        let _ = Command::new("powershell")
            .args(&["-Command", &format!(
                "$p = [Environment]::GetEnvironmentVariable('Path','User'); \
                 if ($p -notlike '*{}*') {{ \
                     [Environment]::SetEnvironmentVariable('Path', '{}' + ';' + $p, 'User') \
                 }}",
                dir_str, dir_str
            )])
            .output();
    }
}

/// 从 GitHub Releases 下载并安装 wokwi-cli
async fn download_wokwi_cli(window: &Window) -> Result<PathBuf, String> {
    let (asset, bin_name) = wokwi_cli_asset_name()?;
    let url = format!(
        "https://github.com/wokwi/wokwi-cli/releases/latest/download/{}",
        asset
    );

    let install_dir = wokwi_install_dir();
    fs::create_dir_all(&install_dir)
        .map_err(|e| format!("创建安装目录失败: {}", e))?;
    let target = install_dir.join(bin_name);

    emit_log(window, &format!("下载 {} ...", url));

    let client = reqwest::Client::builder()
        .redirect(reqwest::redirect::Policy::limited(10))
        .build()
        .map_err(|e| format!("创建 HTTP 客户端失败: {}", e))?;

    let resp = client.get(&url)
        .header("User-Agent", "arduino-tools-installer")
        .send()
        .await
        .map_err(|e| format!("下载失败: {}", e))?;

    if !resp.status().is_success() {
        return Err(format!("下载失败 (HTTP {}): {}", resp.status(), url));
    }

    let bytes = resp.bytes().await
        .map_err(|e| format!("读取下载内容失败: {}", e))?;

    emit_log(window, &format!("已下载 {:.1} MB，正在安装...", bytes.len() as f64 / 1_048_576.0));

    fs::write(&target, &bytes)
        .map_err(|e| format!("写入文件失败: {}", e))?;

    // Linux/macOS 设置可执行权限
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&target, fs::Permissions::from_mode(0o755))
            .map_err(|e| format!("设置执行权限失败: {}", e))?;
    }

    // 确保安装目录在 PATH 上
    add_to_path(&install_dir);

    Ok(target)
}

#[tauri::command]
pub async fn install_wokwi_cli(window: Window) -> Result<bool, String> {
    if has_wokwi_cli() {
        emit_log(&window, "wokwi-cli 已安装");
        return Ok(true);
    }

    emit_log(&window, "正在从 GitHub 下载 wokwi-cli...");
    emit_status(&window, "installing");

    match download_wokwi_cli(&window).await {
        Ok(path) => {
            emit_log(&window, &format!("wokwi-cli 安装成功 → {}", path.display()));
            Ok(true)
        }
        Err(e) => Err(format!(
            "自动安装失败: {}\n请从 https://github.com/wokwi/wokwi-cli/releases 手动下载", e
        ))
    }
}

async fn ensure_wokwi_cli(window: &Window) -> Result<bool, String> {
    if has_wokwi_cli() {
        return Ok(true);
    }

    emit_log(window, "wokwi-cli 未安装，正在自动下载...");
    emit_status(window, "installing");

    match download_wokwi_cli(window).await {
        Ok(path) => {
            emit_log(window, &format!("wokwi-cli 安装成功 → {}", path.display()));
            Ok(true)
        }
        Err(e) => Err(format!(
            "wokwi-cli 自动安装失败: {}\n请从 https://github.com/wokwi/wokwi-cli/releases 手动下载", e
        ))
    }
}

async fn run_simulation(
    window: &Window,
    project_dir: &PathBuf,
    fqbn: &str,
    code: &str,
    llm_config: &LLMConfig,
) -> Result<DeployResult, String> {
    emit_log(window, "未检测到板卡，切换到 Wokwi 仿真...");

    // 自动安装 wokwi-cli
    if let Err(e) = ensure_wokwi_cli(window).await {
        return Ok(DeployResult {
            method: "simulation".to_string(),
            success: false,
            port: None,
            message: format!("wokwi-cli 安装失败: {}", e),
            screenshot_base64: None,
            diagram_json: None,
        });
    }

    // 检查并提示配置 token
    let wokwi_config = get_wokwi_config()?;
    if wokwi_config.token.is_empty() {
        emit_log(window, "警告: 未配置 WOKWI_CLI_TOKEN，仿真可能无法运行");
        emit_log(window, "请在设置中配置 Wokwi Token (https://wokwi.com/dashboard/ci)");
    }

    let board_id = fqbn_to_wokwi_id(fqbn);

    // Create wokwi.toml config if missing
    let wokwi_toml = project_dir.join("wokwi.toml");
    if !wokwi_toml.exists() {
        let toml_content = format!(
            "[wokwi]\nversion = 1\n\n[[chip]]\nname = \"{}\"\n",
            board_id
        );
        let _ = fs::write(&wokwi_toml, toml_content);
    }

    // Generate smart diagram.json with LLM (fallback to minimal if LLM fails)
    let diagram_path = project_dir.join("diagram.json");
    emit_log(window, "正在分析代码生成电路图...");
    let diagram_content = match generate_diagram_json(code, board_id, llm_config).await {
        Ok(json_str) => {
            emit_log(window, "智能电路图生成成功");
            let _ = fs::write(&diagram_path, &json_str);
            Some(json_str)
        }
        Err(e) => {
            emit_log(window, &format!("电路图生成失败，使用默认配置: {}", e));
            let fallback = serde_json::json!({
                "version": 1,
                "author": "Arduino Desktop",
                "editor": "wokwi",
                "parts": [{"type": board_id, "id": "board", "top": 0, "left": 0, "attrs": {}}],
                "connections": []
            });
            let fallback_str = serde_json::to_string_pretty(&fallback).unwrap_or_default();
            let _ = fs::write(&diagram_path, &fallback_str);
            Some(fallback_str)
        }
    };

    // Run wokwi-cli with screenshot capture
    let screenshot_path = project_dir.join("simulation_screenshot.png");
    let mut cmd = Command::new("wokwi-cli");
    cmd.args(&[
        "--timeout", "10000",
        "--screenshot-file", screenshot_path.to_str().unwrap_or("simulation_screenshot.png"),
        "--screenshot-time", "3000",
    ])
    .current_dir(project_dir);

    if !wokwi_config.token.is_empty() {
        cmd.env("WOKWI_CLI_TOKEN", &wokwi_config.token);
    }

    emit_log(window, "启动 Wokwi 仿真（含截图捕获）...");
    let output = cmd.output()
        .map_err(|e| format!("运行 wokwi-cli 失败: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let combined = format!("{}\n{}", stdout, stderr).trim().to_string();

    emit_log(window, &format!("Simulation output:\n{}", combined));

    // Read screenshot and encode as base64
    let screenshot_b64 = if screenshot_path.exists() {
        match fs::read(&screenshot_path) {
            Ok(bytes) => {
                let encoded = base64::engine::general_purpose::STANDARD.encode(&bytes);
                emit_log(window, "仿真截图已捕获");
                Some(encoded)
            }
            Err(_) => None,
        }
    } else {
        None
    };

    // Emit events to frontend
    if let Some(ref b64) = screenshot_b64 {
        let _ = window.emit("simulation-screenshot", b64);
    }
    if let Some(ref diagram) = diagram_content {
        let _ = window.emit("simulation-diagram", diagram);
    }

    // wokwi-cli 超时退出码非 0，但对于持续运行的固件（LED 闪烁、按键控制等）
    // 超时是正常行为 —— 只要仿真成功启动过就视为成功
    let success = output.status.success()
        || (combined.contains("Timeout") && combined.contains("Starting simulation"));

    Ok(DeployResult {
        method: "simulation".to_string(),
        success,
        port: None,
        message: if success {
            format!("仿真完成\n{}", combined)
        } else {
            format!("仿真失败: {}", combined)
        },
        screenshot_base64: screenshot_b64,
        diagram_json: diagram_content,
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

    let project_id = Uuid::new_v4().to_string();
    let project_name = request.name.unwrap_or_else(|| {
        format!("project_{}", &project_id[..8])
    });

    let project_dir = projects_dir.join(&project_id);
    fs::create_dir_all(&project_dir).map_err(|e| e.to_string())?;

    // Arduino-cli requires sketch filename to match directory name
    let ino_filename = format!("{}.ino", project_id);
    let ino_path = project_dir.join(&ino_filename);
    fs::write(&ino_path, &code).map_err(|e| e.to_string())?;

    emit_log(&window, &format!("Created: {}", project_name));

    // Step 3: Build with auto-fix
    let build_result = build_with_auto_fix(
        &window, &project_dir, &project_id, &request.prompt, &fqbn, &config
    ).await?;
    
    if !build_result.success {
        save_project_file(&project_dir, &project_id, &project_name, &fqbn, &request.prompt)?;
        return Err(format!("Build failed after auto-fix attempts:\n{}", 
            build_result.error.unwrap_or_default()));
    }

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
        // No board — run simulation with visualization
        emit_status(&window, "simulating");
        let sim_result = run_simulation(&window, &project_dir, &fqbn, &code, &config).await?;
        emit_log(&window, &sim_result.message);
        // 将仿真串口输出通过事件发送给前端，以便在聊天中展示
        let _ = window.emit("simulation-output", &sim_result.message);
    }

    // [新增] 获取编译产物的 hex 文件路径
    let hex_path = {
        let build_dir = project_dir.join("build");
        let hex_file = build_dir.join(format!("{}.ino.hex", project_id));

        if hex_file.exists() {
            let path_str = hex_file.to_string_lossy().to_string();
            // 确保路径使用正斜杠（跨平台兼容）
            Some(path_str.replace("\\", "/"))
        } else {
            None
        }
    };

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
        hex_path,  // [新增]
        diagram_json: None,  // [新增，预留给 Phase 3]
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
        .args(&["compile", "--fqbn", &fqbn, "--output-dir", "build", "."])
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
                    screenshot_base64: None,
                    diagram_json: None,
                })
            } else {
                Ok(DeployResult {
                    method: "flash".to_string(),
                    success: false,
                    port: None,
                    message: format!("Flash failed: {}", combined),
                    screenshot_base64: None,
                    diagram_json: None,
                })
            }
        }
        None => {
            emit_log(&window, "No board detected, switching to simulation...");
            // For flash_project, we don't have code/config to pass, use minimal simulation
            let code = "// Simulation fallback";
            let config = get_llm_config()?;
            run_simulation(&window, &proj_path, &fqbn, code, &config).await
        }
    }
}

#[tauri::command]
pub fn check_environment() -> Result<serde_json::Value, String> {
    let mut result = serde_json::Map::new();

    let arduino_cli = which::which("arduino-cli").is_ok();
    result.insert("arduino_cli".to_string(), serde_json::json!(arduino_cli));

    let npm = has_npm();
    result.insert("npm".to_string(), serde_json::json!(npm));

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

    let wokwi_config = get_wokwi_config()?;
    result.insert(
        "wokwi_token_configured".to_string(),
        serde_json::json!(!wokwi_config.token.is_empty()),
    );

    Ok(serde_json::Value::Object(result))
}

fn emit_status(window: &Window, status: &str) {
    let _ = window.emit("e2e-status", status);
}

fn emit_log(window: &Window, log: &str) {
    let _ = window.emit("e2e-log", log);
}

// ------------------------------------------------------------------
// 库管理 - 缺失库检测与自动安装
// ------------------------------------------------------------------

use lazy_static::lazy_static;

lazy_static! {
    static ref HEADER_REGEX: Regex = Regex::new(r":\s*fatal error:\s*(\S+\.h):\s*No such file or directory").unwrap();
}

fn header_to_library(header: &str) -> Option<String> {
    let mapping = [
        ("U8g2lib.h", "U8g2"),
        ("U8x8lib.h", "U8g2"),
        ("RTClib.h", "RTClib"),
        ("Adafruit_GFX.h", "Adafruit GFX Library"),
        ("Adafruit_SSD1306.h", "Adafruit SSD1306"),
        ("Adafruit_NeoPixel.h", "Adafruit NeoPixel"),
        ("DHT.h", "DHT sensor library"),
        ("OneWire.h", "OneWire"),
        ("DallasTemperature.h", "DallasTemperature"),
        ("LiquidCrystal_I2C.h", "LiquidCrystal I2C"),
        ("IRremote.h", "IRremote"),
        ("Stepper.h", "Stepper"),
        ("AccelStepper.h", "AccelStepper"),
        ("FastLED.h", "FastLED"),
        ("SD.h", "SD"),
        ("WiFi.h", "WiFi"),
        ("PubSubClient.h", "PubSubClient"),
        ("ArduinoJson.h", "ArduinoJson"),
    ];
    
    for (h, lib) in &mapping {
        if h == &header {
            return Some(lib.to_string());
        }
    }
    
    let builtin = ["Arduino.h", "Wire.h", "SPI.h", "Serial.h", "Servo.h", "EEPROM.h"];
    if builtin.contains(&header) {
        return None;
    }
    
    Some(header.replace(".h", ""))
}

fn detect_missing_libraries(build_output: &str) -> Vec<String> {
    let mut missing = Vec::new();
    for cap in HEADER_REGEX.captures_iter(build_output) {
        if let Some(header) = cap.get(1) {
            if let Some(lib) = header_to_library(header.as_str()) {
                if !missing.contains(&lib) {
                    missing.push(lib);
                }
            }
        }
    }
    missing
}

fn install_libraries(window: &Window, lib_names: &[String]) -> Vec<(String, bool, String)> {
    let mut results = Vec::new();
    
    for lib_name in lib_names {
        emit_log(window, &format!("[库] 安装 {} ...", lib_name));
        
        let output = Command::new("arduino-cli")
            .args(&["lib", "install", lib_name])
            .output();
        
        match output {
            Ok(result) => {
                let stdout = String::from_utf8_lossy(&result.stdout).to_string();
                let stderr = String::from_utf8_lossy(&result.stderr).to_string();
                let msg = format!("{} {}", stdout, stderr).trim().to_string();
                
                if result.status.success() {
                    emit_log(window, &format!("[库] {} 安装成功", lib_name));
                    results.push((lib_name.clone(), true, msg));
                } else {
                    let truncated = if msg.len() > 200 { &msg[..200] } else { &msg };
                    emit_log(window, &format!("[库] {} 安装失败: {}", lib_name, truncated));
                    results.push((lib_name.clone(), false, msg));
                }
            }
            Err(e) => {
                emit_log(window, &format!("[库] {} 安装异常: {}", lib_name, e));
                results.push((lib_name.clone(), false, e.to_string()));
            }
        }
    }
    
    results
}

fn extract_error_lines(build_output: &str, max_chars: usize) -> String {
    let error_lines: Vec<&str> = build_output
        .lines()
        .filter(|line| {
            let lower = line.to_lowercase();
            lower.contains("error:") || lower.contains("fatal error:") || lower.contains("undefined reference")
        })
        .collect();
    
    let result = if !error_lines.is_empty() {
        error_lines.join("\n")
    } else {
        build_output.to_string()
    };
    
    if result.len() > max_chars {
        result[..max_chars].to_string()
    } else {
        result
    }
}

// ------------------------------------------------------------------
// 串口监控
// ------------------------------------------------------------------

#[derive(Debug, Clone, serde::Serialize)]
pub struct SerialCaptureResult {
    pub success: bool,
    pub data: String,
    pub error: Option<String>,
}

#[tauri::command]
pub fn capture_serial_output(port: String, baud_rate: u32, duration_secs: u64) -> SerialCaptureResult {
    let result = std::thread::spawn(move || {
        match serialport::new(&port, baud_rate)
            .timeout(Duration::from_millis(100))
            .open() {
            Ok(mut port) => {
                thread::sleep(Duration::from_millis(500));
                
                let mut buffer: Vec<u8> = vec![0; 1024];
                let mut output = String::new();
                let start = std::time::Instant::now();
                let duration = Duration::from_secs(duration_secs);
                
                while start.elapsed() < duration {
                    match port.read(&mut buffer) {
                        Ok(n) => {
                            output.push_str(&String::from_utf8_lossy(&buffer[..n]));
                        }
                        Err(ref e) if e.kind() == io::ErrorKind::TimedOut => {
                            thread::sleep(Duration::from_millis(10));
                        }
                        Err(_) => break,
                    }
                }
                
                SerialCaptureResult {
                    success: true,
                    data: output,
                    error: None,
                }
            }
            Err(e) => SerialCaptureResult {
                success: false,
                data: String::new(),
                error: Some(format!("Failed to open port {}: {}", port, e)),
            },
        }
    }).join();
    
    match result {
        Ok(res) => res,
        Err(_) => SerialCaptureResult {
            success: false,
            data: String::new(),
            error: Some("Thread panicked".to_string()),
        },
    }
}

// ------------------------------------------------------------------
// 编译自动修复
// ------------------------------------------------------------------

async fn build_with_auto_fix(
    window: &Window,
    project_dir: &PathBuf,
    project_id: &str,
    prompt: &str,
    fqbn: &str,
    config: &LLMConfig,
) -> Result<BuildResult, String> {
    let max_fix_rounds = 3;
    // Arduino-cli requires sketch filename to match directory name
    let ino_path = project_dir.join(format!("{}.ino", project_id));
    let mut lib_install_attempted = false;
    let mut fix_round = 0;

    let fix_prompt = format!("{}\n【目标平台 FQBN: {}，请确保代码兼容该平台 API。】", prompt, fqbn);

    // Emit building status before starting compilation
    emit_status(window, "building");

    loop {
        let label = if fix_round > 0 || lib_install_attempted {
            "重新编译"
        } else {
            "编译"
        };
        emit_log(window, &format!("正在{}（{}）...", label, fqbn));
        
        let output = Command::new("arduino-cli")
            .args(&["compile", "--fqbn", fqbn, "--output-dir", "build", "."])
            .current_dir(&project_dir)
            .output()
            .map_err(|e| format!("Failed to execute arduino-cli: {}", e))?;
        
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        let full_output = format!("{}\n{}", stdout, stderr);
        emit_log(window, &full_output);
        
        if output.status.success() {
            emit_log(window, &format!("编译成功: {}/build", project_dir.display()));
            return Ok(BuildResult {
                success: true,
                output: full_output,
                error: None,
            });
        }
        
        let error_summary = extract_error_lines(&full_output, 1500);
        emit_log(window, &format!("编译失败:\n{}", error_summary));
        
        if !lib_install_attempted {
            let missing = detect_missing_libraries(&full_output);
            if !missing.is_empty() {
                emit_log(window, &format!("[自动] 检测到缺失库: {}", missing.join(", ")));
                install_libraries(window, &missing);
                lib_install_attempted = true;
                continue;
            }
        }
        
        lib_install_attempted = true;
        
        if fix_round >= max_fix_rounds {
            emit_log(window, &format!("已达最大修复轮数 ({})", max_fix_rounds));
            return Ok(BuildResult {
                success: false,
                output: full_output,
                error: Some(error_summary),
            });
        }
        
        emit_log(window, &format!("[修复] 第 {} 轮尝试自动修复...", fix_round + 1));
        
        let current_code = fs::read_to_string(&ino_path)
            .map_err(|e| format!("Failed to read sketch file: {}", e))?;
        
        match fix_arduino_code(&fix_prompt, &current_code, &error_summary, fqbn, config).await {
            Ok(fixed_code) => {
                fs::write(&ino_path, &fixed_code)
                    .map_err(|e| format!("Failed to write fixed code: {}", e))?;
                fix_round += 1;
                emit_log(window, &format!("[修复] 第 {} 轮代码已更新", fix_round));
            }
            Err(e) => {
                emit_log(window, &format!("修复失败: {}", e));
                return Ok(BuildResult {
                    success: false,
                    output: full_output,
                    error: Some(format!("修复失败: {}", e)),
                });
            }
        }
    }
}

// ------------------------------------------------------------------
// 调试诊断
// ------------------------------------------------------------------

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct DebugRequest {
    pub project_id: String,
    pub issue_description: String,
    pub serial_output: String,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct DebugResult {
    pub success: bool,
    pub diagnosis: String,
    pub changes: String,
    pub build_success: bool,
    pub upload_success: bool,
    pub message: String,
}

#[tauri::command]
pub async fn debug_and_fix(
    window: Window,
    request: DebugRequest,
) -> Result<DebugResult, String> {
    let config = get_llm_config()?;
    let projects_dir = get_projects_dir();
    let project_dir = projects_dir.join(&request.project_id);
    
    let project_file = project_dir.join("project.json");
    if !project_file.exists() {
        return Err("Project not found".to_string());
    }
    
    let project_info: ProjectInfo = serde_json::from_str(
        &fs::read_to_string(&project_file).map_err(|e| e.to_string())?
    ).map_err(|e| e.to_string())?;
    
    // Arduino-cli requires sketch filename to match directory name (project_id)
    let ino_filename = format!("{}.ino", request.project_id);
    let ino_path = project_dir.join(&ino_filename);
    
    if !ino_path.exists() {
        return Err("Sketch file not found".to_string());
    }
    
    let current_code = fs::read_to_string(&ino_path).map_err(|e| e.to_string())?;
    
    emit_status(&window, "diagnosing");
    emit_log(&window, "[诊断] 正在分析问题...");
    
    let hardware_info = format!("FQBN: {}", project_info.board);
    
    match diagnose_with_serial(&current_code, &request.serial_output, &request.issue_description, &hardware_info, &config).await {
        Ok(diagnosis) => {
            emit_log(&window, &format!("[诊断] {}", diagnosis.diagnosis));
            if !diagnosis.changes.is_empty() {
                emit_log(&window, &format!("[修改] {}", diagnosis.changes));
            }
            
            if diagnosis.code.is_empty() {
                return Ok(DebugResult {
                    success: false,
                    diagnosis: diagnosis.diagnosis,
                    changes: diagnosis.changes,
                    build_success: false,
                    upload_success: false,
                    message: "LLM 未返回修复代码".to_string(),
                });
            }
            
            fs::write(&ino_path, &diagnosis.code).map_err(|e| e.to_string())?;
            emit_log(&window, "[修复] 代码已更新，重新编译...");
            
            let build_result = build_with_auto_fix(
                &window,
                &project_dir,
                &request.project_id,
                &project_info.description,
                &project_info.board,
                &config,
            ).await?;
            
            if !build_result.success {
                return Ok(DebugResult {
                    success: false,
                    diagnosis: diagnosis.diagnosis,
                    changes: diagnosis.changes,
                    build_success: false,
                    upload_success: false,
                    message: "编译失败".to_string(),
                });
            }
            
            let detected = detect_board_internal()?;
            if let Some(board) = detected {
                emit_log(&window, &format!("[修复] 上传中: {} @ {}", board.name, board.port));
                
                let upload_output = Command::new("arduino-cli")
                    .args(&[
                        "upload", "--fqbn", &board.fqbn, "--port", &board.port, "--input-dir", "build",
                    ])
                    .current_dir(&project_dir)
                    .output();
                
                match upload_output {
                    Ok(result) => {
                        if result.status.success() {
                            emit_log(&window, "[修复] 上传成功！");
                            Ok(DebugResult {
                                success: true,
                                diagnosis: diagnosis.diagnosis,
                                changes: diagnosis.changes,
                                build_success: true,
                                upload_success: true,
                                message: "修复、编译、上传全部成功".to_string(),
                            })
                        } else {
                            let err = String::from_utf8_lossy(&result.stderr);
                            emit_log(&window, &format!("[修复] 上传失败: {}", err));
                            Ok(DebugResult {
                                success: false,
                                diagnosis: diagnosis.diagnosis,
                                changes: diagnosis.changes,
                                build_success: true,
                                upload_success: false,
                                message: format!("上传失败: {}", err),
                            })
                        }
                    }
                    Err(e) => Ok(DebugResult {
                        success: false,
                        diagnosis: diagnosis.diagnosis,
                        changes: diagnosis.changes,
                        build_success: true,
                        upload_success: false,
                        message: format!("上传异常: {}", e),
                    }),
                }
            } else {
                Ok(DebugResult {
                    success: true,
                    diagnosis: diagnosis.diagnosis,
                    changes: diagnosis.changes,
                    build_success: true,
                    upload_success: false,
                    message: "编译成功，但未检测到板卡进行上传".to_string(),
                })
            }
        }
        Err(e) => Err(format!("诊断失败: {}", e)),
    }
}

#[tauri::command]
pub fn get_simulation_files(project_id: String) -> Result<SimulationFiles, String> {
    let projects_dir = get_projects_dir();
    let project_dir = projects_dir.join(&project_id);

    if !project_dir.exists() {
        return Err(format!("项目目录不存在: {}", project_dir.display()));
    }

    let mut files = Vec::new();

    // diagram.json
    let diagram_path = project_dir.join("diagram.json");
    files.push(SimulationFile {
        file_type: "diagram".to_string(),
        path: diagram_path.to_string_lossy().to_string(),
        exists: diagram_path.exists(),
    });

    // wokwi.toml
    let wokwi_toml_path = project_dir.join("wokwi.toml");
    files.push(SimulationFile {
        file_type: "wokwi_config".to_string(),
        path: wokwi_toml_path.to_string_lossy().to_string(),
        exists: wokwi_toml_path.exists(),
    });

    // sketch.ino (main code file)
    let sketch_path = project_dir.join("sketch.ino");
    files.push(SimulationFile {
        file_type: "sketch".to_string(),
        path: sketch_path.to_string_lossy().to_string(),
        exists: sketch_path.exists(),
    });

    // simulation_screenshot.png
    let screenshot_path = project_dir.join("simulation_screenshot.png");
    files.push(SimulationFile {
        file_type: "screenshot".to_string(),
        path: screenshot_path.to_string_lossy().to_string(),
        exists: screenshot_path.exists(),
    });

    Ok(SimulationFiles {
        project_id,
        project_dir: project_dir.to_string_lossy().to_string(),
        files,
    })
}
