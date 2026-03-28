import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Message, Project, Board, LLMConfig } from './types';
import { generateArduinoCode, generateArduinoProject, saveProject, loadProjects, deleteProject, getProject } from './lib/project';
import { exportProjectAsZip, openInWokwi } from './lib/export';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';
import InputBox from './components/InputBox';
import SettingsModal from './components/SettingsModal';
import './App.css';

const BOARDS: { value: Board; label: string }[] = [
  { value: 'arduino:avr:uno', label: 'Arduino Uno' },
  { value: 'arduino:avr:nano', label: 'Arduino Nano' },
  { value: 'arduino:mbed_rp2040:pico', label: 'Raspberry Pi Pico' },
  { value: 'esp32:esp32:esp32', label: 'ESP32' },
];

const INITIAL_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: '你好！我是 Arduino Web。\n\n描述你的项目需求，我会帮你生成 Arduino 代码并导出 ZIP。\n\n**工作流**: 描述需求 → AI 生成代码 → 导出 ZIP → 在 Arduino IDE 或 Wokwi 中运行\n\n例如：\n- "LED 闪烁，13号引脚，每秒闪一次"\n- "用温度传感器读取温度并通过串口输出"\n\n请选择目标板卡，然后开始描述你的需求。',
  timestamp: Date.now(),
};

function App() {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [input, setInput] = useState('');
  const [selectedBoard, setSelectedBoard] = useState<Board>('arduino:avr:uno');
  const [isGenerating, setIsGenerating] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [llmConfig, setLLMConfig] = useState<LLMConfig>({
    apiKey: localStorage.getItem('llm-api-key') || '',
    baseUrl: localStorage.getItem('llm-base-url') || 'https://api.moonshot.cn/v1',
    model: localStorage.getItem('llm-model') || 'kimi-k2-0905-preview',
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setProjects(loadProjects());
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString(),
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, newMessage]);
  }, []);

  const handleSendMessage = async () => {
    if (!input.trim() || isGenerating) return;

    if (!llmConfig.apiKey) {
      addMessage({
        role: 'assistant',
        content: '请先配置 LLM API。点击右上角的设置按钮进行配置。',
      });
      setShowSettings(true);
      return;
    }

    addMessage({ role: 'user', content: input });
    setInput('');
    setIsGenerating(true);

    const loadingId = Date.now().toString();
    addMessage({ role: 'assistant', content: '正在生成代码...', isLoading: true });

    try {
      const code = await generateArduinoCode(
        input,
        selectedBoard,
        llmConfig.apiKey,
        llmConfig.baseUrl,
        llmConfig.model
      );

      const projectName = input.slice(0, 20).replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_') || 'project';
      const project = generateArduinoProject(projectName, selectedBoard, input, code);
      
      saveProject(project);
      setProjects(loadProjects());
      setCurrentProject(project);

      setMessages(prev => prev.filter(m => m.id !== loadingId));
      addMessage({
        role: 'assistant',
        content: `✅ 代码生成成功！\n\n项目名称：${project.name}\n目标板卡：${selectedBoard}\n\n代码已生成，你可以：\n1. 在右侧面板查看代码\n2. 点击"导出 ZIP"下载项目\n3. 使用 Arduino IDE 或 arduino-cli 编译上传`,
      });
    } catch (error: any) {
      setMessages(prev => prev.filter(m => m.id !== loadingId));
      addMessage({
        role: 'assistant',
        content: `❌ 生成失败：${error.message}`,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExportProject = async () => {
    if (!currentProject) return;
    
    try {
      await exportProjectAsZip(currentProject);
      addMessage({
        role: 'assistant',
        content: `✅ 项目已导出：${currentProject.name}.zip\n\n包含 Wokwi 配置文件，可直接导入 https://wokwi.com 在线仿真。`,
      });
    } catch (error: any) {
      addMessage({
        role: 'assistant',
        content: `❌ 导出失败：${error.message}`,
      });
    }
  };

  const handleOpenInWokwi = () => {
    if (!currentProject) return;
    openInWokwi(currentProject);
  };

  const handleNewProject = () => {
    setCurrentProject(null);
    setMessages([INITIAL_MESSAGE]);
  };

  const handleSelectProject = (projectId: string) => {
    const project = getProject(projectId);
    if (project) {
      setCurrentProject(project);
      addMessage({
        role: 'system',
        content: `已加载项目：${project.name}`,
      });
    }
  };

  const handleDeleteProject = (projectId: string) => {
    deleteProject(projectId);
    setProjects(loadProjects());
    if (currentProject?.id === projectId) {
      handleNewProject();
    }
  };

  const handleSaveConfig = (config: LLMConfig) => {
    setLLMConfig(config);
    localStorage.setItem('llm-api-key', config.apiKey);
    localStorage.setItem('llm-base-url', config.baseUrl);
    localStorage.setItem('llm-model', config.model);
    setShowSettings(false);
  };

  return (
    <div className="app">
      <Sidebar
        projects={projects}
        currentProject={currentProject}
        onSelectProject={handleSelectProject}
        onDeleteProject={handleDeleteProject}
        onNewProject={handleNewProject}
        onOpenSettings={() => setShowSettings(true)}
      />
      
      <div className="main-content">
        <Chat messages={messages} messagesEndRef={messagesEndRef} />
        <InputBox
          input={input}
          setInput={setInput}
          selectedBoard={selectedBoard}
          setSelectedBoard={setSelectedBoard}
          boards={BOARDS}
          isGenerating={isGenerating}
          onSend={handleSendMessage}
          onExport={handleExportProject}
          onOpenInWokwi={handleOpenInWokwi}
          hasProject={!!currentProject}
        />
      </div>

      {showSettings && (
        <SettingsModal
          config={llmConfig}
          onSave={handleSaveConfig}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}

export default App;
