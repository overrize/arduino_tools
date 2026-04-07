import { useState, useEffect, useCallback, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';

import Header from './components/Header';
import Terminal, { TerminalBlock, ProgressStep, CommandBlock, ProgressBlock, OutputBlock, StatusBlock, LogBlock } from './components/Terminal';

type BlockInput = Omit<CommandBlock, 'timestamp'> | Omit<ProgressBlock, 'timestamp'> | Omit<OutputBlock, 'timestamp'> | Omit<StatusBlock, 'timestamp'> | Omit<LogBlock, 'timestamp'>;
import PromptInput from './components/PromptInput';
import SettingsModal from './components/SettingsModal';
import './App.css';

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

type AppState = 'idle' | 'running_e2e' | 'waiting_verify' | 'auto_fixing';

// Map e2e-status strings to progress step labels
const STATUS_LABELS: Record<string, string> = {
  checking: '环境检查',
  detecting: '检测板卡',
  generating: '生成代码',
  building: '编译项目',
  deploying: '部署中',
  flashing: '烧录固件',
  simulating: 'Wokwi 仿真',
  diagnosing: '诊断修复',
  installing: '安装依赖',
  completed: '完成',
};

const ALL_STEPS = ['detecting', 'generating', 'building', 'flashing'];
const SIM_STEPS = ['detecting', 'generating', 'building', 'simulating'];

const STEP_DETAILS: Record<string, string> = {
  detecting: '扫描可用的 Arduino 板卡',
  generating: '调用 AI 生成代码',
  building: '编译固件文件',
  flashing: '烧录到连接的板卡',
  simulating: '在 Wokwi 中运行仿真',
};

function App() {
  const [blocks, setBlocks] = useState<TerminalBlock[]>([]);
  const [input, setInput] = useState('');
  const [appState, setAppState] = useState<AppState>('idle');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [detectedBoard, setDetectedBoard] = useState<DetectedBoard | null>(null);
  const [serialOutput, setSerialOutput] = useState('');
  const [fixRound, setFixRound] = useState(0);
  const endRef = useRef<HTMLDivElement>(null);
  const simulationOutputRef = useRef<string>('');
  const currentStepsRef = useRef<string[]>([]);
  const detectedBoardRef = useRef<DetectedBoard | null>(null);

  useEffect(() => {
    detectedBoardRef.current = detectedBoard;
  }, [detectedBoard]);

  useEffect(() => {
    autoDetectBoard();

    const unlistenStatus = listen('e2e-status', (event: any) => {
      const status = event.payload as string;
      currentStepsRef.current = [...currentStepsRef.current, status];
      updateProgressBlock(currentStepsRef.current, detectedBoardRef.current);
    });

    const unlistenLog = listen('e2e-log', (event: any) => {
      const logLine = event.payload as string;
      setBlocks(prev => {
        const lastBlockIdx = prev.length - 1;
        const lastBlock = prev[lastBlockIdx];

        if (lastBlock && lastBlock.type === 'log') {
          // Append to existing log block
          const updatedLog = { ...lastBlock, content: lastBlock.content + '\n' + logLine };
          return [...prev.slice(0, lastBlockIdx), updatedLog];
        } else {
          // Create new log block
          return [...prev, { type: 'log' as const, content: logLine, isStreaming: true, timestamp: Date.now() }];
        }
      });
    });

    const unlistenSimOutput = listen('simulation-output', (event: any) => {
      simulationOutputRef.current = event.payload as string;
    });

    const detectInterval = setInterval(autoDetectBoard, 10000);

    return () => {
      unlistenStatus.then(fn => fn());
      unlistenLog.then(fn => fn());
      unlistenSimOutput.then(fn => fn());
      clearInterval(detectInterval);
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [blocks]);

  const autoDetectBoard = async () => {
    try {
      const board = await invoke<DetectedBoard | null>('detect_board');
      setDetectedBoard(board);
    } catch {
      setDetectedBoard(null);
    }
  };

  const addBlock = useCallback((block: BlockInput) => {
    setBlocks(prev => [...prev, { ...block, timestamp: Date.now() } as TerminalBlock]);
  }, []);

  const updateProgressBlock = (completedStatuses: string[], board: DetectedBoard | null) => {
    const stepNames = board ? ALL_STEPS : SIM_STEPS;
    const steps: ProgressStep[] = stepNames.map(s => {
      const label = STATUS_LABELS[s] || s;
      const detail = STEP_DETAILS[s];
      if (completedStatuses.includes(s)) {
        const idx = completedStatuses.lastIndexOf(s);
        if (idx === completedStatuses.length - 1) {
          return { label, status: 'running' as const, detail };
        }
        return { label, status: 'done' as const, detail };
      }
      return { label, status: 'pending' as const, detail };
    });

    setBlocks(prev => {
      const last = prev[prev.length - 1];
      if (last && last.type === 'progress') {
        return [...prev.slice(0, -1), { ...last, steps }];
      }
      return [...prev, { type: 'progress', steps, timestamp: Date.now() }];
    });
  };

  const captureSerial = async (port: string): Promise<string> => {
    try {
      const result = await invoke<{ success: boolean; data: string; error?: string }>(
        'capture_serial_output',
        { port, baudRate: 115200, durationSecs: 8 }
      );
      return result.success ? result.data : '';
    } catch {
      return '';
    }
  };

  const runEndToEnd = async (userInput: string) => {
    setAppState('running_e2e');
    setIsProcessing(true);
    setFixRound(0);
    currentStepsRef.current = [];

    const board = detectedBoardRef.current;
    const stepNames = board ? ALL_STEPS : SIM_STEPS;
    addBlock({
      type: 'progress',
      steps: stepNames.map(s => ({
        label: STATUS_LABELS[s] || s,
        status: 'pending' as const,
        detail: STEP_DETAILS[s],
      })),
    });

    try {
      const project = await invoke<Project>('run_end_to_end', {
        request: { prompt: userInput, board: board?.fqbn || null, name: null },
      });

      setCurrentProject(project);

      // Mark all progress steps as done
      setBlocks(prev => {
        const last = prev[prev.length - 1];
        if (last && last.type === 'progress') {
          return [
            ...prev.slice(0, -1),
            { ...last, steps: last.steps.map(s => ({ ...s, status: 'done' as const })) },
          ];
        }
        return prev;
      });

      const method = board ? `烧录到 ${board.name}` : 'Wokwi 仿真';
      addBlock({
        type: 'output',
        title: '项目',
        content: `${project.name}  ·  ${project.board}  ·  ${method}`,
        variant: 'default',
      });

      if (board) {
        const serialData = await captureSerial(board.port);
        setSerialOutput(serialData);
        if (serialData) {
          addBlock({
            type: 'output',
            title: 'serial output',
            content: serialData.slice(0, 1500),
            variant: 'serial',
          });
        }
      } else {
        const simOutput = simulationOutputRef.current;
        simulationOutputRef.current = '';
        const userLines = simOutput
          ? simOutput
              .split('\n')
              .filter(line => {
                const l = line.trim();
                return (
                  l &&
                  !l.startsWith('Wokwi CLI') &&
                  !l.startsWith('Connected to') &&
                  !l.startsWith('Starting simulation') &&
                  !l.startsWith('Timeout:')
                );
              })
              .join('\n')
          : '';
        const displayOutput = userLines || '（无串口输出）';
        setSerialOutput(displayOutput);
        if (userLines) {
          addBlock({
            type: 'output',
            title: 'serial output',
            content: displayOutput,
            variant: 'serial',
          });
        }
      }

      addBlock({
        type: 'status',
        message: '✓ 完成。功能正常？(Enter 确认 / 描述问题)',
        variant: 'prompt',
      });
      setAppState('waiting_verify');
    } catch (error: any) {
      setBlocks(prev => {
        const last = prev[prev.length - 1];
        if (last && last.type === 'progress') {
          return [
            ...prev.slice(0, -1),
            {
              ...last,
              steps: last.steps.map(s =>
                s.status === 'running' ? { ...s, status: 'error' as const } : s
              ),
            },
          ];
        }
        return prev;
      });
      addBlock({
        type: 'status',
        message: `✗ 失败：${error.toString()}`,
        variant: 'error',
      });
      setAppState('idle');
    } finally {
      setIsProcessing(false);
    }
  };

  const runAutoFix = async (issueDescription: string) => {
    if (!currentProject) return;

    setAppState('auto_fixing');
    setIsProcessing(true);
    currentStepsRef.current = [];

    addBlock({
      type: 'progress',
      steps: [
        { label: '诊断问题', status: 'running' as const, detail: '分析错误原因' },
        { label: '修复代码', status: 'pending' as const, detail: '调整代码逻辑' },
        { label: '重新编译', status: 'pending' as const, detail: '编译修复后的代码' },
        { label: '验证', status: 'pending' as const, detail: '确认功能正常' },
      ],
    });

    try {
      const result = await invoke<DebugResult>('debug_and_fix', {
        request: {
          project_id: currentProject.id,
          issue_description: issueDescription,
          serial_output: serialOutput,
        },
      });

      if (result.success) {
        setBlocks(prev => {
          const last = prev[prev.length - 1];
          if (last && last.type === 'progress') {
            return [
              ...prev.slice(0, -1),
              { ...last, steps: last.steps.map(s => ({ ...s, status: 'done' as const })) },
            ];
          }
          return prev;
        });

        addBlock({ type: 'output', title: '诊断', content: result.diagnosis, variant: 'default' });
        addBlock({ type: 'output', title: '修改', content: result.changes, variant: 'code' });

        const board = detectedBoardRef.current;
        if (board) {
          const newSerial = await captureSerial(board.port);
          setSerialOutput(newSerial);
          if (newSerial) {
            addBlock({
              type: 'output',
              title: 'serial output',
              content: newSerial.slice(0, 1500),
              variant: 'serial',
            });
          }
        }

        addBlock({
          type: 'status',
          message: `✓ 修复完成 (${fixRound + 1}/5)。功能正常？(Enter 确认 / 描述问题)`,
          variant: 'prompt',
        });
        setAppState('waiting_verify');
        setFixRound(prev => prev + 1);
      } else {
        setBlocks(prev => {
          const last = prev[prev.length - 1];
          if (last && last.type === 'progress') {
            return [
              ...prev.slice(0, -1),
              {
                ...last,
                steps: last.steps.map(s =>
                  s.status === 'running' ? { ...s, status: 'error' as const } : s
                ),
              },
            ];
          }
          return prev;
        });
        addBlock({
          type: 'status',
          message: `✗ 修复失败：${result.message}`,
          variant: 'error',
        });
        setAppState('idle');
        setFixRound(0);
      }
    } catch (error: any) {
      addBlock({
        type: 'status',
        message: `✗ 修复失败：${error.toString()}`,
        variant: 'error',
      });
      setAppState('idle');
      setFixRound(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSubmit = async () => {
    if (!input.trim() || isProcessing) return;
    const userInput = input.trim();
    addBlock({ type: 'command', text: userInput });
    setInput('');

    if (appState === 'waiting_verify') {
      if (!userInput || userInput.toLowerCase() === 'y' || userInput === '正常') {
        addBlock({ type: 'status', message: '✓ 验证通过，项目完成。', variant: 'success' });
        setAppState('idle');
        setFixRound(0);
      } else {
        if (fixRound >= 5) {
          addBlock({
            type: 'status',
            message: '已达最大修复轮数 (5)。请重新描述需求。',
            variant: 'error',
          });
          setAppState('idle');
          setFixRound(0);
        } else {
          await runAutoFix(userInput);
        }
      }
    } else {
      await runEndToEnd(userInput);
    }
  };

  const getPlaceholder = () => {
    switch (appState) {
      case 'waiting_verify':
        return '正常？(Enter 确认 / 描述问题)';
      case 'running_e2e':
      case 'auto_fixing':
        return '处理中...';
      default:
        return '描述你的 Arduino 项目需求...';
    }
  };

  return (
    <div className="app">
      <Header board={detectedBoard} onOpenSettings={() => setShowSettings(true)} />
      <Terminal blocks={blocks} endRef={endRef} />
      <PromptInput
        value={input}
        onChange={setInput}
        onSubmit={handleSubmit}
        disabled={isProcessing}
        placeholder={getPlaceholder()}
      />
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </div>
  );
}

export default App;
