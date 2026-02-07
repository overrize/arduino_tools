#!/usr/bin/env python3
"""Arduino 开发 CLI 工具 - 自然语言版本"""

import sys
import subprocess
import os
from pathlib import Path


def show_welcome():
    """显示欢迎界面"""
    print("\n" + "="*60)
    print("🎯 Arduino 开发助手")
    print("="*60)
    print("\n欢迎使用 Arduino 自然语言开发工具！\n")


def show_examples():
    """显示示例"""
    print("💡 示例：")
    print("  • 用 Pico 做一个 LED 闪烁，25 号引脚")
    print("  • 用 Uno 做一个 LED 闪烁，13 号引脚，每 2 秒闪一次")
    print("  • 用 Nano 做一个按钮控制 LED")
    print("  • 用 ESP32 读取传感器数据\n")


def open_kiro_with_prompt(user_input, workspace=None):
    """打开 Kiro 并传递用户需求"""
    # 生成完整的提示
    prompt = f"使用 Arduino MCP server 帮我{user_input}"
    
    print(f"\n✅ 理解了你的需求！")
    print(f"⏳ 正在启动 Kiro...\n")
    
    try:
        # 使用 kiro . 命令打开当前文件夹
        # 这是 PowerShell 中的标准用法
        subprocess.Popen(
            ["kiro", "."],
            cwd=workspace if workspace else os.getcwd(),
            shell=True
        )
        
        print("✅ Kiro 已启动！\n")
        print("💡 请在 Kiro 中输入：")
        print(f"\n{prompt}\n")
        print("或者直接说：")
        print(f"\n{user_input}\n")
        
        # 尝试复制到剪贴板
        try:
            import pyperclip
            pyperclip.copy(prompt)
            print("✅ 提示已复制到剪贴板，可以直接粘贴（Ctrl+V）\n")
        except:
            # 尝试使用 Windows clip 命令
            try:
                process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=True)
                process.communicate(prompt.encode('utf-8'))
                print("✅ 提示已复制到剪贴板，可以直接粘贴（Ctrl+V）\n")
            except:
                pass
        
        return True
    except Exception as e:
        print(f"❌ 启动 Kiro 失败: {e}")
        print("\n💡 请手动在当前文件夹运行：")
        print(f"   kiro .\n")
        print("然后输入：")
        print(f"\n{prompt}\n")
        return False


def main():
    """主入口"""
    show_welcome()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 从命令行参数获取输入
        user_input = " ".join(sys.argv[1:])
    else:
        # 交互式输入
        show_examples()
        print("请描述你想做什么（或输入 'help' 查看更多示例）：")
        user_input = input("> ").strip()
        
        if not user_input or user_input.lower() in ['help', '帮助', 'h', '?']:
            show_examples()
            print("\n更多功能即将推出...\n")
            return
    
    # 打开 Kiro 并传递需求
    workspace = str(Path.cwd())
    open_kiro_with_prompt(user_input, workspace)
    
    print("💡 提示：")
    print("  Kiro 将自动调用 Arduino MCP Server")
    print("  生成代码、Wokwi 仿真文件，并提供编译上传选项\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见！\n")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}\n")
        import traceback
        traceback.print_exc()
