import React from 'react';
import { Send } from 'lucide-react';
import './InputBox.css';

interface InputBoxProps {
  input: string;
  setInput: (value: string) => void;
  isGenerating: boolean;
  onSend: () => void;
  placeholder?: string;
}

const InputBox: React.FC<InputBoxProps> = ({
  input,
  setInput,
  isGenerating,
  onSend,
  placeholder = '描述你的 Arduino 项目需求... (按 Enter 发送)',
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="input-box-container">
      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
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
