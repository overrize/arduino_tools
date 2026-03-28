import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { Project } from '../types';

export async function exportProjectAsZip(project: Project): Promise<void> {
  const zip = new JSZip();
  
  project.files.forEach(file => {
    zip.file(file.path, file.content);
  });
  
  zip.file('README.md', generateReadme(project));
  zip.file('wokwi.toml', generateWokwiConfig(project.board));
  zip.file('diagram.json', generateDiagramJson(project.board));
  
  const blob = await zip.generateAsync({ type: 'blob' });
  saveAs(blob, `${project.name}.zip`);
}

export function openInWokwi(project: Project): void {
  const code = project.files.find(f => f.path.endsWith('.ino'))?.content || '';
  const diagram = generateDiagramJson(project.board);
  
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = 'https://wokwi.com/projects/new';
  form.target = '_blank';
  
  const codeInput = document.createElement('input');
  codeInput.type = 'hidden';
  codeInput.name = 'code';
  codeInput.value = code;
  form.appendChild(codeInput);
  
  const diagramInput = document.createElement('input');
  diagramInput.type = 'hidden';
  diagramInput.name = 'diagram';
  diagramInput.value = diagram;
  form.appendChild(diagramInput);
  
  document.body.appendChild(form);
  form.submit();
  document.body.removeChild(form);
}

function generateWokwiConfig(board: string): string {
  const boardId = boardToWokwiId(board);
  return `[wokwi]\nversion = 1\nfirmware = 'build/${boardId}.ino.hex'\n`;
}

function generateDiagramJson(board: string): string {
  const boardId = boardToWokwiId(board);
  const diagram = {
    version: 1,
    author: 'Arduino Web',
    editor: 'wokwi',
    parts: [{ type: boardId, id: 'board', top: 0, left: 0, attrs: {} }],
    connections: [],
    dependencies: {}
  };
  return JSON.stringify(diagram, null, 2);
}

function boardToWokwiId(board: string): string {
  switch (board) {
    case 'arduino:avr:uno': return 'wokwi-arduino-uno';
    case 'arduino:avr:nano': return 'wokwi-arduino-nano';
    case 'arduino:mbed_rp2040:pico': return 'wokwi-pi-pico';
    case 'esp32:esp32:esp32': return 'wokwi-esp32-devkit-v1';
    default: return 'wokwi-arduino-uno';
  }
}

function generateReadme(project: Project): string {
  return `# ${project.name}

## 描述
${project.description}

## 目标板卡
${project.board}

## 文件结构
${project.files.map(f => `- ${f.path}`).join('\n')}
- wokwi.toml - Wokwi 仿真配置
- diagram.json - Wokwi 电路图

## 使用方法

### Arduino IDE
1. 解压 ZIP 文件
2. 使用 Arduino IDE 打开 .ino 文件
3. 选择目标板卡：${project.board}
4. 编译并上传

### Wokwi 在线仿真
1. 访问 https://wokwi.com
2. 上传 .ino 文件和 diagram.json
3. 开始仿真

## 生成时间
${new Date(project.createdAt).toLocaleString()}
`;
}
