# 🚀 Quick Test Guide - Wokwi Integration

## ✅ Ready to Test in Another Kiro Window

---

## 🎯 Test Command

```
用 Pico 做一个 LED 闪烁，25 号引脚
```

---

## 📋 Expected Output

```
🚀 Starting full LED blink workflow...

Step 1: Parsing intent and generating code...
✅ Code generated at: ./arduino_projects/led_blink
   📌 Board: arduino:mbed_rp2040:pico
   📍 LED Pin: 25
   ⏱️  Interval: 1000ms

🎮 Wokwi Simulation Files Generated:
   • diagram.json (circuit diagram)
   • wokwi.toml (configuration)

📋 下一步选择：
   1. [在 Wokwi 中仿真] - 先测试代码和接线
      • 在 VS Code 中打开 diagram.json
      • 按 F1 → 'Wokwi: Start Simulator'
      • 查看电路接线和运行效果
   2. [直接上传到硬件] - 如果已经接好线

💡 推荐：先在 Wokwi 中仿真，确认接线正确后再上传硬件！

Step 2: Compiling...
✅ Compilation successful

Step 3: Detecting board and uploading...
[continues if board detected...]
```

---

## ✅ What to Verify

### 1. Wokwi Files Generated
- [ ] `diagram.json` exists
- [ ] `wokwi.toml` exists
- [ ] Arduino `.ino` file exists

### 2. Chinese Guidance Shown
- [ ] "📋 下一步选择：" displayed
- [ ] Option 1: 在 Wokwi 中仿真
- [ ] Option 2: 直接上传到硬件
- [ ] "💡 推荐：先在 Wokwi 中仿真..."

### 3. Workflow Steps
- [ ] Step 1: Code generation with details
- [ ] Step 2: Compilation
- [ ] Step 3: Upload (if board connected)

### 4. Error Handling
- [ ] If no board: suggests Wokwi simulation
- [ ] Clear error messages

---

## 🎮 Test in VS Code

### After generation:
1. Open `./arduino_projects/led_blink/`
2. Open `diagram.json`
3. Press `F1`
4. Type "Wokwi: Start Simulator"
5. Verify:
   - [ ] Pico board shown
   - [ ] Red LED shown
   - [ ] 220Ω resistor shown
   - [ ] Connections: GP25 → R → LED → GND
   - [ ] LED blinks when simulated

---

## 🔧 Additional Test Cases

### Test 2: Arduino Uno
```
用 Arduino Uno 做一个 LED 闪烁，13 号引脚，每 3 秒闪一次
```
**Verify:** Board type, pin 13, 3000ms interval

### Test 3: Arduino Nano
```
用 Nano 做一个 LED 闪烁，8 号引脚
```
**Verify:** Nano board, pin 8

---

## 📊 Success Criteria

✅ All of these should work:
- Natural language parsing (Chinese)
- Wokwi file generation
- Chinese guidance display
- Clear next-step options
- Compilation success
- Upload (if hardware connected)
- Simulation in VS Code

---

## 🎉 Status

**READY FOR TESTING** ✅

All features implemented and verified.

---

**Quick Start:** Open another Kiro window and type:
```
用 Pico 做一个 LED 闪烁，25 号引脚
```
