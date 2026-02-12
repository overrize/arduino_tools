"""交互式配置向导"""
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # 降级到标准输出
    def rprint(*args, **kwargs):
        print(*args)


def setup_config(work_dir: Optional[Path] = None) -> bool:
    """交互式配置向导
    
    Args:
        work_dir: 工作目录，None 时使用当前目录
        
    Returns:
        是否成功配置
    """
    console = Console() if RICH_AVAILABLE else None
    
    if console:
        console.print(Panel.fit(
            "[bold cyan]Arduino Client 配置向导[/bold cyan]\n"
            "让我们来配置 LLM API，以便生成 Arduino 代码",
            border_style="cyan"
        ))
    else:
        print("=" * 60)
        print("Arduino Client 配置向导")
        print("让我们来配置 LLM API，以便生成 Arduino 代码")
        print("=" * 60)
    
    # 选择 API 提供商
    if console:
        console.print("\n[bold]请选择 API 提供商：[/bold]")
        console.print("1. [cyan]Kimi K2[/cyan] (推荐，国内可用)")
        console.print("2. [green]OpenAI[/green]")
        console.print("3. [yellow]其他兼容 OpenAI 格式的 API[/yellow]")
    else:
        print("\n请选择 API 提供商：")
        print("1. Kimi K2 (推荐，国内可用)")
        print("2. OpenAI")
        print("3. 其他兼容 OpenAI 格式的 API")
    
    provider = Prompt.ask("选择", choices=["1", "2", "3"], default="1") if RICH_AVAILABLE else input("选择 [1-3] (默认: 1): ").strip() or "1"
    
    # 收集配置信息
    if provider == "1":
        # Kimi K2
        if console:
            console.print("\n[cyan]配置 Kimi K2 API[/cyan]")
            console.print("获取 API Key: https://platform.moonshot.cn/console/api-keys")
        else:
            print("\n配置 Kimi K2 API")
            print("获取 API Key: https://platform.moonshot.cn/console/api-keys")
        
        api_key = Prompt.ask("请输入 API Key", password=True) if RICH_AVAILABLE else input("请输入 API Key: ").strip()
        base_url = "https://api.moonshot.cn/v1"
        
        if console:
            console.print("\n请选择模型：")
            console.print("1. [cyan]kimi-k2-0905-preview[/cyan] (推荐)")
            console.print("2. [cyan]kimi-k2-turbo-preview[/cyan]")
        else:
            print("\n请选择模型：")
            print("1. kimi-k2-0905-preview (推荐)")
            print("2. kimi-k2-turbo-preview")
        
        model_choice = Prompt.ask("选择模型", choices=["1", "2"], default="1") if RICH_AVAILABLE else input("选择 [1-2] (默认: 1): ").strip() or "1"
        model = "kimi-k2-0905-preview" if model_choice == "1" else "kimi-k2-turbo-preview"
        
    elif provider == "2":
        # OpenAI
        if console:
            console.print("\n[green]配置 OpenAI API[/green]")
            console.print("获取 API Key: https://platform.openai.com/api-keys")
        else:
            print("\n配置 OpenAI API")
            print("获取 API Key: https://platform.openai.com/api-keys")
        
        api_key = Prompt.ask("请输入 API Key", password=True) if RICH_AVAILABLE else input("请输入 API Key: ").strip()
        base_url = None  # OpenAI 使用默认 base_url
        model = Prompt.ask("请输入模型名称", default="gpt-4o-mini") if RICH_AVAILABLE else input("请输入模型名称 (默认: gpt-4o-mini): ").strip() or "gpt-4o-mini"
        
    else:
        # 其他 API
        if console:
            console.print("\n[yellow]配置自定义 API[/yellow]")
        else:
            print("\n配置自定义 API")
        
        api_key = Prompt.ask("请输入 API Key", password=True) if RICH_AVAILABLE else input("请输入 API Key: ").strip()
        base_url = Prompt.ask("请输入 API Base URL") if RICH_AVAILABLE else input("请输入 API Base URL: ").strip()
        model = Prompt.ask("请输入模型名称") if RICH_AVAILABLE else input("请输入模型名称: ").strip()
    
    if not api_key:
        if console:
            console.print("[red]错误：API Key 不能为空[/red]")
        else:
            print("错误：API Key 不能为空", file=sys.stderr)
        return False
    
    # 确定保存位置
    if work_dir is None:
        work_dir = Path.cwd()
    else:
        work_dir = Path(work_dir)
    
    env_path = work_dir / ".env"
    
    # 询问保存位置
    if console:
        console.print(f"\n配置将保存到: [cyan]{env_path}[/cyan]")
        save_here = Confirm.ask("保存到当前目录？", default=True)
    else:
        print(f"\n配置将保存到: {env_path}")
        save_here = input("保存到当前目录？[Y/n]: ").strip().lower() != "n"
    
    if not save_here:
        # 保存到用户主目录
        env_path = Path.home() / ".env"
        if console:
            console.print(f"将保存到: [cyan]{env_path}[/cyan]")
        else:
            print(f"将保存到: {env_path}")
    
    # 写入配置
    try:
        env_content = []
        env_content.append(f"OPENAI_API_KEY={api_key}")
        if base_url:
            env_content.append(f"OPENAI_API_BASE={base_url}")
        if model:
            env_content.append(f"OPENAI_MODEL={model}")
        
        env_path.write_text("\n".join(env_content) + "\n", encoding="utf-8")
        
        if console:
            console.print(f"\n[green]✓ 配置已保存到 {env_path}[/green]")
            console.print("\n[bold]配置完成！[/bold] 现在可以使用 arduino-client 生成代码了。")
            console.print("\n示例命令：")
            console.print("  [cyan]arduino-client gen \"LED 闪烁\" blink_demo --build --flash[/cyan]")
        else:
            print(f"\n✓ 配置已保存到 {env_path}")
            print("\n配置完成！现在可以使用 arduino-client 生成代码了。")
            print("\n示例命令：")
            print("  arduino-client gen \"LED 闪烁\" blink_demo --build --flash")
        
        return True
        
    except Exception as e:
        if console:
            console.print(f"[red]保存配置失败: {e}[/red]")
        else:
            print(f"保存配置失败: {e}", file=sys.stderr)
        return False
