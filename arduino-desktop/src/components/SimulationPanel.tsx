import React from 'react';
import { Monitor, ExternalLink, RotateCcw, X, Terminal } from 'lucide-react';
import './SimulationPanel.css';

interface SimulationPanelProps {
  screenshotBase64: string | null;
  diagramJson: string | null;
  serialOutput: string;
  onClose: () => void;
  onReSimulate: () => void;
  onOpenInWokwi: () => void;
}

const SimulationPanel: React.FC<SimulationPanelProps> = ({
  screenshotBase64,
  diagramJson: _diagramJson,
  serialOutput,
  onClose,
  onReSimulate,
  onOpenInWokwi,
}) => {
  const outputEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [serialOutput]);

  return (
    <div className="simulation-panel">
      <div className="simulation-header">
        <div className="simulation-title">
          <Monitor size={18} />
          <span>Wokwi 仿真结果</span>
        </div>
        <button className="simulation-close" onClick={onClose}>
          <X size={16} />
        </button>
      </div>

      <div className="simulation-content">
        {/* Left: Screenshot */}
        <div className="simulation-screenshot-section">
          <div className="section-label">仿真截图</div>
          <div className="screenshot-container">
            {screenshotBase64 ? (
              <img
                src={`data:image/png;base64,${screenshotBase64}`}
                alt="Wokwi Simulation"
                className="simulation-image"
              />
            ) : (
              <div className="screenshot-placeholder">
                <Monitor size={48} opacity={0.3} />
                <span>无截图</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Serial Output */}
        <div className="simulation-output-section">
          <div className="section-label">
            <Terminal size={14} />
            <span>串口输出</span>
          </div>
          <div className="serial-output">
            {serialOutput ? (
              serialOutput.split('\n').map((line, index) => (
                <div key={index} className="output-line">
                  <span className="output-prompt">&gt;</span>
                  <span className="output-text">{line}</span>
                </div>
              ))
            ) : (
              <div className="empty-output">无串口输出</div>
            )}
            <div ref={outputEndRef} />
          </div>
        </div>
      </div>

      {/* Bottom: Actions */}
      <div className="simulation-actions">
        <button className="action-btn primary" onClick={onOpenInWokwi}>
          <ExternalLink size={14} />
          <span>在 Wokwi 中打开</span>
        </button>
        <button className="action-btn secondary" onClick={onReSimulate}>
          <RotateCcw size={14} />
          <span>重新仿真</span>
        </button>
      </div>
    </div>
  );
};

export default SimulationPanel;
