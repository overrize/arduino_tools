# Simulation Files API - Quick Reference

## Command

```rust
// Backend: Arduino Desktop Tauri Command
#[tauri::command]
pub fn get_simulation_files(project_id: String) -> Result<SimulationFiles, String>
```

## TypeScript Interface

```typescript
interface SimulationFiles {
  project_id: string;
  project_dir: string;
  files: SimulationFile[];
}

interface SimulationFile {
  file_type: string;  // "diagram", "wokwi_config", "sketch", "screenshot"
  path: string;
  exists: boolean;
}
```

## Quick Usage

### Get all files
```typescript
const files = await invoke<SimulationFiles>('get_simulation_files', { projectId });
```

### Using utility functions
```typescript
import { getSimulationFiles } from './utils/simulationFiles';

const files = await getSimulationFiles('project-id');
```

## Available Utilities

| Function | Purpose |
|----------|---------|
| `getSimulationFiles()` | Get all files for a project |
| `getSimulationFileByType()` | Get specific file by type |
| `simulationFileExists()` | Check if a file exists |
| `getProjectDir()` | Get project directory path |
| `getSimulationFilePaths()` | Get all paths as object |
| `getExistingSimulationFiles()` | Get only existing files |
| `getFileTypeName()` | Get friendly name for file type |

## File Types

| Type | File | Created When |
|------|------|--------------|
| `diagram` | diagram.json | During simulation/build |
| `wokwi_config` | wokwi.toml | During first simulation |
| `sketch` | sketch.ino | During code generation |
| `screenshot` | simulation_screenshot.png | After simulation runs |

## Common Patterns

### Check if simulation has run
```typescript
const ran = await simulationFileExists(projectId, 'screenshot');
```

### Get diagram file
```typescript
const diagram = await getSimulationFileByType(projectId, 'diagram');
if (diagram?.exists) {
  // Use diagram.path
}
```

### Get all file paths
```typescript
const paths = await getSimulationFilePaths(projectId);
const diagramPath = paths?.diagram;
const sketchPath = paths?.sketch;
```

### Only existing files
```typescript
const existing = await getExistingSimulationFiles(projectId);
existing.forEach(file => {
  console.log(`${file.file_type}: ${file.path}`);
});
```

## Error Handling

```typescript
try {
  const files = await getSimulationFiles(projectId);
} catch (error) {
  console.error('Failed to get files:', error);
  // error is a string describing the issue
}
```

## Integration Points

### In App.tsx
```typescript
const getSimulationFiles = async (projectId: string) => {
  try {
    const result = await invoke<SimulationFiles>('get_simulation_files', { projectId });
    return result;
  } catch (error: any) {
    console.error('Failed to get simulation files:', error);
    return null;
  }
};
```

### In Custom Components
```typescript
import { getSimulationFiles, getFileTypeName } from '../utils/simulationFiles';

// In component
const files = await getSimulationFiles(projectId);
files?.files.forEach(file => {
  console.log(`${getFileTypeName(file.file_type)}: ${file.path}`);
});
```

## Return Value Structure

```typescript
{
  project_id: "abc123",
  project_dir: "/Users/username/Documents/arduino-tools/projects/abc123",
  files: [
    {
      file_type: "diagram",
      path: "/Users/username/Documents/arduino-tools/projects/abc123/diagram.json",
      exists: true
    },
    {
      file_type: "wokwi_config",
      path: "/Users/username/Documents/arduino-tools/projects/abc123/wokwi.toml",
      exists: true
    },
    {
      file_type: "sketch",
      path: "/Users/username/Documents/arduino-tools/projects/abc123/sketch.ino",
      exists: true
    },
    {
      file_type: "screenshot",
      path: "/Users/username/Documents/arduino-tools/projects/abc123/simulation_screenshot.png",
      exists: false  // Only exists if simulation has run
    }
  ]
}
```

## Files Location

```
~/Documents/arduino-tools/projects/{project_id}/
  ├── diagram.json
  ├── wokwi.toml
  ├── sketch.ino
  └── simulation_screenshot.png
```

## Implementation Location

- **Backend**: `arduino-desktop/src-tauri/src/commands.rs` (lines 1230-1278)
- **Data Types**: `arduino-desktop/src-tauri/src/project.rs` (added SimulationFile, SimulationFiles)
- **Frontend Types**: `arduino-desktop/src/App.tsx` (added interface definitions)
- **Utilities**: `arduino-desktop/src/utils/simulationFiles.ts`

## Documentation Files

- **API Docs**: `SIMULATION_FILES_API.md` (complete specification)
- **Examples**: `SIMULATION_FILES_EXAMPLES.md` (10 usage examples)
- **Feature Overview**: `SIMULATION_FILES_FEATURE.md` (design and details)
- **This File**: `SIMULATION_FILES_QUICK_REFERENCE.md` (quick reference)

## Most Common Use Cases

1. **Verify simulation setup**
   ```typescript
   const files = await getExistingSimulationFiles(projectId);
   const isReady = files.length >= 3; // diagram, config, sketch
   ```

2. **Check if simulation has run**
   ```typescript
   const hasRun = await simulationFileExists(projectId, 'screenshot');
   ```

3. **Get file path for opening**
   ```typescript
   const sketch = await getSimulationFileByType(projectId, 'sketch');
   await open(sketch!.path); // Open in default editor
   ```

4. **Display files in UI**
   ```typescript
   const files = await getSimulationFiles(projectId);
   files.files.forEach(file => {
     // Render file type and path
   });
   ```

## Tips

- Always check the `exists` field before using a path
- Use the utility functions instead of calling `invoke()` directly
- All returned paths are absolute and platform-specific
- File existence is checked at call time, not cached
- Suitable for both real-time checks and periodic monitoring
