#!/usr/bin/env python3
"""Arduino 开发 CLI 工具 - BootLoop 风格版本"""

import sys
import subprocess
import os
import time
import itertools
from pathlib import Path


# ASCII 艺术标题
ASCII_LOGO = r"""
 —————————————————————————————————————————————————————————————————————————————————————————————————————————
|  █████╗ ██████╗ ██████╗ ██╗   ██╗██╗███╗   ██╗ ██████╗      █████╗  ██████╗ ███████╗███╗   ██╗████████╗ |   
| ██╔══██╗██╔══██╗██╔══██╗██║   ██║██║████╗  ██║██╔═══██╗    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝ |  
| ███████║██████╔╝██║  ██║██║   ██║██║██╔██╗ ██║██║   ██║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║    |  
| ██╔══██║██╔══██╗██║  ██║██║   ██║██║██║╚██╗██║██║   ██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║    |  
| ██║  ██║██║  ██║██████╔╝╚██████╔╝██║██║ ╚████║╚██████╔╝    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║    |  
| ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝    |
 —————————————————————————————————————————————————————————————————————————————————————————————————————————    
 Welcome to the Arduino Agent!  
 Ctrl + C to exit. Type / for commands.                                                                                                                                                                               
"""

# 颜色代码
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'


def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_colored(text, color=Colors.ENDC):
    """打印彩色文本"""
    print(f"{color}{text}{Colors.ENDC}")


def print_logo():
    """打印 ASCII 标题"""
    print_colored(ASCII_LOGO, Colors.CYAN)


def thinking_animation(duration=2):
    """思考动画"""
    spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    end_time = time.time() + duration
    
    while time.time() < end_time:
        sys.stdout.write(f'\r{Colors.CYAN}⚡ Thinking... {next(spinner)}{Colors.ENDC}')
        sys.stdout.flush()
        time.sleep(0.1)
    
    sys.stdout.write('\r' + ' ' * 50 + '\r')
    sys.stdout.flush()


