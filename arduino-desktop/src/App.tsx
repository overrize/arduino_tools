import { useState, useEffect, useCallback, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';
import { open } from '@tauri-apps/api/shell';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';
import InputBox from './components/InputBox';
import TaskPanel from './components/TaskPanel';
import SimulationPanel from './components/SimulationPanel';
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

export interface DebugResult {
  success: boolean;
  diagnosis: string;
  changes: string;
  build_success: boolean;
  upload_success: boolean;
  message: string;
}

const INITIAL_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: '你好！我是 Arduino Desktop。\n\n**只需描述你的项目需求，我会自动完成全部流程：**\n生成代码 → 编译 → 烧录/仿真 → 串口验证\n\n如果功能不正常，告诉我问题，我会自动诊断修复。\n\n例如：\n- "用 pico 做 LED 闪烁，GP10 引脚"\n- "用温度传感器读取温度并通过串口输出"\n\n如果没有连接板卡，会自动切换到 Wokwi 仿真（首次使用会自动安装 wokwi-cli）。',
  timestamp: Date.now(),
};

type AppState = 
  | 'idle'
  | 'running_e2e'
  | 'waiting_verify'
  | 'auto_fixing';

function App() {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [input, setInput] = useState('');
  const [appState, setAppState] = useState<AppState>('idle');
  const [isProcessing, setIsProcessing] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [taskLogs, setTaskLogs] = useState<string[]>([]);
  const [detectedBoard, setDetectedBoard] = useState<DetectedBoard | null>(null);
  const [serialOutput, setSerialOutput] = useState('');
  const [fixRound, setFixRound] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const simulationOutputRef = useRef<string>('');
  const [simulationScreenshot, setSimulationScreenshot] = useState<string | null>(null);
  const [simulationDiagram, setSimulationDiagram] = useState<string | null>(null);
  const [showSimPanel, setShowSimPanel] = useState(false);

  useEffect(() => {
    loadProjects();
    autoDetectBoard();

    const unlistenStatus = listen('e2e-status', (event: any) => {
      setTaskStatus(event.payload);
    });

    const unlistenLog = listen('e2e-log', (event: any) => {
      setTaskLogs(prev => [...prev, event.payload]);
    });

    const unlistenSimOutput = listen('simulation-output', (event: any) => {
      simulationOutputRef.current = event.payload as string;
    });

    const unlistenScreenshot = listen('simulation-screenshot', (event: any) => {
      setSimulationScreenshot(event.payload as string);
    });

    const unlistenDiagram = listen('simulation-diagram', (event: any) => {
      setSimulationDiagram(event.payload as string);
    });

    const detectInterval = setInterval(autoDetectBoard, 10000);

    return () => {
      unlistenStatus.then(fn => fn());
      unlistenLog.then(fn => fn());
      unlistenSimOutput.then(fn => fn());
      unlistenScreenshot.then(fn => fn());
      unlistenDiagram.then(fn => fn());
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

  const captureSerial = async (port: string): Promise<string> => {
    try {
      const result = await invoke<{
        success: boolean;
        data: string;
        error?: string;
      }>('capture_serial_output', {
        port: port,
        baudRate: 115200,
        durationSecs: 8,
      });

      if (result.success) {
        return result.data;
      }
      return '';
    } catch {
      return '';
    }
  };

  const runAutoFix = async (issueDescription: string) => {
    if (!currentProject) return;

    setAppState('auto_fixing');
    setTaskStatus('diagnosing');
    setTaskLogs([]);
    setIsProcessing(true);

    const loadingId = addMessage({
      role: 'assistant',
      content: `第 ${fixRound + 1}/5 轮自动修复...\n\n问题：${issueDescription}`,
      isLoading: true,
    });

    try {
      const result = await invoke<DebugResult>('debug_and_fix', {
        request: {
          project_id: currentProject.id,
          issue_description: issueDescription,
          serial_output: serialOutput,
        },
      });

      setMessages(prev => prev.filter(m => m.id !== loadingId));

      if (result.success) {
        addMessage({
          role: 'assistant',
          content: `自动修复成功！\n\n**诊断**：${result.diagnosis}\n\n**修改**：${result.changes}\n\n代码已更新并重新上传。`,
        });

        if (detectedBoard) {
          addMessage({
            role: 'assistant',
            content: '正在重新采集串口输出验证...',
          });
          
          const newSerialOutput = await captureSerial(detectedBoard.port);
          setSerialOutput(newSerialOutput);
          
          const displayData = newSerialOutput || '（无输出）';
          addMessage({
            role: 'assistant',
            content: `串口输出：\n\n\`\`\`\n${displayData.slice(0, 1500)}\n\`\`\`${newSerialOutput.length > 1500 ? '\n\n... (已截断)' : ''}\n\n功能是否正常？（正常请按 Enter，有问题请描述）`,
          });
        } else {
          addMessage({
            role: 'assistant',
            content: '修复完成。功能是否正常？（正常请按 Enter，有问题请描述）',
          });
        }

        setAppState('waiting_verify');
        setFixRound(prev => prev + 1);
      } else {
        addMessage({
          role: 'assistant',
          content: `自动修复遇到问题\n\n**诊断**：${result.diagnosis}\n\n**修改**：${result.changes}\n\n**状态**：${result.message}\n\n请尝试重新描述需求，或检查硬件连接。`,
        });
        setAppState('idle');
        setFixRound(0);
      }
    } catch (error: any) {
      setMessages(prev => prev.filter(m => m.id !== loadingId));
      addMessage({ role: 'assistant', content: `自动修复失败：${error.toString()}` });
      setAppState('idle');
      setFixRound(0);
    } finally {
      setIsProcessing(false);
      setTaskStatus(null);
    }
  };

  const runEndToEnd = async (userInput: string) => {
    setAppState('running_e2e');
    setIsProcessing(true);
    setTaskStatus('detecting');
    setTaskLogs([]);
    setFixRound(0);

    const loadingId = addMessage({
      role: 'assistant',
      content: detectedBoard
        ? `检测到板卡：${detectedBoard.name} (${detectedBoard.port})\n正在执行端到端流程...`
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
      setCurrentProject(project);
      await loadProjects();

      const method = detectedBoard ? `已烧录到 ${detectedBoard.name}` : '已通过 Wokwi 仿真';

      addMessage({
        role: 'assistant',
        content: `端到端流程完成！\n\n**项目**：${project.name}\n**板卡**：${project.board}\n**部署**：${method}`,
      });

      if (detectedBoard) {
        addMessage({
          role: 'assistant',
          content: '正在采集串口输出进行验证...',
        });

        const serialData = await captureSerial(detectedBoard.port);
        setSerialOutput(serialData);

        const displayData = serialData || '（无输出）';
        addMessage({
          role: 'assistant',
          content: `串口输出：\n\n\`\`\`\n${displayData.slice(0, 1500)}\n\`\`\`${serialData.length > 1500 ? '\n\n... (已截断)' : ''}\n\n功能是否正常？（正常请按 Enter，有问题请描述）`,
        });

        setAppState('waiting_verify');
      } else {
        const simOutput = simulationOutputRef.current;
        simulationOutputRef.current = '';

        const userLines = simOutput
          ? simOutput.split('\n').filter(line => {
              const l = line.trim();
              return l && !l.startsWith('Wokwi CLI') && !l.startsWith('Connected to') && !l.startsWith('Starting simulation') && !l.startsWith('Timeout:');
            }).join('\n')
          : '';

        const displayOutput = userLines || '（无串口输出 — 固件可能未调用 Serial.print）';

        setSerialOutput(displayOutput);
        setShowSimPanel(true);
        setAppState('waiting_verify');
      }
    } catch (error: any) {
      setMessages(prev => prev.filter(m => m.id !== loadingId));
      addMessage({
        role: 'assistant',
        content: `流程失败：${error.toString()}\n\n请检查：\n1. arduino-cli 是否安装\n2. LLM API 配置是否正确\n3. 板卡连接是否正常`,
      });
      setAppState('idle');
    } finally {
      setIsProcessing(false);
      setTaskStatus(null);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isProcessing) return;

    const userInput = input.trim();
    addMessage({ role: 'user', content: userInput });
    setInput('');

    if (appState === 'waiting_verify') {
      if (!userInput || userInput.toLowerCase() === 'y' || userInput.toLowerCase() === 'yes' || userInput === '正常') {
        addMessage({
          role: 'assistant',
          content: '验证通过！项目已完成。\n\n如需创建新项目，直接描述新需求即可。',
        });
        setAppState('idle');
        setFixRound(0);
        setShowSimPanel(false);
      } else {
        if (fixRound >= 5) {
          addMessage({
            role: 'assistant',
            content: '已达到最大修复轮数（5轮）。\n\n建议：\n1. 重新描述需求，换个方式表达\n2. 检查硬件连接\n3. 尝试在 CLI 版本中获得更详细的调试信息',
          });
          setAppState('idle');
          setFixRound(0);
          setShowSimPanel(false);
        } else {
          await runAutoFix(userInput);
        }
      }
    } else {
      await runEndToEnd(userInput);
    }
  };

  const handleNewProject = () => {
    setCurrentProject(null);
    setMessages([INITIAL_MESSAGE]);
    setAppState('idle');
    setTaskStatus(null);
    setTaskLogs([]);
    setFixRound(0);
    setSerialOutput('');
    simulationOutputRef.current = '';
    setSimulationScreenshot(null);
    setSimulationDiagram(null);
    setShowSimPanel(false);
  };

  const handleSelectProject = async (projectId: string) => {
    try {
      const project = await invoke<Project>('get_project', { projectId });
      setCurrentProject(project);
      setAppState('idle');
      addMessage({
        role: 'system',
        content: `已加载项目：${project.name}\n\n直接发送消息即可重新生成/修改代码。`,
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

  const handleOpenInWokwi = async () => {
    if (simulationDiagram) {
      const encodedDiagram = encodeURIComponent(simulationDiagram);
      const code = currentProject?.files.find(f => f.path.endsWith('.ino'))?.content || '';
      const encodedCode = encodeURIComponent(code);
      await open(`https://wokwi.com/projects/new?diagram=${encodedDiagram}&code=${encodedCode}`);
    }
  };

  const handleReSimulate = async () => {
    if (currentProject) {
      setShowSimPanel(false);
      setSimulationScreenshot(null);
      setSimulationDiagram(null);
      await runEndToEnd(currentProject.description);
    }
  };

  const getPlaceholder = () => {
    switch (appState) {
      case 'waiting_verify':
        return '功能是否正常？（正常请按 Enter，有问题请描述）';
      case 'running_e2e':
      case 'auto_fixing':
        return '处理中，请稍候...';
      default:
        return '描述你的 Arduino 项目需求... (按 Enter 发送)';
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
              {detectedBoard.name} ({detectedBoard.port})
            </span>
          ) : (
            <span className="board-disconnected">
              未检测到板卡 — 将使用仿真
            </span>
          )}
        </div>

        <div className="chat-section">
          <Chat messages={messages} messagesEndRef={messagesEndRef} />
          <InputBox
            input={input}
            setInput={setInput}
            isGenerating={isProcessing}
            onSend={handleSendMessage}
            placeholder={getPlaceholder()}
          />
        </div>

        {taskStatus && !showSimPanel && (
          <TaskPanel
            status={taskStatus}
            logs={taskLogs}
            deployMethod={detectedBoard ? 'flash' : 'simulation'}
          />
        )}

        {showSimPanel && (
          <SimulationPanel
            screenshotBase64={simulationScreenshot}
            diagramJson={simulationDiagram}
            serialOutput={serialOutput}
            onClose={() => setShowSimPanel(false)}
            onReSimulate={handleReSimulate}
            onOpenInWokwi={handleOpenInWokwi}
          />
        )}
      </div>

      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

export default App;
