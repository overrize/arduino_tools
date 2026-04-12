import { useState } from 'react';
import './VirtualButton.css';

export interface VirtualButtonProps {
  label: string;
  pin: number;
  port: 'B' | 'C' | 'D';
  onPress?: () => void;
  onRelease?: () => void;
}

/**
 * 虚拟按钮组件
 * 模拟按下时 GPIO 引脚被拉低（LOW = 0），释放时拉高（HIGH = 1）
 */
export function VirtualButton({
  label,
  pin,
  port,
  onPress,
  onRelease,
}: VirtualButtonProps) {
  const [isPressed, setIsPressed] = useState(false);

  const handleMouseDown = () => {
    setIsPressed(true);
    onPress?.();
  };

  const handleMouseUp = () => {
    setIsPressed(false);
    onRelease?.();
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    e.preventDefault();
    handleMouseDown();
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    e.preventDefault();
    handleMouseUp();
  };

  return (
    <button
      className={`virtual-button ${isPressed ? 'pressed' : ''}`}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      title={`Button on Pin ${pin} (PORT${port})`}
    >
      <div className="button-label">{label}</div>
      <div className="button-pin">PIN {pin}</div>
    </button>
  );
}

export default VirtualButton;
