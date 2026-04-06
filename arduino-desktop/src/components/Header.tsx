import React from 'react';
import { Settings, Cpu } from 'lucide-react';
import { DetectedBoard } from '../App';
import './Header.css';

interface HeaderProps {
  board: DetectedBoard | null;
  onOpenSettings: () => void;
}

const Header: React.FC<HeaderProps> = ({ board, onOpenSettings }) => {
  return (
    <header className="header">
      <div className="header-left">
        <span className="header-logo">⚡</span>
        <span className="header-title">Arduino Tools</span>
      </div>
      <div className="header-center">
        {board ? (
          <span className="board-indicator connected">
            <Cpu size={14} />
            {board.name} ({board.port})
          </span>
        ) : (
          <span className="board-indicator disconnected">
            <Cpu size={14} />
            未连接 — 仿真模式
          </span>
        )}
      </div>
      <div className="header-right">
        <span className="header-version">v0.1.0</span>
        <button className="header-btn" onClick={onOpenSettings} title="设置">
          <Settings size={16} />
        </button>
      </div>
    </header>
  );
};

export default Header;
