import './LED.css';

export interface LEDProps {
  pin: number;
  isOn: boolean;
  color?: string;
  brightness?: number;
  label?: string;
}

/**
 * 虚拟 LED 组件 - 模拟 Arduino 上的 LED 灯
 * @param pin - Arduino 引脚号 (0-19)
 * @param isOn - LED 是否亮起
 * @param color - LED 颜色 (默认 'red')
 * @param brightness - 亮度 0-100 (默认 100)
 * @param label - LED 标签 (默认显示引脚号)
 */
export function LED({
  pin,
  isOn,
  color = 'red',
  brightness = 100,
  label,
}: LEDProps) {
  const displayLabel = label || `Pin ${pin}`;

  // 计算实际亮度
  const actualBrightness = isOn ? brightness : Math.max(brightness * 0.2, 10);

  // 将颜色转换为 RGB 便于透明度处理
  const colorMap: Record<string, string> = {
    'red': '#ff0000',
    'green': '#00ff00',
    'blue': '#0000ff',
    'yellow': '#ffff00',
    'orange': '#ff8800',
    'purple': '#ff00ff',
  };

  const rgbColor = colorMap[color] || color;

  return (
    <div className="led-container">
      <div
        className="led-bulb"
        style={{
          backgroundColor: rgbColor,
          opacity: actualBrightness / 100,
          boxShadow: isOn
            ? `0 0 10px ${rgbColor}, 0 0 20px ${rgbColor}80`
            : `0 0 2px ${rgbColor}40`,
        }}
      />
      <div className="led-label">{displayLabel}</div>
    </div>
  );
}
