"""
进度组件 - 进度条、步骤指示器、Spinner
"""

from typing import Optional, List
from contextlib import contextmanager

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
)
from rich.tree import Tree
from rich.panel import Panel

from ..console import get_console


def create_progress(
    console: Console = None,
    transient: bool = False,
) -> Progress:
    """创建 Arduino 风格的进度条"""
    console = console or get_console()

    return Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[cyan]{task.description}"),
        BarColumn(
            complete_style="cyan",
            finished_style="green",
            pulse_style="dim cyan",
        ),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=transient,
    )


@contextmanager
def create_spinner(
    message: str,
    console: Console = None,
):
    """
    创建 Spinner 上下文管理器

    使用示例：
        with create_spinner("Loading..."):
            time.sleep(2)
    """
    console = console or get_console()

    progress = Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[cyan]{task.description}"),
        console=console,
        transient=True,
    )

    progress.add_task(message, total=None)

    try:
        progress.start()
        yield progress
    finally:
        progress.stop()


class StepIndicator:
    """
    多步骤流程指示器

    使用示例：
        steps = ["Detect", "Generate", "Compile", "Flash"]
        indicator = StepIndicator(steps)
        for step in steps:
            indicator.next()
            # 执行步骤...
    """

    def __init__(self, steps: List[str], console: Console = None):
        self.steps = steps
        self.current = 0
        self.console = console or get_console()
        self.completed = []

    def next(self, success: bool = True) -> None:
        """进入下一步"""
        if self.current < len(self.steps):
            if success:
                self.completed.append(self.steps[self.current])
            self.current += 1
        self.render()

    def render(self) -> None:
        """渲染当前状态"""
        tree = Tree(">>> Progress", style="cyan")

        for i, step in enumerate(self.steps):
            if i < len(self.completed):
                tree.add(f"[green][OK][/green] {step}", style="dim")
            elif i == self.current:
                tree.add(f"[cyan][>][/cyan] [bold cyan]{step}[/bold cyan]", style="cyan")
            else:
                tree.add(f"[dim][ ] {step}[/dim]", style="dim")

        self.console.print(tree)

    def is_complete(self) -> bool:
        """检查是否所有步骤都已完成"""
        return self.current >= len(self.steps)

    def get_current_step(self) -> Optional[str]:
        """获取当前步骤名称"""
        if self.current < len(self.steps):
            return self.steps[self.current]
        return None


class WorkflowDisplay:
    """工作流显示组件"""

    def __init__(self, console: Console = None):
        self.console = console or get_console()
        self.tasks = {}

    def add_task(self, task_id: str, description: str, status: str = "pending") -> None:
        self.tasks[task_id] = {
            "description": description,
            "status": status,
            "details": "",
        }

    def update_task(self, task_id: str, status: Optional[str] = None, details: Optional[str] = None) -> None:
        if task_id in self.tasks:
            if status:
                self.tasks[task_id]["status"] = status
            if details:
                self.tasks[task_id]["details"] = details

    def render(self) -> Panel:
        status_icons = {
            "pending": "[ ]",
            "running": "[*]",
            "success": "[OK]",
            "error": "[X]",
        }
        status_styles = {
            "pending": "dim",
            "running": "cyan",
            "success": "green",
            "error": "red",
        }

        content = []
        for task_id, task in self.tasks.items():
            icon = status_icons.get(task["status"], "?")
            style = status_styles.get(task["status"], "white")
            line = f"[{style}]{icon}[/{style}] {task['description']}"
            if task["details"]:
                line += f"\n   [dim]{task['details']}[/dim]"
            content.append(line)

        return Panel(
            "\n".join(content),
            title="[cyan]Workflow[/cyan]",
            border_style="cyan",
        )

    def print(self) -> None:
        self.console.print(self.render())


class BuildProgress:
    """构建进度显示器"""

    def __init__(self, total_steps: int, console: Console = None):
        self.total = total_steps
        self.current = 0
        self.console = console or get_console()
        self.progress = create_progress(console)
        self.task = None

    def __enter__(self):
        self.progress.start()
        self.task = self.progress.add_task("Building...", total=self.total)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.stop()

    def advance(self, message: str = "") -> None:
        self.current += 1
        if message:
            self.progress.update(self.task, description=message)
        self.progress.advance(self.task)

    def set_message(self, message: str) -> None:
        self.progress.update(self.task, description=message)
