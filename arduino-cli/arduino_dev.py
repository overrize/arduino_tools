#!/usr/bin/env python3
"""Arduino 开发 CLI 工具 - 主程序"""

import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from ui import Display, Menu, Prompts
from core import ProjectConfig, KiroIntegration, DependencyChecker


def create_new_project():
    """新建项目流程"""
    display = Display()
    menu = Menu()
    prompts = Prompts()
    
    # 1. 选择板型
    board = menu.show_board_menu()
    
    # 2. 选择项目类型
    project_type = menu.show_project_type_menu()
    
    # 3. 收集参数
    pin = prompts.get_pin_number(board)
    interval = prompts.get_interval()
    project_name = prompts.get_project_name()
    
    # 4. 创建配置
    config = ProjectConfig.from_user_input(
        board=board,
        project_type=project_type,
        pin=pin,
        interval=interval,
        name=project_name
    )
    
    # 5. 显示摘要
    display.show_project_summary(config)
    
    # 6. 确认
    if not prompts.confirm("确认创建项目？"):
        display.show_info("已取消")
        return
    
    # 7. 生成命令并打开 Kiro
    display.show_progress("正在生成 Kiro 命令")
    kiro = KiroIntegration()
    
    # 使用当前工作目录作为 workspace
    workspace = str(Path.cwd())
    kiro.open_in_kiro(config, workspace)
    
    display.show_success("完成！")
    display.show_info("请在 Kiro 中粘贴命令（Ctrl+V）")


def compile_project():
    """编译项目"""
    display = Display()
    display.show_info("编译功能即将推出...")
    print("\n💡 提示：你可以在 Kiro 中使用以下命令编译：")
    print("   使用 Arduino MCP server 的 compile_sketch 工具编译 ./arduino_projects/项目名\n")


def upload_project():
    """上传项目"""
    display = Display()
    display.show_info("上传功能即将推出...")
    print("\n💡 提示：你可以在 Kiro 中使用以下命令上传：")
    print("   使用 Arduino MCP server 的 upload_sketch 工具上传 ./arduino_projects/项目名\n")


def monitor_serial():
    """监控串口"""
    display = Display()
    display.show_info("串口监控功能即将推出...")
    print("\n💡 提示：你可以在 Kiro 中使用以下命令监控：")
    print("   使用 Arduino MCP server 的 monitor_serial 工具监控 COM3 端口\n")


def show_help():
    """显示帮助"""
    print("\n" + "="*60)
    print("❓ 帮助")
    print("="*60)
    print("\n🎯 Arduino 开发助手")
    print("\n这是一个友好的命令行工具，帮助你快速开始 Arduino 开发。\n")
    
    print("📋 功能：")
    print("  1. 新建项目 - 通过引导式界面创建 Arduino 项目")
    print("  2. 编译项目 - 编译 Arduino 代码")
    print("  3. 上传项目 - 上传代码到硬件")
    print("  4. 监控串口 - 查看串口输出\n")
    
    print("🚀 快速开始：")
    print("  1. 选择'新建项目'")
    print("  2. 选择你的板型（Pico/Uno/Nano/ESP32）")
    print("  3. 选择项目类型（LED 闪烁等）")
    print("  4. 输入参数（引脚、间隔等）")
    print("  5. 工具会自动生成 Kiro 命令并打开 Kiro")
    print("  6. 在 Kiro 中粘贴命令即可\n")
    
    print("💡 提示：")
    print("  - 所有输入都有默认值，直接回车使用默认值")
    print("  - 命令会自动复制到剪贴板")
    print("  - 如果 Kiro 未自动打开，请手动打开并粘贴命令\n")
    
    print("📚 更多信息：")
    print("  - Arduino MCP Server 文档")
    print("  - Wokwi 仿真教程")
    print("  - 故障排查指南\n")
    
    print("="*60 + "\n")


def main():
    """主入口"""
    display = Display()
    menu = Menu()
    checker = DependencyChecker()
    
    # 显示欢迎界面
    display.welcome()
    
    # 检查依赖（不阻塞）
    checker.check_all(verbose=False)
    
    # 主循环
    while True:
        try:
            choice = menu.show_main_menu()
            
            if choice == 1:
                create_new_project()
            elif choice == 2:
                compile_project()
            elif choice == 3:
                upload_project()
            elif choice == 4:
                monitor_serial()
            elif choice == 5:
                show_help()
            elif choice == 0:
                print("\n👋 再见！\n")
                break
        
        except KeyboardInterrupt:
            print("\n\n👋 再见！\n")
            break
        except Exception as e:
            display.show_error(f"发生错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
