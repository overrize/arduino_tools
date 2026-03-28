import React from 'react';
import { Terminal, CheckCircle, Loader, Hammer, Upload, Cpu, Zap, Activity, Bug } from 'lucide-react';
import './TaskPanel.css';

interface TaskPanelProps {
  status: string;
  logs: string[];
  deployMethod?: 'flash' | 'simulation' | null;
}

const statusConfig: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
  checking: { icon: <Loader size={16} className="spin" />, label: '环境检查', color: '#8b9dc3' },
  detecting: { icon: <Loader size={16} className="spin" />, label: '检测板卡', color: '#9b59b6' },
  generating: { icon: <Loader size={16} className="spin" />, label: '生成代码', color: '#e94560' },
  building: { icon: <Hammer size={16} />, label: '编译项目', color: '#f39c12' },
  deploying: { icon: <Zap size={16} className="spin" />, label: '部署中...', color: '#3498db' },
  flashing: { icon: <Upload size={16} />, label: '烧录固件', color: '#3498db' },
  simulating: { icon: <Cpu size={16} className="spin" />, label: 'Wokwi 仿真', color: '#00d4aa' },
  diagnosing: { icon: <Bug size={16} className="spin" />, label: '诊断修复', color: '#e74c3c' },
  installing: { icon: <Loader size={16} className="spin" />, label: '安装依赖', color: '#f39c12' },
  completed: { icon: <CheckCircle size={16} />, label: '完成', color: '#2ecc71' },
};

const TaskPanel: React.FC<TaskPanelProps> = ({ status, logs, deployMethod }) => {
  let config = statusConfig[status] || statusConfig.checking;
  
  // Override label based on deploy method
  if (status === 'deploying' && deployMethod === 'simulation') {
    config = { ...config, label: '切换到仿真...' };
  }
  const logsEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="task-panel">
      <div className="task-header" style={{ borderColor: config.color }}>
        <div className="task-status" style={{ color: config.color }}>
          {config.icon}
          <span>{config.label}</span>
        </div>
        <div className="task-indicator">
          <div className="pulse-dot" style={{ backgroundColor: config.color }} />
        </div>
      </div>

      <div className="task-logs">
        <div className="logs-header">
          <Terminal size={14} />
          <span>日志输出</span>
        </div>
        <div className="logs-content">
          {logs.length === 0 ? (
            <div className="empty-logs">等待输出...</div>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="log-line">
                <span className="log-time">
                  {new Date().toLocaleTimeString()}
                </span>
                <span className="log-text">{log}</span>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
};

export default TaskPanel;
