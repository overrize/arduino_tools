import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { Project } from '../types';

export async function exportProjectAsZip(project: Project): Promise<void> {
  const zip = new JSZip();
  
  project.files.forEach(file => {
    zip.file(file.path, file.content);
  });
  
  zip.file('README.md', generateReadme(project));
  
  const blob = await zip.generateAsync({ type: 'blob' });
  saveAs(blob, `${project.name}.zip`);
}

function generateReadme(project: Project): string {
  return `# ${project.name}

## 描述
${project.description}

## 目标板卡
${project.board}

## 文件结构
${project.files.map(f => `- ${f.path}`).join('\n')}

## 使用方法

1. 解压 ZIP 文件
2. 使用 Arduino IDE 或 arduino-cli 打开 .ino 文件
3. 选择目标板卡：${project.board}
4. 编译并上传

## 生成时间
${new Date(project.createdAt).toLocaleString()}
`;
}
