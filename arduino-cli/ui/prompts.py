"""用户输入提示和收集"""


class Prompts:
    """输入提示类 - 负责收集用户输入"""
    
    def get_pin_number(self, board: str) -> int:
        """获取引脚号"""
        # 根据板型设置默认引脚
        defaults = {
            "pico": 25,
            "uno": 13,
            "nano": 13,
            "esp32": 2
        }
        default = defaults.get(board, 13)
        
        print("\n" + "-"*60)
        print("📍 配置引脚")
        print("-"*60)
        
        while True:
            pin = input(f"LED 引脚号 [默认: {default}]: ").strip()
            if not pin:
                return default
            try:
                pin_num = int(pin)
                if 0 <= pin_num <= 40:
                    return pin_num
                print("❌ 引脚号必须在 0-40 之间")
            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                exit(0)
    
    def get_interval(self, default: int = 1) -> int:
        """获取闪烁间隔"""
        print("\n" + "-"*60)
        print("⏱️  配置间隔")
        print("-"*60)
        
        while True:
            interval = input(f"闪烁间隔（秒）[默认: {default}]: ").strip()
            if not interval:
                return default
            try:
                interval_num = int(interval)
                if interval_num > 0:
                    return interval_num
                print("❌ 间隔必须大于 0")
            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                exit(0)
    
    def get_project_name(self, default: str = "my_arduino_project") -> str:
        """获取项目名称"""
        print("\n" + "-"*60)
        print("📁 配置项目名称")
        print("-"*60)
        
        name = input(f"项目名称 [默认: {default}]: ").strip()
        return name if name else default
    
    def confirm(self, message: str) -> bool:
        """确认操作"""
        while True:
            response = input(f"\n{message} (y/n): ").strip().lower()
            if response in ['y', 'yes', '是']:
                return True
            elif response in ['n', 'no', '否']:
                return False
            print("❌ 请输入 y 或 n")
