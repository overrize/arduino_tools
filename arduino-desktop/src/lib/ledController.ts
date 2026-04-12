import { CPU } from 'avr8js';
import { readPort } from './simulation';

export interface LEDState {
  pin: number;
  isOn: boolean;
  brightness: number; // 0-100
}

export type LEDChangeCallback = (pin: number, state: LEDState) => void;

export class LEDController {
  private cpu: CPU;
  private ledStates: Map<number, LEDState> = new Map();
  private previousPortB: number = 0;
  private previousPortC: number = 0;
  private previousPortD: number = 0;
  private onLEDChange: LEDChangeCallback | null = null;

  constructor(cpu: CPU, onLEDChange?: LEDChangeCallback) {
    this.cpu = cpu;
    if (onLEDChange) {
      this.onLEDChange = onLEDChange;
    }

    // 初始化所有引脚的 LED 状态
    for (let i = 0; i < 20; i++) {
      this.ledStates.set(i, {
        pin: i,
        isOn: false,
        brightness: 0,
      });
    }
  }

  /**
   * 更新 LED 状态，检测 PORT 变化
   * Arduino UNO 的引脚分布：
   * - Digital 0-7: PORTD
   * - Digital 8-13: PORTB
   * - Analog 0-5 (14-19): PORTC
   */
  updateLEDStates(): void {
    // 读取当前端口值
    const portB = readPort(this.cpu, 'B');
    const portC = readPort(this.cpu, 'C');
    const portD = readPort(this.cpu, 'D');

    // 检查 PORTD (引脚 0-7)
    this.checkPortChanges(
      portD,
      this.previousPortD,
      'D',
      0
    );

    // 检查 PORTB (引脚 8-13)
    this.checkPortChanges(
      portB,
      this.previousPortB,
      'B',
      8
    );

    // 检查 PORTC (引脚 14-19，模拟输入也可做数字输出)
    this.checkPortChanges(
      portC,
      this.previousPortC,
      'C',
      14
    );

    // 保存当前状态作为下一次的"前一个状态"
    this.previousPortB = portB;
    this.previousPortC = portC;
    this.previousPortD = portD;
  }

  /**
   * 检查端口中的位变化
   */
  private checkPortChanges(
    currentPort: number,
    previousPort: number,
    _portName: 'B' | 'C' | 'D',
    startPin: number
  ): void {
    for (let i = 0; i < 8; i++) {
      const pin = startPin + i;
      if (pin >= 20) break; // Arduino UNO 只有 20 个引脚

      const currentBit = (currentPort >> i) & 1;
      const previousBit = (previousPort >> i) & 1;

      // 仅在位变化时更新
      if (currentBit !== previousBit) {
        const isOn = currentBit === 1;
        this.updateLEDState(pin, isOn);
      }
    }
  }

  /**
   * 更新单个 LED 的状态
   */
  private updateLEDState(pin: number, isOn: boolean): void {
    const state: LEDState = {
      pin,
      isOn,
      brightness: isOn ? 100 : 20, // 亮时 100%，灭时 20% 残余光
    };

    this.ledStates.set(pin, state);

    if (this.onLEDChange) {
      this.onLEDChange(pin, state);
    }
  }

  /**
   * 获取所有 LED 状态
   */
  getAll(): LEDState[] {
    return Array.from(this.ledStates.values());
  }

  /**
   * 获取特定引脚的 LED 状态
   */
  getPin(pin: number): LEDState | undefined {
    return this.ledStates.get(pin);
  }

  /**
   * 注册 LED 状态变化回调
   */
  setOnLEDChange(callback: LEDChangeCallback): void {
    this.onLEDChange = callback;
  }
}
