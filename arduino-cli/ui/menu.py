"""菜单系统"""


class Menu:
    """菜单类 - 负责显示菜单和获取用户选择"""
    
    def show_main_menu(self) -> int:
        """显示主菜单"""
        print("\n" + "="*60)
        print("📋 主菜单")
        print("="*60)
        print("\n请选择操作：")
        print("  1. 🆕 新建项目")
        print("  2. 🔨 编译项目")
        print("  3. 📤 上传到硬件")
        print("  4. 📡 监控串口")
        print("  5. ❓ 帮助")
        print("  0. 退出")
        
        return self.get_choice(0, 5)
    
    def show_board_menu(self) -> str:
        """选择板型"""
        print("\n" + "-"*60)
        print("📌 选择板型")
        print("-"*60)
        print("  1. Raspberry Pi Pico")
        print("  2. Arduino Uno")
        print("  3. Arduino Nano")
        print("  4. ESP32")
        
        choice = self.get_choice(1, 4)
        boards = {
            1: "pico",
            2: "uno",
            3: "nano",
            4: "esp32"
        }
        return boards[choice]
    
    def show_project_type_menu(self) -> str:
        """选择项目类型"""
        print("\n" + "-"*60)
        print("📦 选择项目类型")
        print("-"*60)
        print("  1. LED 闪烁")
        print("  2. 按钮控制 LED")
        print("  3. 传感器读取")
        print("  4. 自定义")
        
        choice = self.get_choice(1, 4)
        types = {
            1: "led_blink",
            2: "button_led",
            3: "sensor",
            4: "custom"
        }
        return types[choice]
    
    def get_choice(self, min_val: int, max_val: int) -> int:
        """获取用户选择"""
        while True:
            try:
                choice = input(f"\n请输入选项 [{min_val}-{max_val}]: ").strip()
                choice_num = int(choice)
                if min_val <= choice_num <= max_val:
                    return choice_num
                print(f"❌ 请输入 {min_val} 到 {max_val} 之间的数字")
            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                exit(0)
