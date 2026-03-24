import { Project, ProjectFile } from '../types';

const ARDUINO_SYSTEM_PROMPT = `你是 Arduino 嵌入式开发专家。

生成 Arduino 代码必须遵循以下原则：

1. **零依赖优先** - 不依赖第三方库（U8g2、Adafruit、RTClib 等），直接操作硬件
2. **软件 I2C/SPI** - 使用 bit-bang 实现，不依赖 Wire/SPI 库
3. **setup() 必须包含**:
   - Serial.begin(115200) - 调试输出
   - 每个组件的独立初始化验证（通过 Serial 输出结果）

4. **引脚定义** - 使用清晰的宏定义
5. **调试输出** - 关键操作后输出状态信息到 Serial
6. **平台兼容** - 支持 AVR、RP2040、ESP32

生成的代码必须是完整可编译的 .ino 文件。`;

export async function generateArduinoCode(
  prompt: string,
  board: string,
  apiKey: string,
  baseUrl: string,
  model: string
): Promise<string> {
  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: 'system', content: ARDUINO_SYSTEM_PROMPT },
        { role: 'user', content: `Board: ${board}\n需求: ${prompt}\n\n请生成完整的 Arduino 代码（.ino 文件）。` }
      ],
      temperature: 0.2,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API error: ${error}`);
  }

  const data = await response.json();
  const content = data.choices[0].message.content;
  
  return extractCodeBlock(content);
}

function extractCodeBlock(content: string): string {
  if (content.includes('```cpp')) {
    return content.split('```cpp')[1].split('```')[0].trim();
  } else if (content.includes('```c')) {
    return content.split('```c')[1].split('```')[0].trim();
  } else if (content.includes('```')) {
    return content.split('```')[1].split('```')[0].trim();
  }
  return content.trim();
}

export function generateArduinoProject(
  name: string,
  board: string,
  description: string,
  code: string
): Project {
  const id = Date.now().toString(36) + Math.random().toString(36).substr(2);
  
  return {
    id,
    name,
    board,
    description,
    files: [
      { path: `${name}.ino`, content: code }
    ],
    createdAt: Date.now(),
  };
}

export function saveProject(project: Project): void {
  const projects = loadProjects();
  const existingIndex = projects.findIndex(p => p.id === project.id);
  
  if (existingIndex >= 0) {
    projects[existingIndex] = project;
  } else {
    projects.push(project);
  }
  
  localStorage.setItem('arduino-projects', JSON.stringify(projects));
}

export function loadProjects(): Project[] {
  const data = localStorage.getItem('arduino-projects');
  return data ? JSON.parse(data) : [];
}

export function deleteProject(projectId: string): void {
  const projects = loadProjects().filter(p => p.id !== projectId);
  localStorage.setItem('arduino-projects', JSON.stringify(projects));
}

export function getProject(projectId: string): Project | null {
  return loadProjects().find(p => p.id === projectId) || null;
}
