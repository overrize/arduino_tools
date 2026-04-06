import React from 'react';
import { ArrowRight } from 'lucide-react';
import './PromptInput.css';

interface PromptInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  placeholder?: string;
}

const PromptInput: React.FC<PromptInputProps> = ({ value, onChange, onSubmit, disabled, placeholder }) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="prompt-container">
      <span className="prompt-symbol">&gt;</span>
      <input
        type="text"
        className="prompt-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder || '输入指令...'}
        autoFocus
      />
      <button
        className="prompt-submit"
        onClick={onSubmit}
        disabled={disabled || !value.trim()}
      >
        <ArrowRight size={16} />
      </button>
    </div>
  );
};

export default PromptInput;
