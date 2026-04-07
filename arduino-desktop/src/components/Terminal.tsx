import React from 'react';
import { Check, Circle, AlertTriangle, ChevronRight, Terminal as TermIcon } from 'lucide-react';
import './Terminal.css';

// Block types
export interface CommandBlock {
  type: 'command';
  text: string;
  timestamp: number;
}

export interface ProgressBlock {
  type: 'progress';
  steps: ProgressStep[];
  timestamp: number;
}

export interface ProgressStep {
  label: string;
  status: 'done' | 'running' | 'pending' | 'error';
  detail?: string;  // 步骤的详细说明
}

export interface OutputBlock {
  type: 'output';
  title: string;
  content: string;
  variant?: 'default' | 'serial' | 'code' | 'error';
  timestamp: number;
}

export interface StatusBlock {
  type: 'status';
  message: string;
  variant: 'success' | 'error' | 'info' | 'prompt';
  timestamp: number;
}

export interface LogBlock {
  type: 'log';
  content: string;
  isStreaming?: boolean;
  timestamp: number;
}

export type TerminalBlock = CommandBlock | ProgressBlock | OutputBlock | StatusBlock | LogBlock;

interface TerminalProps {
  blocks: TerminalBlock[];
  endRef: React.RefObject<HTMLDivElement>;
}

const StepIcon: React.FC<{ status: string }> = ({ status }) => {
  switch (status) {
    case 'done':
      return <Check size={14} className="step-icon done" />;
    case 'running':
      return <span className="step-icon running step-spinner">◆</span>;
    case 'error':
      return <AlertTriangle size={14} className="step-icon error" />;
    default:
      return <Circle size={14} className="step-icon pending" />;
  }
};

const Terminal: React.FC<TerminalProps> = ({ blocks, endRef }) => {
  return (
    <div className="terminal">
      {blocks.length === 0 && (
        <div className="terminal-welcome">
          <div className="welcome-icon">
            <TermIcon size={32} />
          </div>
          <div className="welcome-text">描述你的 Arduino 项目需求</div>
          <div className="welcome-hint">例如：用 pico 做 LED 闪烁，GP10 引脚</div>
        </div>
      )}
      {blocks.map((block, i) => {
        switch (block.type) {
          case 'command':
            return (
              <div key={i} className="block block-command">
                <ChevronRight size={14} className="command-chevron" />
                <span className="command-text">{block.text}</span>
              </div>
            );
          case 'progress':
            return (
              <div key={i} className="block block-progress">
                {block.steps.map((step, j) => (
                  <div key={j} className={`progress-step ${step.status}`}>
                    <StepIcon status={step.status} />
                    <div className="step-content">
                      <span className="step-label">{step.label}</span>
                      {step.detail && <span className="step-detail">{step.detail}</span>}
                    </div>
                  </div>
                ))}
              </div>
            );
          case 'output':
            return (
              <div key={i} className={`block block-output ${block.variant || 'default'}`}>
                <div className="output-header">
                  <span className="output-title">{block.title}</span>
                  <span className="output-line" />
                </div>
                <pre className="output-content">{block.content}</pre>
              </div>
            );
          case 'status':
            return (
              <div key={i} className={`block block-status ${block.variant}`}>
                <span>{block.message}</span>
              </div>
            );
          case 'log':
            return (
              <div key={i} className={`block block-log ${block.isStreaming ? 'streaming' : ''}`}>
                <pre className="log-content">{block.content}</pre>
                {block.isStreaming && <span className="log-cursor" />}
              </div>
            );
          default:
            return null;
        }
      })}
      <div ref={endRef} />
    </div>
  );
};

export default Terminal;
