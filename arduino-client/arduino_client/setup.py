"""交互式配置向导"""
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.panel import Panel
    from rich.align import Align
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def setup_config(work_dir: Optional[Path] = None) -> bool:
    """交互式配置向导

    Args:
        work_dir: 工作目录，None 时使用当前目录

    Returns:
        是否成功配置
    """
    if not RICH_AVAILABLE:
        return _setup_plain(work_dir)

    try:
        from .ui.console import get_console
        console = get_console()
    except Exception:
        from rich.console import Console
        console = Console()

    # 欢迎面板 — 对标 STLoop chat_rich._setup_instructions
    console.print(
        Panel(
            Align.center(
                Text.assemble(
                    ("Welcome to ", "dim"),
                    ("Arduino Client", "bold cyan"),
                    ("\n", ""),
                    ("Configure your LLM API to start generating firmware", "dim"),
                )
            ),
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # 提供商选择表格
    console.print("\n[dim]Select LLM Provider:[/dim]")

    providers_table = Table(show_header=False, box=None, padding=(0, 2))
    providers_table.add_column(style="cyan")
    providers_table.add_column(style="white")
    providers_table.add_column(style="dim")

    providers_table.add_row("1", "Kimi (Moonshot)", "Recommended for Chinese users")
    providers_table.add_row("2", "OpenAI", "GPT-4, GPT-3.5")
    providers_table.add_row("3", "Custom", "Other OpenAI-compatible API")

    console.print(providers_table)

    choice = Prompt.ask("\n[>] Select", choices=["1", "2", "3"], default="1")

    # 配置参数
    configs = {
        "1": ("Kimi", "https://api.moonshot.cn/v1", "kimi-k2-0905-preview"),
        "2": ("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"),
        "3": ("Custom", "", ""),
    }

    provider_name, default_base, default_model = configs[choice]

    console.print(f"\n[dim]Configure {provider_name}:[/dim]")

    # API Key
    api_key = Prompt.ask("[>] API Key", password=True)
    if not api_key or not api_key.strip():
        console.print("[red][X] API Key is required[/red]")
        return False
    api_key = api_key.strip()

    # Base URL
    if choice == "3":
        base_url = Prompt.ask("[>] API Base URL", default=default_base)
    else:
        base_url = default_base

    # Model
    model = Prompt.ask("[>] Model", default=default_model)

    # 配置摘要
    console.print("\n[dim]Configuration Summary:[/dim]")
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column(style="dim", justify="right")
    summary_table.add_column(style="white")
    summary_table.add_row("Provider:", provider_name)
    summary_table.add_row("API Key:", f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***")
    summary_table.add_row("Base URL:", base_url)
    summary_table.add_row("Model:", model)
    console.print(summary_table)

    # 保存位置
    if work_dir is None:
        work_dir = Path.cwd()
    else:
        work_dir = Path(work_dir)

    env_path = work_dir / ".env"

    # 确认保存
    if not Confirm.ask(f"\n[>] Save to {env_path}?", default=True):
        env_path = Path.home() / ".env"
        console.print(f"[dim]Will save to: {env_path}[/dim]")

    # 写入
    try:
        env_content = f"""# Arduino Client Configuration
OPENAI_API_KEY={api_key}
OPENAI_API_BASE={base_url}
OPENAI_MODEL={model}
"""
        env_path.write_text(env_content, encoding="utf-8")

        # 立即生效
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_API_BASE"] = base_url
        os.environ["OPENAI_MODEL"] = model

        console.print(f"\n[green][OK] Configuration saved to {env_path}[/green]")
        console.print("\n[dim]You can now generate code:[/dim]")
        console.print("  [cyan]arduino-client gen \"LED blink on pin 13\" blink_demo --build --flash[/cyan]")

        return True

    except Exception as e:
        console.print(f"[red][X] Failed to save: {e}[/red]")
        return False


def _setup_plain(work_dir: Optional[Path] = None) -> bool:
    """纯文本版配置向导（Rich 不可用时的 fallback）"""
    print("=" * 60)
    print("Arduino Client Configuration Wizard")
    print("=" * 60)

    print("\nSelect LLM Provider:")
    print("1. Kimi (Moonshot) - Recommended")
    print("2. OpenAI")
    print("3. Custom")

    choice = input("Select [1-3] (default: 1): ").strip() or "1"

    configs = {
        "1": ("Kimi", "https://api.moonshot.cn/v1", "kimi-k2-0905-preview"),
        "2": ("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"),
        "3": ("Custom", "", ""),
    }
    if choice not in configs:
        choice = "1"

    provider_name, default_base, default_model = configs[choice]

    print(f"\nConfigure {provider_name}:")
    api_key = input("API Key: ").strip()
    if not api_key:
        print("Error: API Key is required", file=sys.stderr)
        return False

    if choice == "3":
        base_url = input(f"API Base URL [{default_base}]: ").strip() or default_base
    else:
        base_url = default_base

    model = input(f"Model [{default_model}]: ").strip() or default_model

    if work_dir is None:
        work_dir = Path.cwd()
    else:
        work_dir = Path(work_dir)

    env_path = work_dir / ".env"

    try:
        env_content = f"OPENAI_API_KEY={api_key}\nOPENAI_API_BASE={base_url}\nOPENAI_MODEL={model}\n"
        env_path.write_text(env_content, encoding="utf-8")

        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_API_BASE"] = base_url
        os.environ["OPENAI_MODEL"] = model

        print(f"\nConfiguration saved to {env_path}")
        return True
    except Exception as e:
        print(f"Failed to save: {e}", file=sys.stderr)
        return False
