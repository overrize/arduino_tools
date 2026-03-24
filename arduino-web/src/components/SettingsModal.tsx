import React, { useState } from 'react';
import { X, Check, AlertCircle } from 'lucide-react';
import { LLMConfig } from '../types';
import './SettingsModal.css';

interface SettingsModalProps {
  config: LLMConfig;
  onSave: (config: LLMConfig) => void;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ config, onSave, onClose }) => {
  const [localConfig, setLocalConfig] = useState<LLMConfig>(config);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const handleValidate = async () => {
    setIsValidating(true);
    setMessage(null);

    try {
      const response = await fetch(`${localConfig.baseUrl}/models`, {
        headers: {
          'Authorization': `Bearer ${localConfig.apiKey}`,
        },
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'API 连接正常' });
      } else {
        setMessage({ type: 'error', text: 'API 连接失败，请检查配置' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误，无法连接到 API' });
    } finally {
      setIsValidating(false);
    }
  };

  const handleSave = () => {
    onSave(localConfig);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>设置</h2>
          <button className="close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <div className="settings-section">
            <h3>LLM API 配置</h3>
            
            <div className="form-group">
              <label>API Key</label>
              <input
                type="password"
                value={localConfig.apiKey}
                onChange={(e) => setLocalConfig({ ...localConfig, apiKey: e.target.value })}
                placeholder="sk-..."
              />
            </div>

            <div className="form-group">
              <label>Base URL</label>
              <input
                type="text"
                value={localConfig.baseUrl}
                onChange={(e) => setLocalConfig({ ...localConfig, baseUrl: e.target.value })}
                placeholder="https://api.openai.com/v1"
              />
            </div>

            <div className="form-group">
              <label>模型</label>
              <input
                type="text"
                value={localConfig.model}
                onChange={(e) => setLocalConfig({ ...localConfig, model: e.target.value })}
                placeholder="gpt-4"
              />
            </div>

            {message && (
              <div className={`message ${message.type}`}>
                {message.type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}
                <span>{message.text}</span>
              </div>
            )}
          </div>

          <div className="settings-section">
            <h3>预设配置</h3>
            <div className="preset-buttons">
              <button
                className="preset-button"
                onClick={() => setLocalConfig({
                  apiKey: '',
                  baseUrl: 'https://api.moonshot.cn/v1',
                  model: 'kimi-k2-0905-preview',
                })}
              >
                Kimi (Moonshot)
              </button>
              <button
                className="preset-button"
                onClick={() => setLocalConfig({
                  apiKey: '',
                  baseUrl: 'https://api.openai.com/v1',
                  model: 'gpt-4',
                })}
              >
                OpenAI
              </button>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button
            className="button secondary"
            onClick={handleValidate}
            disabled={isValidating}
          >
            {isValidating ? '验证中...' : '验证连接'}
          </button>
          <button
            className="button primary"
            onClick={handleSave}
          >
            保存
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
