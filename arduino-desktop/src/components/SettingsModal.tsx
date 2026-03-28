import React, { useState, useEffect } from 'react';
import { X, Check, AlertCircle } from 'lucide-react';
import { invoke } from '@tauri-apps/api/tauri';
import './SettingsModal.css';

interface SettingsModalProps {
  onClose: () => void;
}

interface LLMConfig {
  api_key: string;
  base_url: string;
  model: string;
}

interface WokwiConfig {
  token: string;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  const [config, setConfig] = useState<LLMConfig>({
    api_key: '',
    base_url: 'https://api.moonshot.cn/v1',
    model: 'kimi-k2-0905-preview',
  });
  const [wokwiConfig, setWokwiConfig] = useState<WokwiConfig>({
    token: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadConfig();
    loadWokwiConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const savedConfig = await invoke<LLMConfig>('get_llm_config');
      setConfig(savedConfig);
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const loadWokwiConfig = async () => {
    try {
      const savedConfig = await invoke<WokwiConfig>('get_wokwi_config');
      setWokwiConfig(savedConfig);
    } catch (error) {
      console.error('Failed to load wokwi config:', error);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      await invoke('save_llm_config', { config });
      await invoke('save_wokwi_config', { config: wokwiConfig });
      setMessage({ type: 'success', text: '配置已保存' });
      setTimeout(() => onClose(), 1000);
    } catch (error: any) {
      setMessage({ type: 'error', text: error.toString() });
    } finally {
      setIsLoading(false);
    }
  };

  const handleValidate = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      const isValid = await invoke<boolean>('validate_llm_config', { config });
      if (isValid) {
        setMessage({ type: 'success', text: 'API 连接正常' });
      } else {
        setMessage({ type: 'error', text: 'API 连接失败' });
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: error.toString() });
    } finally {
      setIsLoading(false);
    }
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
                value={config.api_key}
                onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                placeholder="sk-..."
              />
            </div>

            <div className="form-group">
              <label>Base URL</label>
              <input
                type="text"
                value={config.base_url}
                onChange={(e) => setConfig({ ...config, base_url: e.target.value })}
                placeholder="https://api.openai.com/v1"
              />
            </div>

            <div className="form-group">
              <label>模型</label>
              <input
                type="text"
                value={config.model}
                onChange={(e) => setConfig({ ...config, model: e.target.value })}
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
            <h3>Wokwi 仿真配置</h3>
            <div className="form-group">
              <label>WOKWI_CLI_TOKEN</label>
              <input
                type="password"
                value={wokwiConfig.token}
                onChange={(e) => setWokwiConfig({ ...wokwiConfig, token: e.target.value })}
                placeholder="wokwi_..."
              />
              <small style={{ display: 'block', marginTop: '4px', color: '#666' }}>
                用于 Wokwi 仿真，获取地址：
                <a href="https://wokwi.com/dashboard/ci" target="_blank" rel="noopener noreferrer" style={{ color: '#3498db' }}>
                  wokwi.com/dashboard/ci
                </a>
              </small>
            </div>
          </div>

          <div className="settings-section">
            <h3>预设配置</h3>
            <div className="preset-buttons">
              <button
                className="preset-button"
                onClick={() => setConfig({
                  api_key: '',
                  base_url: 'https://api.moonshot.cn/v1',
                  model: 'kimi-k2-0905-preview',
                })}
              >
                Kimi (Moonshot)
              </button>
              <button
                className="preset-button"
                onClick={() => setConfig({
                  api_key: '',
                  base_url: 'https://api.openai.com/v1',
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
            disabled={isLoading}
          >
            验证连接
          </button>
          <button
            className="button primary"
            onClick={handleSave}
            disabled={isLoading}
          >
            {isLoading ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
