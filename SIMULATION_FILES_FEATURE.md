# Simulation Files API Feature

## Summary

A new Tauri command `get_simulation_files` has been implemented to provide a convenient way to retrieve paths to all simulation-related files for a given Arduino project.

## What Was Added

### Backend (Rust)

**File:** `arduino-desktop/src-tauri/src/commands.rs`

1. **New Tauri Command:** `get_simulation_files`
   - Accepts: `project_id: String`
   - Returns: `Result<SimulationFiles, String>`
   - Functionality:
     - Validates project directory exists
     - Checks existence of all simulation files
     - Returns full file paths and existence status

2. **Data Structures:** `arduino-desktop/src-tauri/src/project.rs`
   - `SimulationFile` - Information about a single simulation file
   - `SimulationFiles` - Container with all simulation files for a project

### Frontend (TypeScript/React)

1. **Type Definitions:** `arduino-desktop/src/App.tsx`
   - Added `SimulationFile` interface
   - Added `SimulationFiles` interface
   - Added example `getSimulationFiles()` function

2. **Utility Module:** `arduino-desktop/src/utils/simulationFiles.ts`
   - Complete utility library with helper functions:
     - `getSimulationFiles()` - Main function
     - `getSimulationFileByType()` - Get specific file
     - `simulationFileExists()` - Check if file exists
     - `getProjectDir()` - Get project directory
     - `getSimulationFilePaths()` - Get all paths as object
     - `getExistingSimulationFiles()` - Get only existing files
     - `getFileTypeName()` - Get friendly name for file type

## Files Modified

1. `arduino-desktop/src-tauri/src/project.rs` - Added 2 new structs
2. `arduino-desktop/src-tauri/src/commands.rs` - Added imports and new command
3. `arduino-desktop/src/App.tsx` - Added type definitions and example usage

## Files Created

1. `SIMULATION_FILES_API.md` - Complete API documentation
2. `SIMULATION_FILES_EXAMPLES.md` - 10 practical usage examples
3. `arduino-desktop/src/utils/simulationFiles.ts` - Utility library
4. `SIMULATION_FILES_FEATURE.md` - This file

## Supported File Types

The API tracks these simulation-related files:

| Type | File | Purpose |
|------|------|---------|
| `diagram` | `diagram.json` | Wokwi circuit diagram configuration |
| `wokwi_config` | `wokwi.toml` | Wokwi simulator runtime configuration |
| `sketch` | `sketch.ino` | Arduino source code |
| `screenshot` | `simulation_screenshot.png` | Screenshot from last simulation run |

## Quick Start

### Basic Usage

```typescript
import { getSimulationFiles } from './utils/simulationFiles';

const files = await getSimulationFiles('project-id');
console.log(files.project_dir);
files.files.forEach(f => {
  console.log(`${f.file_type}: ${f.path} (exists: ${f.exists})`);
});
```

### Check if Simulation Has Run

```typescript
import { simulationFileExists } from './utils/simulationFiles';

const hasRun = await simulationFileExists('project-id', 'screenshot');
if (hasRun) {
  console.log('Simulation has been executed');
}
```

### Get File Paths as Object

```typescript
import { getSimulationFilePaths } from './utils/simulationFiles';

const paths = await getSimulationFilePaths('project-id');
// {
//   diagram: '/path/to/diagram.json',
//   wokwi_config: '/path/to/wokwi.toml',
//   sketch: '/path/to/sketch.ino',
//   screenshot: '/path/to/simulation_screenshot.png'
// }
```

## Use Cases

1. **File Management** - Locate and manage project files
2. **Verification** - Confirm simulation setup is complete
3. **Editor Integration** - Open files in external applications
4. **Backup/Export** - Copy simulation assets
5. **Progress Tracking** - Detect when simulations complete
6. **Debugging** - Access generated files for inspection
7. **CI/CD Integration** - Verify build artifacts

## Error Handling

```typescript
try {
  const files = await getSimulationFiles('project-id');
} catch (error) {
  // Handle errors like missing project directory
  console.error('Failed:', error);
}
```

## File Locations

All project files are stored at:

```
~/Documents/arduino-tools/projects/{project_id}/
```

Full paths are returned by the API for all operating systems (Windows, macOS, Linux).

## Design Decisions

1. **Return all file information** - The API checks existence for all standard files, even if they don't exist yet
2. **Use absolute paths** - Full system paths are returned for reliability in file operations
3. **Single command** - All files are fetched in one command to minimize IPC overhead
4. **No caching** - Existence is checked at call time to stay current with file system state
5. **Separate utility module** - Helpers in `utils/simulationFiles.ts` for better code organization

## Integration Notes

- The command is automatically registered with Tauri's command registry
- No additional configuration needed
- Works on all platforms (Windows, macOS, Linux)
- Handles path separators correctly for each OS
- Error messages are in Chinese to match app language

## Testing Recommendations

1. Test with projects that have completed simulations
2. Test with projects missing some files
3. Test with non-existent project IDs
4. Test on different operating systems for path handling
5. Test concurrent calls with multiple projects

## Future Enhancements

Potential future additions:

1. File metadata (size, modification time)
2. File content retrieval
3. File deletion
4. File watching/monitoring
5. Directory structure enumeration
6. Compression/archiving utilities

## Implementation Details

### Backend Implementation

The command iterates through expected file names and checks existence:

```rust
let files = vec![
    ("diagram", "diagram.json"),
    ("wokwi_config", "wokwi.toml"),
    ("sketch", "sketch.ino"),
    ("screenshot", "simulation_screenshot.png"),
];

for (type_name, filename) in files {
    let path = project_dir.join(filename);
    files.push(SimulationFile {
        file_type: type_name.to_string(),
        path: path.to_string_lossy().to_string(),
        exists: path.exists(),
    });
}
```

### Frontend Invocation

Uses Tauri's command invocation system:

```typescript
const result = await invoke<SimulationFiles>('get_simulation_files', {
    projectId
});
```

## Documentation

- Full API documentation: `SIMULATION_FILES_API.md`
- Usage examples (10 examples): `SIMULATION_FILES_EXAMPLES.md`
- Utility module source: `arduino-desktop/src/utils/simulationFiles.ts`
