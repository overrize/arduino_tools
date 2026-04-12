import { useState } from 'react';
import './VirtualSensor.css';

export interface VirtualSensorProps {
  label: string;
  analogPin: number; // A0-A5 (0-5)
  value: number; // 0-1023
  onChange?: (value: number) => void;
}

/**
 * 虚拟传感器组件
 * 模拟模拟输入，通过滑块调节 0-1023
 * 映射到 Arduino 的 analogRead(A0-A5)
 */
export function VirtualSensor({
  label,
  analogPin,
  value,
  onChange,
}: VirtualSensorProps) {
  const [hovering, setHovering] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = Number(e.target.value);
    onChange?.(newValue);
  };

  // 将 0-1023 映射到百分比
  const percentage = (value / 1023) * 100;

  return (
    <div className="virtual-sensor">
      <div className="sensor-header">
        <label className="sensor-label">{label}</label>
        <span className="sensor-pin">A{analogPin}</span>
      </div>

      <div
        className="sensor-input-wrapper"
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={() => setHovering(false)}
      >
        <input
          type="range"
          min="0"
          max="1023"
          value={value}
          onChange={handleChange}
          className="sensor-slider"
          title={`Analog Pin A${analogPin}`}
        />

        {/* 滑块背景填充 */}
        <div
          className="slider-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="sensor-value">
        {hovering ? `${value} / 1023` : `${value}`}
      </div>
    </div>
  );
}

export default VirtualSensor;
