# 🔌 Arduino 虚拟仿真模块

本模块实现了基于 **avr8js** 的 Arduino 虚拟仿真功能，支持在 Tauri 应用内实时运行和显示 AVR 程序的仿真结果。

## 架构概览

```
编译生成 .hex
    ↓
加载 HEX 文件
    ↓
avr8js CPU 执行 AVR 指令
    ↓
监听 GPIO 端口变化
    ↓
LEDController 更新 LED 状态
    ↓
React 组件渲染虚拟元件
```

## 核心模块

### 1. `src/lib/simulation.ts`
AVR CPU 初始化和执行引擎

**主要函数**：
- `loadHexAndInitAVR(hexData)` - 解析 HEX 文件并初始化 CPU
- `loadHexFromFile(hexPath)` - 从文件加载 HEX
- `stepCPU(cpu)` - 单步执行
- `stepCPUMultiple(cpu, steps)` - 批量执行
- `readPort(cpu, portName)` - 读取 GPIO 端口（B/C/D）
- `setPinInput(cpu, port, pin, pressed)` - 模拟按钮输入

**类型**：
```typescript
interface AVRCore {
  cpu: CPU;
  memory: Uint8Array;
  flash: Uint8Array;
}
```

### 2. `src/lib/ledController.ts`
GPIO 监听和 LED 状态管理

**主要类**：
```typescript
class LEDController {
  constructor(cpu: CPU, onLEDChange?: LEDChangeCallback);
  updateLEDStates(): void;      // 轮询 GPIO 并更新状态
  getAll(): LEDState[];          // 获取所有 LED 状态
  getPin(pin: number): LEDState; // 获取特定引脚状态
}
```

**LED 状态接口**：
```typescript
interface LEDState {
  pin: number;      // Arduino 引脚号 (0-19)
  isOn: boolean;    // 是否亮起
  brightness: number; // 亮度 0-100
}
```

### 3. `src/components/SimulationPanel.tsx`
主仿真面板 React 组件

**Props**：
```typescript
interface SimulationPanelProps {
  hexPath: string;              // .hex 文件路径
  boardType?: string;           // 板卡型号 (默认 'wokwi-arduino-uno')
  onError?: (error: string) => void;
  onSerialOutput?: (output: string) => void;
}
```

**特性**：
- ⏸️ 暂停/继续仿真
- 🔄 重置仿真
- 📊 实时 LED 显示
- 🖥️ 虚拟串口监视器（预留接口）
- 📈 FPS 和运行时间统计

### 4. `src/components/LED.tsx`
虚拟 LED 灯光组件

**Props**：
```typescript
interface LEDProps {
  pin: number;      // Arduino 引脚号
  isOn: boolean;    // LED 状态
  color?: string;   // 颜色 (red/green/blue/yellow等)
  brightness?: number; // 亮度 0-100
  label?: string;   // 自定义标签
}
```

## 使用示例

### 基础用法

```tsx
import SimulationPanel from './components/SimulationPanel';

export function MyApp() {
  return (
    <SimulationPanel
      hexPath="/path/to/blink.hex"
      boardType="wokwi-arduino-uno"
      onError={(err) => console.error(err)}
    />
  );
}
```

### 与编译流程集成

```tsx
// 编译完成后
const hexPath = '/projects/my-project/build/output.hex';

// 显示仿真面板
setShowSimulation(true);
setSimulationHexPath(hexPath);
```

### 手动控制 CPU

```typescript
import { loadHexFromFile, stepCPUMultiple, readPort } from './lib/simulation';
import { LEDController } from './lib/ledController';

async function customSimulation() {
  const avrCore = await loadHexFromFile('/path/to/blink.hex');
  const ledController = new LEDController(avrCore.cpu);

  // 运行 1 秒的仿真
  for (let i = 0; i < 16000; i++) {
    stepCPUMultiple(avrCore.cpu, 1000);
    ledController.updateLEDStates();

    // 检查 LED 状态
    const leds = ledController.getAll();
    console.log('LED 13:', leds.find(l => l.pin === 13)?.isOn);
  }
}
```

## Arduino 引脚分布

| 引脚范围 | 端口 | 用途 |
|---------|------|------|
| 0-7    | PORTD | 数字输入/输出 |
| 8-13   | PORTB | 数字输入/输出 + PWM |
| 14-19  | PORTC | 模拟输入（也可作数字输出） |

## 性能指标

- **CPU 频率模拟**：16 MHz
- **每帧周期**：~266,666 (@ 60 FPS)
- **GPIO 轮询**：每帧检测变化
- **内存使用**：~34KB (Flash) + 2KB (SRAM)

## 已知限制

1. **UART 仿真**：暂不支持 Serial.println() 捕获（Phase 3 实现）
2. **SPI/I2C**：当前不支持
3. **中断边界**：简化实现，可能与硬件有细微差异
4. **时钟精度**：基于 CPU 周期计数，与实时时间松耦合

## 测试

运行核心功能测试：

```typescript
import { runAllTests } from './lib/simulation.test';

await runAllTests();
// 输出：
// ✓ HEX loaded successfully
// ✓ CPU executed 1000 cycles
// ✓ GPIO read successful
```

## 常见问题

**Q: LED 不闪烁？**
A: 确认：
1. .hex 文件路径正确
2. blink 程序逻辑无误
3. 延迟时间足够长（delay() 值）

**Q: 性能不足？**
A: 尝试：
1. 降低 FPS（减少每帧周期）
2. 使用 requestIdleCallback 而非 requestAnimationFrame
3. 缓存 LED 变化而非每帧重新计算

**Q: 如何添加更多元件（按钮、传感器）？**
A: 在 SimulationPanel 中：
1. 添加虚拟元件 React 组件
2. 监听用户交互（onClick、onChange）
3. 调用 `setPinInput()` 设置 GPIO 输入
4. 在循环中更新状态

## 依赖

- `avr8js` ^0.21.0 - AVR 指令集模拟器
- `@wokwi/elements` ^1.9.2 - 虚拟元件库（可选，当前未使用）
- `intel-hex` ^0.2.0 - HEX 文件解析

## 路线图

- [x] Phase 1：基础 LED 仿真
- [ ] Phase 2：编译→仿真自动流程
- [ ] Phase 3：UART 串口输出捕获
- [ ] Phase 4：虚拟按钮和传感器交互
- [ ] Phase 5：性能优化和多板卡支持
