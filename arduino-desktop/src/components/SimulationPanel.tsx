import { useState, useEffect, useRef, useCallback } from 'react';
import { loadHexFromFile, stepCPUMultiple, setPinInput } from '../lib/simulation';
import { LEDController, LEDState } from '../lib/ledController';
import { UARTController } from '../lib/uartController';
import { LED } from './LED';
import { VirtualButton } from './VirtualButton';
import { VirtualSensor } from './VirtualSensor';
import './SimulationPanel.css';

export interface SimulationPanelProps {
  hexPath: string;
  boardType?: string;
  onError?: (error: string) => void;
  onSerialOutput?: (output: string) => void;
  onClose?: () => void;  // [新增] 关闭回调
}

/**
 * SimulationPanel - 虚拟仿真面板
 * 加载 .hex 文件，运行 AVR 仿真，渲染虚拟电路元件
 */
export function SimulationPanel({
  hexPath,
  boardType = 'wokwi-arduino-uno',
  onError,
  onSerialOutput,
  onClose,  // [新增]
}: SimulationPanelProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isRunning, setIsRunning] = useState(true);
  const [ledStates, setLedStates] = useState<Map<number, LEDState>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const [fps, setFps] = useState(60);
  const [simulationTime, setSimulationTime] = useState(0);
  // [新增] UART 和传感器状态
  const [uartLines, setUartLines] = useState<string[]>([]);
  const [analogValues, setAnalogValues] = useState<Record<number, number>>({
    0: 512, 1: 512, 2: 512, 3: 512, 4: 512, 5: 512,
  });

  const cpuRef = useRef<any>(null);
  const ledControllerRef = useRef<LEDController | null>(null);
  const uartControllerRef = useRef<UARTController | null>(null);  // [新增]
  const animationFrameRef = useRef<number | null>(null);
  const cpuCyclesRef = useRef<number>(0);
  const fpsCounterRef = useRef<{ count: number; lastTime: number }>({
    count: 0,
    lastTime: Date.now(),
  });

  // 初始化 AVR CPU 和 HEX 加载
  useEffect(() => {
    (async () => {
      try {
        const avrCore = await loadHexFromFile(hexPath);
        cpuRef.current = avrCore.cpu;

        // 初始化 LED 控制器
        const ledController = new LEDController(avrCore.cpu, (pin: number, state: LEDState) => {
          setLedStates(prev => new Map(prev).set(pin, state));
        });
        ledControllerRef.current = ledController;

        // [新增] 初始化 UART 控制器
        const uartController = new UARTController(avrCore.cpu, (line: string) => {
          setUartLines(prev => {
            const updated = [...prev, line];
            // 保留最近 100 行
            return updated.slice(-100);
          });
        });
        uartControllerRef.current = uartController;

        setIsLoaded(true);
        setError(null);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        setError(errorMsg);
        onError?.(errorMsg);
      }
    })();
  }, [hexPath, onError]);

  // 仿真主循环 - requestAnimationFrame
  useEffect(() => {
    if (!isLoaded || !cpuRef.current || !ledControllerRef.current || !uartControllerRef.current) return;

    let running = isRunning;

    const loop = () => {
      if (!running || !cpuRef.current || !ledControllerRef.current || !uartControllerRef.current) {
        animationFrameRef.current = requestAnimationFrame(loop);
        return;
      }

      // 每帧执行 CPU 周期（模拟 16MHz, 约每帧 16000 周期 @ 60fps）
      // 16MHz / 60fps ≈ 266,666 周期/帧，取整为 ~260,000
      const CYCLES_PER_FRAME = 266666;
      stepCPUMultiple(cpuRef.current, CYCLES_PER_FRAME);
      cpuCyclesRef.current += CYCLES_PER_FRAME;

      // 更新 LED 状态
      ledControllerRef.current.updateLEDStates();
      setLedStates(new Map(ledControllerRef.current.getAll().map(s => [s.pin, s])));

      // [新增] 更新 UART 输出
      uartControllerRef.current.updateUART();

      // 更新仿真时间（毫秒）
      const elapsedMs = Math.floor(cpuCyclesRef.current / 16000);
      setSimulationTime(elapsedMs);

      // 更新 FPS
      const now = Date.now();
      fpsCounterRef.current.count++;
      if (now - fpsCounterRef.current.lastTime >= 1000) {
        setFps(fpsCounterRef.current.count);
        fpsCounterRef.current = { count: 0, lastTime: now };
      }

      animationFrameRef.current = requestAnimationFrame(loop);
    };

    animationFrameRef.current = requestAnimationFrame(loop);

    return () => {
      running = false;
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isLoaded, isRunning]);

  // 监听仿真运行状态变化
  useEffect(() => {
    // 这里可以添加其他副作用，比如发送串口输出
  }, [onSerialOutput]);

  const toggleRunning = useCallback(() => {
    setIsRunning(prev => !prev);
  }, []);

  const resetSimulation = useCallback(() => {
    if (cpuRef.current && ledControllerRef.current) {
      // 重新加载 HEX（简单实现）
      (async () => {
        try {
          const avrCore = await loadHexFromFile(hexPath);
          cpuRef.current = avrCore.cpu;
          const ledController = new LEDController(avrCore.cpu, (pin: number, state: LEDState) => {
            setLedStates(prev => new Map(prev).set(pin, state));
          });
          ledControllerRef.current = ledController;

          // [新增] 重置 UART
          const uartController = new UARTController(avrCore.cpu, (line: string) => {
            setUartLines(prev => {
              const updated = [...prev, line];
              return updated.slice(-100);
            });
          });
          uartControllerRef.current = uartController;
          setUartLines([]);

          cpuCyclesRef.current = 0;
          setSimulationTime(0);
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : String(err);
          setError(errorMsg);
        }
      })();
    }
  }, [hexPath]);

  if (error) {
    return (
      <div className="simulation-panel error">
        <div className="error-message">
          <strong>仿真加载失败</strong>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="simulation-panel loading">
        <div className="spinner"></div>
        <p>加载 HEX 文件...</p>
      </div>
    );
  }

  // 获取活跃的 LED（当前被使用的引脚）
  const activeLeds = Array.from(ledStates.values())
    .filter(state => {
      // 显示数字引脚 0-13 (UNO)
      return state.pin <= 13;
    })
    .sort((a, b) => a.pin - b.pin);

  return (
    <div className="simulation-panel">
      <div className="simulation-header">
        <div className="simulation-title">
          <h3>🔌 虚拟仿真 - {boardType}</h3>
          <p className="board-info">Arduino UNO 仿真器</p>
        </div>

        <div className="simulation-controls">
          <button
            className={`btn ${isRunning ? 'btn-pause' : 'btn-play'}`}
            onClick={toggleRunning}
            title={isRunning ? '暂停' : '继续'}
          >
            {isRunning ? '⏸ 暂停' : '▶ 继续'}
          </button>
          <button className="btn btn-reset" onClick={resetSimulation} title="重置仿真">
            🔄 重置
          </button>
          {/* [新增] 关闭按钮 */}
          {onClose && (
            <button
              className="btn btn-close"
              onClick={onClose}
              title="返回编辑"
            >
              ← 返回
            </button>
          )}
        </div>

        <div className="simulation-stats">
          <div className="stat">
            <span className="stat-label">运行时间</span>
            <span className="stat-value">{(simulationTime / 1000).toFixed(2)}s</span>
          </div>
          <div className="stat">
            <span className="stat-label">FPS</span>
            <span className="stat-value">{fps}</span>
          </div>
        </div>
      </div>

      <div className="simulation-content">
        <div className="leds-section">
          <h4>📊 LED 指示灯</h4>
          <div className="leds-grid">
            {activeLeds.length > 0 ? (
              activeLeds.map(state => (
                <LED
                  key={state.pin}
                  pin={state.pin}
                  isOn={state.isOn}
                  brightness={state.brightness}
                  color={state.pin === 13 ? 'orange' : 'red'}
                />
              ))
            ) : (
              <p className="no-leds">检测到 {ledStates.size} 个引脚，尚未输出信号</p>
            )}
          </div>
        </div>

        <div className="interaction-section">
          <div className="buttons-section">
            <h4>🔘 虚拟按钮</h4>
            <div className="buttons-grid">
              <VirtualButton
                label="Button 1"
                pin={2}
                port="D"
                onPress={() => {
                  if (cpuRef.current) setPinInput(cpuRef.current, 'D', 2, true);
                }}
                onRelease={() => {
                  if (cpuRef.current) setPinInput(cpuRef.current, 'D', 2, false);
                }}
              />
              <VirtualButton
                label="Button 2"
                pin={3}
                port="D"
                onPress={() => {
                  if (cpuRef.current) setPinInput(cpuRef.current, 'D', 3, true);
                }}
                onRelease={() => {
                  if (cpuRef.current) setPinInput(cpuRef.current, 'D', 3, false);
                }}
              />
            </div>
          </div>

          <div className="sensors-section">
            <h4>📊 虚拟传感器</h4>
            <div className="sensors-grid">
              {[0, 1, 2].map(pin => (
                <VirtualSensor
                  key={pin}
                  label={`Sensor ${pin + 1}`}
                  analogPin={pin}
                  value={analogValues[pin]}
                  onChange={(val) => {
                    if (cpuRef.current) {
                      // 更新 ADC 寄存器（简化实现）
                      cpuRef.current.data[0x79] = (val >> 8) & 0x03;
                      cpuRef.current.data[0x78] = val & 0xFF;
                      setAnalogValues(prev => ({ ...prev, [pin]: val }));
                    }
                  }}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="serial-section">
          <h4>🖥 串口监视器</h4>
          <div className="serial-monitor">
            {uartLines.length > 0 ? (
              uartLines.map((line, idx) => (
                <div key={idx} className="serial-line">
                  {line}
                </div>
              ))
            ) : (
              <p className="serial-placeholder">（等待串口输出...）</p>
            )}
          </div>
        </div>
      </div>

      <div className="simulation-footer">
        <p>Board: {boardType} | CPU Cycles: {cpuCyclesRef.current.toLocaleString()}</p>
      </div>
    </div>
  );
}

export default SimulationPanel;
