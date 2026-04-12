import { CPU } from 'avr8js';
import { parseIntelHex } from 'intel-hex';

export interface AVRCore {
  cpu: CPU;
  memory: Uint8Array;
  flash: Uint8Array;
}

/**
 * 解析 Intel HEX 格式并初始化 AVR CPU
 * @param hexData - 原始 HEX 文件内容（字符串）
 * @returns AVR CPU 实例和内存对象
 */
export async function loadHexAndInitAVR(hexData: string): Promise<AVRCore> {
  try {
    // 使用 intel-hex 库解析 HEX 文件
    const parsed = parseIntelHex(hexData);

    // AVR UNO 规格：32KB Flash（指令内存），2KB SRAM
    const flash = new Uint8Array(32768);
    const memory = new Uint8Array(2048);

    // 将解析的 HEX 数据写入 Flash
    Object.entries(parsed).forEach(([addrStr, byte]) => {
      const addr = parseInt(addrStr, 10);
      if (addr < flash.length) {
        flash[addr] = byte as number;
      }
    });

    // 初始化 CPU，传入 Flash 内存
    const cpu = new CPU(new Uint16Array(flash.buffer)) as any;

    return { cpu, memory, flash };
  } catch (error) {
    throw new Error(`Failed to load HEX file: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * 从文件路径加载 HEX 文件
 * @param hexPath - HEX 文件路径
 * @returns AVR CPU 实例
 */
export async function loadHexFromFile(hexPath: string): Promise<AVRCore> {
  try {
    const response = await fetch(hexPath);
    if (!response.ok) {
      throw new Error(`Failed to fetch HEX file: ${response.statusText}`);
    }
    const hexContent = await response.text();
    return loadHexAndInitAVR(hexContent);
  } catch (error) {
    throw new Error(`Failed to load HEX from file: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * 单步执行 AVR CPU（一个机器周期）
 * @param cpu - AVR CPU 实例
 */
export function stepCPU(cpu: any): void {
  if (typeof cpu.step === 'function') {
    cpu.step();
  } else if (typeof cpu.execute === 'function') {
    cpu.execute();
  } else if (typeof cpu.tick === 'function') {
    cpu.tick();
  }
}

/**
 * 批量执行 CPU 步骤
 * @param cpu - AVR CPU 实例
 * @param steps - 要执行的步骤数
 */
export function stepCPUMultiple(cpu: any, steps: number): void {
  for (let i = 0; i < steps; i++) {
    stepCPU(cpu);
  }
}

/**
 * 读取 AVR 端口值（PORTB, PORTC, PORTD 等）
 * Arduino UNO 的数字引脚分布：
 * - Pin 0-7: PORTD
 * - Pin 8-13: PORTB
 * - Pin 14-19: PORTC (模拟引脚)
 */
export function readPort(cpu: CPU, portName: 'B' | 'C' | 'D'): number {
  // avr8js CPU 的寄存器地址
  const portAddresses: Record<string, number> = {
    'B': 0x25, // PORTB
    'C': 0x28, // PORTC
    'D': 0x2B, // PORTD
  };

  const addr = portAddresses[portName];
  return cpu.data[addr] || 0;
}

/**
 * 读取 AVR DDR（数据方向寄存器）
 */
export function readDDR(cpu: CPU, portName: 'B' | 'C' | 'D'): number {
  const ddrAddresses: Record<string, number> = {
    'B': 0x24, // DDRB
    'C': 0x27, // DDRC
    'D': 0x2A, // DDRD
  };

  const addr = ddrAddresses[portName];
  return cpu.data[addr] || 0;
}

/**
 * 模拟按钮按下（写入端口位）
 * @param cpu - AVR CPU 实例
 * @param portName - 端口名 ('B', 'C', 'D')
 * @param pin - 引脚号 (0-7)
 * @param pressed - 是否按下 (true = LOW, false = HIGH)
 */
export function setPinInput(cpu: CPU, portName: 'B' | 'C' | 'D', pin: number, pressed: boolean): void {
  const pinAddresses: Record<string, number> = {
    'B': 0x23, // PINB
    'C': 0x26, // PINC
    'D': 0x29, // PIND
  };

  const addr = pinAddresses[portName];
  const currentValue = cpu.data[addr] || 0;

  if (pressed) {
    // 按下：设置为 0（LOW）
    cpu.data[addr] = currentValue & ~(1 << pin);
  } else {
    // 释放：设置为 1（HIGH）
    cpu.data[addr] = currentValue | (1 << pin);
  }
}
