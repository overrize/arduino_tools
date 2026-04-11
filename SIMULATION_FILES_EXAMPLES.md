# Simulation Files API - Usage Examples

## Example 1: Check if a simulation has been run

```typescript
import { simulationFileExists } from './utils/simulationFiles';

async function hasSimulationResults(projectId: string) {
  const hasScreenshot = await simulationFileExists(projectId, 'screenshot');
  return hasScreenshot;
}

// Usage
if (await hasSimulationResults('project-123')) {
  console.log('Simulation has been run');
} else {
  console.log('Simulation has not been run yet');
}
```

## Example 2: Get all file paths and display them

```typescript
import { getSimulationFilePaths, getFileTypeName } from './utils/simulationFiles';

async function displayProjectFiles(projectId: string) {
  const paths = await getSimulationFilePaths(projectId);

  if (!paths) {
    console.log('Project not found');
    return;
  }

  console.log('Project files:');
  Object.entries(paths).forEach(([type, path]) => {
    console.log(`  ${getFileTypeName(type)}: ${path}`);
  });
}
```

## Example 3: Display in React component

```typescript
import { useState, useEffect } from 'react';
import { getSimulationFiles, getFileTypeName } from '../utils/simulationFiles';

interface SimulationFilesDisplayProps {
  projectId: string;
}

export function SimulationFilesDisplay({ projectId }: SimulationFilesDisplayProps) {
  const [files, setFiles] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const result = await getSimulationFiles(projectId);
        setFiles(result);
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [projectId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!files) return <div>No files found</div>;

  return (
    <div>
      <h3>Project Directory</h3>
      <p>{files.project_dir}</p>

      <h3>Files</h3>
      <ul>
        {files.files.map((file: any) => (
          <li key={file.file_type}>
            <strong>{getFileTypeName(file.file_type)}</strong>
            <p>{file.path}</p>
            <p>Status: {file.exists ? '✓ 存在' : '✗ 不存在'}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

## Example 4: Get only existing files

```typescript
import { getExistingSimulationFiles } from './utils/simulationFiles';

async function listAvailableFiles(projectId: string) {
  const existing = await getExistingSimulationFiles(projectId);

  console.log(`Found ${existing.length} files:`);
  existing.forEach(file => {
    console.log(`  - ${file.file_type}: ${file.path}`);
  });

  return existing;
}
```

## Example 5: Open a file in external application

```typescript
import { getSimulationFileByType } from './utils/simulationFiles';
import { open } from '@tauri-apps/api/shell';

async function openProjectFile(projectId: string, fileType: string) {
  const file = await getSimulationFileByType(projectId, fileType);

  if (!file || !file.exists) {
    console.error(`File of type "${fileType}" not found`);
    return;
  }

  try {
    await open(file.path);
    console.log(`Opened: ${file.path}`);
  } catch (error) {
    console.error('Failed to open file:', error);
  }
}

// Usage
await openProjectFile('my-project', 'sketch'); // Opens sketch.ino in default editor
```

## Example 6: Copy simulation files for backup

```typescript
import { getExistingSimulationFiles } from './utils/simulationFiles';
import { readBinaryFile, writeBinaryFile } from '@tauri-apps/api/fs';

async function backupSimulationFiles(projectId: string, backupDir: string) {
  const files = await getExistingSimulationFiles(projectId);

  const results = [];
  for (const file of files) {
    try {
      const content = await readBinaryFile(file.path);
      const backupPath = `${backupDir}/${file.file_type}_${Date.now()}`;
      await writeBinaryFile(backupPath, content);
      results.push({ type: file.file_type, status: 'success', path: backupPath });
    } catch (error) {
      results.push({ type: file.file_type, status: 'failed', error: String(error) });
    }
  }

  return results;
}
```

## Example 7: Display simulation status in Terminal blocks

```typescript
import { getExistingSimulationFiles } from '../utils/simulationFiles';
import { CommandBlock, OutputBlock } from './Terminal';

async function generateSimulationStatusBlock(projectId: string) {
  const existing = await getExistingSimulationFiles(projectId);

  const content = existing
    .map(file => `✓ ${file.file_type}: ${file.path}`)
    .join('\n');

  const block: OutputBlock = {
    type: 'output',
    title: '仿真文件',
    content: content || '(无仿真文件)',
    variant: 'default',
    timestamp: Date.now(),
  };

  return block;
}
```

## Example 8: Real-time file monitoring

```typescript
import { getSimulationFiles } from './utils/simulationFiles';

let lastFileState: any = null;

async function checkForNewSimulationFiles(projectId: string) {
  const current = await getSimulationFiles(projectId);

  if (!current) return;

  if (!lastFileState) {
    lastFileState = current;
    return;
  }

  // Find newly created files
  const newFiles = current.files.filter(
    f => f.exists && !lastFileState.files.find((old: any) => old.file_type === f.file_type && old.exists)
  );

  if (newFiles.length > 0) {
    console.log('New simulation files detected:');
    newFiles.forEach(file => {
      console.log(`  - ${file.file_type}: ${file.path}`);
    });
  }

  lastFileState = current;
}

// Call this periodically in a component
setInterval(() => checkForNewSimulationFiles('project-123'), 2000);
```

## Example 9: Verify simulation setup

```typescript
import { getSimulationFiles } from './utils/simulationFiles';

async function verifySimulationSetup(projectId: string): Promise<{
  isValid: boolean;
  missing: string[];
  message: string;
}> {
  const files = await getSimulationFiles(projectId);

  if (!files) {
    return {
      isValid: false,
      missing: ['all'],
      message: '项目不存在'
    };
  }

  const required = ['diagram', 'wokwi_config', 'sketch'];
  const missing = required.filter(
    type => !files.files.find(f => f.file_type === type && f.exists)
  );

  if (missing.length > 0) {
    return {
      isValid: false,
      missing,
      message: `缺少文件: ${missing.join(', ')}`
    };
  }

  return {
    isValid: true,
    missing: [],
    message: '仿真配置完整'
  };
}
```

## Example 10: Get file size information

```typescript
import { getExistingSimulationFiles } from './utils/simulationFiles';
import { metadata } from '@tauri-apps/api/fs';

async function getSimulationFileSizes(projectId: string) {
  const files = await getExistingSimulationFiles(projectId);

  const sizes: Record<string, number> = {};

  for (const file of files) {
    try {
      const info = await metadata(file.path);
      sizes[file.file_type] = info.size || 0;
    } catch (error) {
      console.error(`Failed to get size for ${file.file_type}:`, error);
    }
  }

  return sizes;
}

// Usage
const sizes = await getSimulationFileSizes('project-123');
console.log(`Diagram size: ${sizes.diagram} bytes`);
console.log(`Screenshot size: ${sizes.screenshot} bytes`);
```

## Tips

1. **Always check `exists` field** - Files may be listed but not yet created
2. **Use the utility functions** - They handle error cases and provide convenience methods
3. **Cache results when possible** - File metadata doesn't change frequently during a session
4. **Handle errors gracefully** - Network or permission issues may occur
5. **Use absolute paths** - All returned paths are absolute for reliable file operations

## Related Files

- Backend implementation: `arduino-desktop/src-tauri/src/commands.rs` (`get_simulation_files`)
- API documentation: `SIMULATION_FILES_API.md`
- Utility functions: `arduino-desktop/src/utils/simulationFiles.ts`
