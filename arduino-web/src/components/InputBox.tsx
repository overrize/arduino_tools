import React from 'react';
import { Send, Download } from 'lucide-react';
import { Board } from '../types';
import './InputBox.css';

interface InputBoxProps {
  input: string;
  setInput: (value: string) => void;
  selectedBoard: Board;
  setSelectedBoard: (board: Board) => void;
  boards: { value: Board; label: string }[];
  isGenerating: boolean;
  onSend: () => void;
  onExport: () => void;
  hasProject: boolean;
}

const InputBox: React.FC<InputBoxProps> = ({
  input,
  setInput,
  selectedBoard,
  setSelectedBoard,
  boards,
  isGenerating,
  onSend,
  onExport,
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
      <div className="input-toolbar">
        <div className="board-selector">
          <label>目标板卡：</label>
          <select
            value={selectedBoard}
            onChange={(e) => setSelectedBoard(e.target.value as Board)}
            disabled={isGenerating}
          >
            {boards.map((board) => (
              <option key={board.value} value={board.value}>
                {board.label}
              </option>
            ))}
          </select>
        </div>

        {hasProject && (
          <button
            className="export-button"
            onClick={onExport}
            disabled={isGenerating}
            title="导出 ZIP"
          >
            <Download size={16} />
            <span>导出 ZIP</span>
          </button>
        )}
      </div>

      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="描述你的 Arduino 项目需求... (按 Enter 发送)"
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
