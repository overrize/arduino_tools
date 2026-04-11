# Simulation Files API

## Overview

The `get_simulation_files` command provides a way to retrieve the paths of all simulation-related files for a given Arduino project.

## Command

**Name:** `get_simulation_files`

**Type:** Tauri Command (Frontend → Backend)

## Request

```typescript
invoke<SimulationFiles>('get_simulation_files', {
  projectId: string  // The ID of the project
})
```

## Response

### Success

Returns a `SimulationFiles` object:

```typescript
interface SimulationFiles {
  project_id: string;        // The project ID
  project_dir: string;       // Full path to the project directory
  files: SimulationFile[];   // Array of simulation files
}

interface SimulationFile {
  file_type: string;  // Type of file: "diagram", "wokwi_config", "sketch", "screenshot"
  path: string;       // Full path to the file
  exists: boolean;    // Whether the file currently exists
}
```

### Failure

Returns a `Result<SimulationFiles, String>` error with a descriptive message if:
- The project directory does not exist
- File system access fails

## File Types

| Type | File Name | Description |
|------|-----------|-------------|
| `diagram` | `diagram.json` | Wokwi circuit diagram configuration |
| `wokwi_config` | `wokwi.toml` | Wokwi simulator configuration |
| `sketch` | `sketch.ino` | Arduino source code |
| `screenshot` | `simulation_screenshot.png` | Screenshot from simulation |

## Usage Example

### TypeScript/React

```typescript
import { invoke } from '@tauri-apps/api/tauri';

interface SimulationFiles {
  project_id: string;
  project_dir: string;
  files: Array<{
    file_type: string;
    path: string;
    exists: boolean;
  }>;
}

async function fetchSimulationFiles(projectId: string) {
  try {
    const files = await invoke<SimulationFiles>('get_simulation_files', {
      projectId
    });

    console.log('Project Directory:', files.project_dir);
    files.files.forEach(file => {
      console.log(`${file.file_type}: ${file.path} (exists: ${file.exists})`);
    });

    return files;
  } catch (error) {
    console.error('Failed to fetch simulation files:', error);
  }
}

// Usage
const simFiles = await fetchSimulationFiles('my-project-id');
```

### Backend (Rust)

The command is implemented in `arduino-desktop/src-tauri/src/commands.rs`:

```rust
#[tauri::command]
pub fn get_simulation_files(project_id: String) -> Result<SimulationFiles, String> {
    // Implementation handles file existence checking and path construction
}
```

## File Locations

All files are stored in the project directory, which follows this pattern:

```
~/Documents/arduino-tools/projects/{project_id}/
  ├── diagram.json
  ├── wokwi.toml
  ├── sketch.ino
  └── simulation_screenshot.png
```

Where:
- `~` is the user's home directory (e.g., `/Users/username` on macOS, `C:\Users\username` on Windows)
- `{project_id}` is the unique identifier for the project (e.g., `abc123def456`)

## Integration Points

This API can be used to:

1. **Open files in external editors** - Get paths to open files in user's preferred IDE
2. **View simulation results** - Display the screenshot base64 or raw file
3. **Access project files** - Read or modify project configurations
4. **Verify file existence** - Check if simulation has been run (screenshot exists)
5. **Manage project assets** - Track which files have been generated

## Error Handling

```typescript
try {
  const files = await invoke<SimulationFiles>('get_simulation_files', { projectId });
} catch (error) {
  // error is a string describing what went wrong
  // Common messages:
  // - "项目目录不存在: ..." (Project directory does not exist)
  // - File system access errors
}
```

## Notes

- The `exists` field is checked at the time of the API call, not cached
- File paths use the system's native path separators (e.g., `\` on Windows, `/` on macOS/Linux)
- All paths are absolute paths from the system root
- The API does not return file contents; use standard file I/O for that
- Screenshot files are created during simulation and may not exist if simulation hasn't been run

## Related Commands

- `run_end_to_end` - Creates/updates these files during the full build and deploy process
- `debug_and_fix` - Updates files during the auto-fix process
- `install_wokwi_cli` - Installs Wokwi CLI needed for simulation
