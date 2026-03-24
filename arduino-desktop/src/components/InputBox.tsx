import React from 'react';
import { Send, Hammer, Upload } from 'lucide-react';
import './InputBox.css';

interface InputBoxProps {
  input: string;
  setInput: (value: string) => void;
  isGenerating: boolean;
  onSend: () => void;
  onBuild: () => void;
  onFlash: () => void;
  hasProject: boolean;
}

const InputBox: React.FC<InputBoxProps> = ({
  input,
  setInput,
  isGenerating,
  onSend,
  onBuild,
  onFlash,
  hasProject,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="input-box-container">
      {hasProject && (
        <div className="input-toolbar">
          <div className="action-buttons">
            <button
              className="action-button build"
              onClick={onBuild}
              disabled={isGenerating}
              title="编译项目"
            >
              <Hammer size={16} />
              <span>构建</span>
            </button>
            <button
              className="action-button flash"
              onClick={onFlash}
              disabled={isGenerating}
              title="烧录/仿真"
            >
              <Upload size={16} />
              <span>部署</span>
            </button>
          </div>
        </div>
      )}

      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="描述你的 Arduino 项目需求... (按 Enter 发送，自动检测板卡)"
          disabled={isGenerating}
          rows={3}
        />
        <button
          className="send-button"
          onClick={onSend}
          disabled={isGenerating || !input.trim()}
          title="发送"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

export default InputBox;
