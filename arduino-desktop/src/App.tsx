import { useState, useEffect, useCallback, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';
import InputBox from './components/InputBox';
import TaskPanel from './components/TaskPanel';
import SettingsModal from './components/SettingsModal';
import './App.css';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  isLoading?: boolean;
}

export interface Project {
  id: string;
  name: string;
  board: string;
  description: string;
  files: ProjectFile[];
  createdAt: number;
}

export interface ProjectFile {
  path: string;
  content: string;
}

export interface DetectedBoard {
  port: string;
  fqbn: string;
  name: string;
}

const INITIAL_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: '你好！我是 Arduino Desktop。\n\n直接描述你的项目需求，我会自动完成全部流程：\n**检测板卡 → 生成代码 → 编译 → 烧录/仿真**\n\n例如：\n- "LED 闪烁，13号引脚，每秒闪一次"\n- "用温度传感器读取温度并通过串口输出"\n\n如果没有连接板卡，会自动切换到 Wokwi 仿真。',
  timestamp: Date.now(),
};

function App() {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [taskLogs, setTaskLogs] = useState<string[]>([]);
  const [detectedBoard, setDetectedBoard] = useState<DetectedBoard | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadProjects();
    autoDetectBoard();

    const unlistenStatus = listen('e2e-status', (event: any) => {
      setTaskStatus(event.payload);
    });

    const unlistenLog = listen('e2e-log', (event: any) => {
      setTaskLogs(prev => [...prev, event.payload]);
    });

    // Re-detect board every 10 seconds
    const detectInterval = setInterval(autoDetectBoard, 10000);

    return () => {
      unlistenStatus.then(fn => fn());
      unlistenLog.then(fn => fn());
      clearInterval(detectInterval);
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const autoDetectBoard = async () => {
    try {
      const board = await invoke<DetectedBoard | null>('detect_board');
      setDetectedBoard(board);
    } catch {
      setDetectedBoard(null);
    }
  };

  const loadProjects = async () => {
    try {
      const projectList = await invoke<Project[]>('list_projects');
      setProjects(projectList);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString(),
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage.id;
  }, []);

  const handleSendMessage = async () => {
    if (!input.trim() || isGenerating) return;

    const userInput = input;
    addMessage({ role: 'user', content: userInput });
    setInput('');
    setIsGenerating(true);
    setTaskStatus('detecting');
    setTaskLogs([]);

    const loadingId = addMessage({
      role: 'assistant',
      content: detectedBoard
        ? `检测到板卡: ${detectedBoard.name} (${detectedBoard.port})\n正在执行端到端流程...`
        : '未检测到板卡，将使用仿真模式。\n正在执行端到端流程...',
      isLoading: true,
    });

    try {
      const project = await invoke<Project>('run_end_to_end', {
        request: {
          prompt: userInput,
          board: detectedBoard?.fqbn || null,
          name: null,
        },
      });

      setMessages(prev => prev.filter(m => m.id !== loadingId));

      const method = detectedBoard ? `已烧录到 ${detectedBoard.name}` : '已通过 Wokwi 仿真';
      addMessage({
        role: 'assistant',
        content: `✅ 端到端流程完成！\n\n**项目**: ${project.name}\n**板卡**: ${project.board}\n**部署**: ${method}\n\n代码已生成并保存到项目列表。`,
      });

      setCurrentProject(project);
      await loadProjects();
    } catch (error: any) {
      setMessages(prev => prev.filter(m => m.id !== loadingId));
      addMessage({
        role: 'assistant',
        content: `❌ 流程失败：${error.toString()}`,
      });
    } finally {
      setIsGenerating(false);
      setTaskStatus(null);
    }
  };

  const handleBuild = async () => {
    if (!currentProject) return;

    setTaskStatus('building');
    setTaskLogs([]);

    try {
      await invoke('build_project', {
        projectDir: currentProject.id,
        fqbn: currentProject.board,
      });

      addMessage({
        role: 'assistant',
        content: '✅ 构建成功！',
      });
    } catch (error: any) {
      addMessage({
        role: 'assistant',
        content: `❌ 构建失败：${error.toString()}`,
      });
    } finally {
      setTaskStatus(null);
    }
  };

  const handleFlash = async () => {
    if (!currentProject) return;

    setTaskStatus('deploying');
    setTaskLogs([]);

    try {
      const result = await invoke<any>('flash_project', {
        projectDir: currentProject.id,
        fqbn: currentProject.board,
      });

      const icon = result.success ? '✅' : '⚠️';
      const methodLabel = result.method === 'flash' ? '烧录' : '仿真';
      addMessage({
        role: 'assistant',
        content: `${icon} ${methodLabel}: ${result.message}`,
      });
    } catch (error: any) {
      addMessage({
        role: 'assistant',
        content: `❌ 部署失败：${error.toString()}`,
      });
    } finally {
      setTaskStatus(null);
    }
  };

  const handleNewProject = () => {
    setCurrentProject(null);
    setMessages([INITIAL_MESSAGE]);
    setTaskStatus(null);
    setTaskLogs([]);
  };

  const handleSelectProject = async (projectId: string) => {
    try {
      const project = await invoke<Project>('get_project', { projectId });
      setCurrentProject(project);
      addMessage({
        role: 'system',
        content: `已加载项目：${project.name}`,
      });
    } catch (error) {
      console.error('Failed to load project:', error);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    try {
      await invoke('delete_project', { projectId });
      await loadProjects();
      if (currentProject?.id === projectId) {
        handleNewProject();
      }
    } catch (error) {
      console.error('Failed to delete project:', error);
    }
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
        <div className="board-status">
          {detectedBoard ? (
            <span className="board-connected">
              ● {detectedBoard.name} ({detectedBoard.port})
            </span>
          ) : (
            <span className="board-disconnected">
              ○ 未检测到板卡 — 将使用仿真
            </span>
          )}
        </div>

        <div className="chat-section">
          <Chat messages={messages} messagesEndRef={messagesEndRef} />
          <InputBox
            input={input}
            setInput={setInput}
            isGenerating={isGenerating}
            onSend={handleSendMessage}
            onBuild={handleBuild}
            onFlash={handleFlash}
            hasProject={!!currentProject}
          />
        </div>

        {taskStatus && (
          <TaskPanel status={taskStatus} logs={taskLogs} />
        )}
      </div>

      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

export default App;
