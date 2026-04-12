/**
 * UART 控制器 - 捕获虚拟 Serial 输出
 * 监听 UDR0 寄存器 (0xC6) 变化，收集输出数据
 */

export type UARTOutputCallback = (line: string) => void;

export class UARTController {
  private cpu: any;
  private outputBuffer: string = '';
  private onOutput: UARTOutputCallback | null = null;
  private previousUDR: number = 0;
  private maxBufferSize: number = 10240; // 10KB 最大缓冲
  private lineCount: number = 0;

  constructor(cpu: any, onOutput?: UARTOutputCallback) {
    this.cpu = cpu;
    if (onOutput) {
      this.onOutput = onOutput;
    }
  }

  /**
   * 每帧调用，检查 UDR0 寄存器变化
   * UDR0 地址：0xC6（AVR UNO）
   */
  updateUART(): void {
    if (!this.cpu || !this.cpu.data) return;

    // 读取 UDR0 (Data Register)
    const udr = this.cpu.data[0xC6] || 0;

    // 检查是否有新数据（值变化）
    if (udr !== this.previousUDR && udr !== 0) {
      const char = String.fromCharCode(udr);
      this.outputBuffer += char;

      // 缓冲溢出保护
      if (this.outputBuffer.length > this.maxBufferSize) {
        this.flushBuffer(true);
      }

      // 遇到换行符时触发输出
      if (char === '\n') {
        this.flushBuffer(false);
      }

      this.previousUDR = udr;
    }
  }

  /**
   * 刷新输出缓冲
   */
  private flushBuffer(overflow: boolean): void {
    if (this.outputBuffer.length === 0) return;

    const line = this.outputBuffer
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .trim();

    if (line && this.onOutput) {
      this.onOutput(overflow ? line + ' [OVERFLOW]' : line);
    }

    this.lineCount++;
    this.outputBuffer = '';
  }

  /**
   * 获取已输出的行数
   */
  getLineCount(): number {
    return this.lineCount;
  }

  /**
   * 重置计数
   */
  reset(): void {
    this.outputBuffer = '';
    this.previousUDR = 0;
    this.lineCount = 0;
  }

  /**
   * 设置输出回调
   */
  setOnOutput(callback: UARTOutputCallback): void {
    this.onOutput = callback;
  }
}