def typing_effect(text, delay=0.03):
    """打字机效果"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def show_welcome():
    """显示欢迎界面"""
    clear_screen()
    print_logo()


def show_prompt():
    """显示提示符"""
    print_colored("\n▶ ", Colors.GREEN, end='')


def parse_command(user_input):
    """解析命令"""
    if user_input.startswith('/'):
        cmd = user_input[1:].lower().strip()
        
        if cmd in ['help', 'h', '?']:
            # 显示示例
            examples = [
                "用 Pico 做一个 LED 闪烁，25 号引脚",
                "用 Uno 做一个 LED 闪烁，13 号引脚，每 2 秒闪一次",
                "用 Nano 做一个按钮控制 LED",
                "用 ESP32 读取传感器数据"
            ]
            
            print_colored("\n💡 Examples:", Colors.YELLOW)
            for i, example in enumerate(examples, 1):
                print_colored(f"  {i}. {example}", Colors.DIM)
            
            print_colored("\n💡 Commands:", Colors.YELLOW)
            print_colored("  /help    - Show examples", Colors.DIM)
            print_colored("  /clear   - Clear screen", Colors.DIM)
            print_colored("  /exit    - Exit program", Colors.DIM)
            
            return 'help'
        elif cmd in ['exit', 'quit', 'q']:
            return 'exit'
        elif cmd in ['clear', 'cls', 'c']:
            clear_screen()
            print_logo()
            return 'clear'
        else:
            print_colored(f"❌ Unknown command: /{cmd}", Colors.RED)
            print_colored("   Try /help for available commands", Colors.DIM)
            return 'unknown'
    
    return 'input'


def process_request(user_input):
    """处理用户请求"""
    # 显示思考动画
    thinking_animation(1.5)
    
    # 解析意图
    print_colored("✓ Understanding your request...", Colors.GREEN)
    time.sleep(0.5)
    
    # 生成提示
    prompt = f"使用 Arduino MCP server 帮我{user_input}"
    
    print_colored("✓ Generating Arduino project...", Colors.GREEN)
    time.sleep(0.5)
    
    print_colored("✓ Ready to launch Kiro!", Colors.GREEN)
    time.sleep(0.3)
    
    return prompt


def open_kiro_with_prompt(user_input, workspace=None):
    """打开 Kiro 并传递用户需求"""
    prompt = process_request(user_input)
    
    print_colored("\n" + "─" * 60, Colors.DIM)
    print_colored("\n🚀 Launching Kiro...\n", Colors.CYAN)
    
    try:
        # 启动 Kiro
        subprocess.Popen(
            ["kiro", "."],
            cwd=workspace if workspace else os.getcwd(),
            shell=True
        )
        
        time.sleep(1)
        print_colored("✓ Kiro launched successfully!\n", Colors.GREEN)
        
        # 显示提示信息
        print_colored("📋 Please paste this in Kiro:\n", Colors.YELLOW)
        print_colored(f"   {prompt}\n", Colors.BOLD)
        
        # 尝试复制到剪贴板
        try:
            import pyperclip
            pyperclip.copy(prompt)
            print_colored("✓ Prompt copied to clipboard (Ctrl+V to paste)\n", Colors.GREEN)
        except:
            try:
                process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=True)
                process.communicate(prompt.encode('utf-8'))
                print_colored("✓ Prompt copied to clipboard (Ctrl+V to paste)\n", Colors.GREEN)
            except:
                pass
        
        print_colored("─" * 60, Colors.DIM)
        
        return True
    except Exception as e:
        print_colored(f"\n❌ Failed to launch Kiro: {e}", Colors.RED)
        print_colored("\n💡 Please manually run:", Colors.YELLOW)
        print_colored(f"   kiro .\n", Colors.DIM)
        print_colored("Then paste:", Colors.YELLOW)
        print_colored(f"   {prompt}\n", Colors.DIM)
        return False


def interactive_mode():
    """交互模式"""
    show_welcome()
    
    while True:
        try:
            show_prompt()
            user_input = input().strip()
            
            if not user_input:
                continue
            
            # 解析命令
            cmd_type = parse_command(user_input)
            
            if cmd_type == 'exit':
                print_colored("\n👋 Goodbye!\n", Colors.CYAN)
                break
            elif cmd_type in ['help', 'clear', 'unknown']:
                continue
            elif cmd_type == 'input':
                # 处理用户输入
                workspace = str(Path.cwd())
                open_kiro_with_prompt(user_input, workspace)
                
                # 询问是否继续
                print_colored("\n💡 Continue? (y/n or new request): ", Colors.YELLOW, end='')
                response = input().strip().lower()
                
                if response in ['n', 'no', 'exit', 'quit']:
                    print_colored("\n👋 Goodbye!\n", Colors.CYAN)
                    break
                elif response in ['y', 'yes', '']:
                    continue
                else:
                    # 将响应作为新请求处理
                    user_input = response
                    workspace = str(Path.cwd())
                    open_kiro_with_prompt(user_input, workspace)
        
        except KeyboardInterrupt:
            print_colored("\n\n👋 Goodbye!\n", Colors.CYAN)
            break
        except EOFError:
            print_colored("\n\n👋 Goodbye!\n", Colors.CYAN)
            break


def main():
    """主入口"""
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 非交互模式
        user_input = " ".join(sys.argv[1:])
        
        # 检查是否是命令
        if user_input.startswith('/') or user_input.lower() in ['help', '-h', '--help', '?']:
            show_welcome()
            
            # 显示示例
            examples = [
                "用 Pico 做一个 LED 闪烁，25 号引脚",
                "用 Uno 做一个 LED 闪烁，13 号引脚，每 2 秒闪一次",
                "用 Nano 做一个按钮控制 LED",
                "用 ESP32 读取传感器数据"
            ]
            
            print_colored("\n💡 Examples:", Colors.YELLOW)
            for i, example in enumerate(examples, 1):
                print_colored(f"  {i}. {example}", Colors.DIM)
            
            print_colored("\n💡 Usage:", Colors.YELLOW)
            print_colored("  arduino-dev-v3.py                    # Interactive mode", Colors.DIM)
            print_colored("  arduino-dev-v3.py <your request>     # Direct mode", Colors.DIM)
            print_colored("\n💡 Commands:", Colors.YELLOW)
            print_colored("  /help    - Show examples", Colors.DIM)
            print_colored("  /clear   - Clear screen", Colors.DIM)
            print_colored("  /exit    - Exit program", Colors.DIM)
            print()
            return
        
        # 直接处理请求
        show_welcome()
        workspace = str(Path.cwd())
        open_kiro_with_prompt(user_input, workspace)
    else:
        # 交互模式
        interactive_mode()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_colored(f"\n❌ Error: {e}\n", Colors.RED)
        import traceback
        traceback.print_exc()
