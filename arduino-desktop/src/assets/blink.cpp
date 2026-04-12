// Blink - 最简单的 Arduino 程序
// LED 连接到引脚 13，每秒闪烁一次

void setup() {
  // 将引脚 13 设置为输出模式
  pinMode(13, OUTPUT);
}

void loop() {
  // 点亮 LED
  digitalWrite(13, HIGH);
  delay(1000);

  // 熄灭 LED
  digitalWrite(13, LOW);
  delay(1000);
}
