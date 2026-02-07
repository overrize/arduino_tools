"""显示和格式化模块"""


class Display:
    """显示类 - 负责所有输出格式化"""
    
    def welcome(self):
        """欢迎界面"""
        print("\n" + "="*60)
        print("🎯 Arduino 开发助手")
        print("="*60)
        print("\n欢迎使用 Arduino 自然语言开发工具！")
        print("从想法到硬件，只需几步。\n")
    
    def show_project_summary(self, config):
        """显示项目摘要"""
        print("\n" + "="*60)
        print("✅ 配置完成")
        print("="*60)
        print("\n项目信息：")
        print(f"  📌 板型: {config.get_board_name()}")
        print(f"  📦 类型: {config.get_project_type_name()}")
        print(f"  📍 引脚: {config.pin}")
        print(f"  ⏱️  间隔: {config.interval} 秒")
        print(f"  📁 名称: {config.project_name}")
        print()
    
    def show_progress(self, message: str):
        """显示进度"""
        print(f"⏳ {message}...")
    
    def show_success(self, message: str):
        """显示成功"""
        print(f"✅ {message}")
    
    def show_error(self, message: str):
        """显示错误"""
        print(f"❌ {message}")
    
    def show_info(self, message: str):
        """显示信息"""
        print(f"💡 {message}")
    
    def show_command(self, command: str):
        """显示生成的命令"""
        print("\n" + "="*60)
        print("📋 生成的 Kiro 命令")
        print("="*60)
        print(f"\n{command}\n")
        print("="*60)
