import { invoke } from '@tauri-apps/api/tauri';

export interface SimulationFile {
  file_type: string;
  path: string;
  exists: boolean;
}

export interface SimulationFiles {
  project_id: string;
  project_dir: string;
  files: SimulationFile[];
}

/**
 * Fetch simulation-related files for a project
 * @param projectId - The ID of the project
 * @returns SimulationFiles object with paths and existence info
 */
export async function getSimulationFiles(projectId: string): Promise<SimulationFiles | null> {
  try {
    const result = await invoke<SimulationFiles>('get_simulation_files', { projectId });
    return result;
  } catch (error) {
    console.error('Failed to get simulation files:', error);
    return null;
  }
}

/**
 * Get a specific file by type
 * @param projectId - The ID of the project
 * @param fileType - The type of file ('diagram', 'wokwi_config', 'sketch', 'screenshot')
 * @returns The file object if found, null otherwise
 */
export async function getSimulationFileByType(
  projectId: string,
  fileType: string
): Promise<SimulationFile | null> {
  const files = await getSimulationFiles(projectId);
  if (!files) return null;

  const file = files.files.find(f => f.file_type === fileType);
  return file || null;
}

/**
 * Check if a simulation file exists
 * @param projectId - The ID of the project
 * @param fileType - The type of file to check
 * @returns True if the file exists, false otherwise
 */
export async function simulationFileExists(projectId: string, fileType: string): Promise<boolean> {
  const file = await getSimulationFileByType(projectId, fileType);
  return file?.exists ?? false;
}

/**
 * Get the project directory path
 * @param projectId - The ID of the project
 * @returns The project directory path, or null if not found
 */
export async function getProjectDir(projectId: string): Promise<string | null> {
  const files = await getSimulationFiles(projectId);
  return files?.project_dir ?? null;
}

/**
 * Get all file paths for a project
 * @param projectId - The ID of the project
 * @returns An object with file type as key and path as value
 */
export async function getSimulationFilePaths(projectId: string): Promise<Record<string, string> | null> {
  const files = await getSimulationFiles(projectId);
  if (!files) return null;

  return files.files.reduce((acc, file) => {
    acc[file.file_type] = file.path;
    return acc;
  }, {} as Record<string, string>);
}

/**
 * Get only the files that exist
 * @param projectId - The ID of the project
 * @returns Array of existing simulation files
 */
export async function getExistingSimulationFiles(projectId: string): Promise<SimulationFile[]> {
  const files = await getSimulationFiles(projectId);
  if (!files) return [];

  return files.files.filter(f => f.exists);
}

/**
 * Get a friendly name for a file type
 * @param fileType - The file type
 * @returns A user-friendly name
 */
export function getFileTypeName(fileType: string): string {
  const names: Record<string, string> = {
    diagram: '电路图配置 (diagram.json)',
    wokwi_config: 'Wokwi 配置 (wokwi.toml)',
    sketch: 'Arduino 代码 (sketch.ino)',
    screenshot: '仿真截图 (simulation_screenshot.png)',
  };
  return names[fileType] || fileType;
}
