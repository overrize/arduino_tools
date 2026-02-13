"""Arduino Client CLI 入口"""
import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .client import ArduinoClient
from .code_generator import generate_arduino_code_fix
from .llm_config import is_llm_configured
from .setup import setup_config
from .interactive import run_interactive

logging.basicConfig(
    level=logging.INFO,
    format="[arduino_client] %(levelname)s: %(message)s",
    stream=sys.stdout,
)

SETUP_INSTRUCTIONS = """
┌─────────────────────────────────────────────────────────────────┐
│  Arduino Client 需要配置大模型 API 才能生成代码                  │
├─────────────────────────────────────────────────────────────────┤
│  方式一：创建 .env 文件（推荐）                                 │
│  复制 .env.example 为 .env，填入：                               │
│                                                                 │
│  # Kimi K2（参考 platform.moonshot.cn/docs/guide/agent-support）  │
│  OPENAI_API_KEY=sk-xxx                                         │
│  OPENAI_API_BASE=https://api.moonshot.cn/v1                     │
│  OPENAI_MODEL=kimi-k2-0905-preview   # 或 kimi-k2-turbo-preview│
│                                                                 │
│  # OpenAI                                                       │
│  OPENAI_API_KEY=sk-xxx                                          │
├─────────────────────────────────────────────────────────────────┤
│  方式二：设置环境变量                                           │
│  PowerShell: $env:OPENAI_API_KEY="sk-xxx"                       │
│  Linux/Mac: export OPENAI_API_KEY=sk-xxx                        │
├─────────────────────────────────────────────────────────────────┤
│  获取 API Key：                                                 │
│  • Kimi:   https://platform.moonshot.cn/console/api-keys       │
│  • OpenAI: https://platform.openai.com/api-keys                 │
└─────────────────────────────────────────────────────────────────┘

配置完成后重新运行: python -m arduino_client
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="arduino_client",
        description="Arduino Client — Arduino 自然语言端到端开发 Client",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-C", "--work-dir", type=Path, default=Path.cwd(), help="工作目录")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出 DEBUG 日志")
    
    sub = parser.add_subparsers(dest="cmd", required=False)
    
    # gen — 生成代码
    p_gen = sub.add_parser("gen", help="根据自然语言生成工程")
    p_gen.add_argument("prompt", help="需求描述，如：用 Arduino Uno 做一个 LED 闪烁，13 号引脚")
    p_gen.add_argument("project_name", help="项目名称")
    p_gen.add_argument("-o", "--output", type=Path, help="输出目录，默认 work-dir/projects/arduino_projects/{project_name}")
    p_gen.add_argument("--build", action="store_true", help="生成后编译")
    p_gen.add_argument("--flash", action="store_true", help="编译后烧录")
    p_gen.add_argument("--fqbn", type=str, help="板卡 FQBN（如 arduino:avr:uno），未指定时自动检测")
    p_gen.set_defaults(func=_cmd_gen)
    
    # detect — 检测板卡
    p_detect = sub.add_parser("detect", help="检测已连接的 Arduino 板卡")
    p_detect.add_argument("--type", type=str, help="按类型检测（如 'uno', 'pico', 'nano'）")
    p_detect.set_defaults(func=_cmd_detect)
    
    # build — 编译
    p_build = sub.add_parser("build", help="编译工程")
    p_build.add_argument("project", type=Path, help="工程目录")
    p_build.add_argument("--fqbn", type=str, required=True, help="板卡 FQBN（如 arduino:avr:uno）")
    p_build.add_argument("--flash", action="store_true", help="编译后烧录")
    p_build.set_defaults(func=_cmd_build)
    
    # upload — 上传
    p_upload = sub.add_parser("upload", help="上传固件到板卡")
    p_upload.add_argument("project", type=Path, help="工程目录")
    p_upload.add_argument("--fqbn", type=str, required=True, help="板卡 FQBN")
    p_upload.add_argument("--port", type=str, help="串口，未指定时自动检测")
    p_upload.set_defaults(func=_cmd_upload)
    
    # demo — Demo
    p_demo = sub.add_parser("demo", help="运行 Demo")
    p_demo.add_argument("scenario", choices=["blink"], help="Demo 场景")
    p_demo.add_argument("--board", type=str, default="uno", help="板卡类型（默认: uno）")
    p_demo.add_argument("--pin", type=int, default=13, help="LED 引脚（默认: 13）")
    p_demo.add_argument("--interval", type=int, default=1000, help="闪烁间隔毫秒（默认: 1000）")
    p_demo.add_argument("--flash", action="store_true", help="自动上传")
    p_demo.set_defaults(func=_cmd_demo)
    
    # setup — 配置向导
    p_setup = sub.add_parser("setup", help="交互式配置向导（首次使用推荐）")
    p_setup.set_defaults(func=_cmd_setup)
    
    # interactive — 交互式终端（可停留的菜单客户端）
    p_interactive = sub.add_parser(
        "interactive",
        aliases=["i", "shell"],
        help="进入交互式终端（菜单驱动，类似可停留的客户端）",
    )
    p_interactive.set_defaults(func=_cmd_interactive)
    
    args = parser.parse_args()
    if getattr(args, "verbose", False):
        logging.getLogger("arduino_client").setLevel(logging.DEBUG)
    
    # setup 命令不依赖 arduino-cli，仅配置 LLM API
    if args.cmd == "setup":
        success = setup_config(Path(args.work_dir))
        return 0 if success else 1
    
    # interactive 命令不依赖 arduino-cli 即可进入（内部按需创建 Client）
    if args.cmd == "interactive":
        return run_interactive(Path(args.work_dir))
    
    # 无子命令时直接进入交互式终端（首次安装即可在菜单中选 1 完成配置）
    if args.cmd is None:
        return run_interactive(Path(args.work_dir))
    
    # 其他命令需要 ArduinoClient（会检查 arduino-cli）
    client = ArduinoClient(work_dir=args.work_dir)
    return args.func(client, args)


def _cmd_setup(client: ArduinoClient, args) -> int:
    """配置向导命令"""
    success = setup_config(client.work_dir)
    return 0 if success else 1


def _cmd_interactive(client: ArduinoClient, args) -> int:
    """交互式终端（一般已在 main 中提前处理，此处兜底）"""
    return run_interactive(Path(args.work_dir))


def _cmd_gen(client: ArduinoClient, args) -> int:
    """生成代码命令"""
    if not is_llm_configured(client.work_dir):
        try:
            from rich.console import Console
            console = Console()
            console.print("\n[bold yellow]⚠ LLM API 未配置[/bold yellow]")
            console.print("运行 [cyan]arduino-client setup[/cyan] 进行交互式配置\n")
        except ImportError:
            print("\n⚠ LLM API 未配置")
            print("运行 arduino-client setup 进行交互式配置\n")
        print(SETUP_INSTRUCTIONS)
        return 1
    
    output_dir = args.output
    if output_dir is None:
        from . import _paths
        projects_dir = _paths.get_projects_dir(client.work_dir)
        output_dir = projects_dir / "arduino_projects" / args.project_name
    
    # 生成代码
    try:
        project_dir = client.generate(args.prompt, args.project_name, output_dir=output_dir)
        print(f"工程已生成: {project_dir}")
    except Exception as e:
        print(f"生成失败: {e}", file=sys.stderr)
        return 1
    
    # 编译（如果需要）
    if args.build or args.flash:
        # 确定 FQBN
        fqbn = args.fqbn
        if not fqbn:
            # 尝试从 prompt 推断板卡类型
            prompt_lower = args.prompt.lower()
            if "pico" in prompt_lower:
                board_type = "pico"
                fqbn = "arduino:mbed_rp2040:pico"
            elif "nano" in prompt_lower:
                board_type = "nano"
                fqbn = "arduino:avr:nano"
            elif "esp32" in prompt_lower:
                fqbn = "esp32:esp32:esp32"
            else:
                # 默认检测第一个板卡
                boards = client.detect_boards()
                if not boards:
                    print("未检测到板卡，请指定 --fqbn", file=sys.stderr)
                    return 1
                fqbn = boards[0].fqbn or "arduino:avr:uno"
        
        max_fix_rounds = 3
        for attempt in range(max_fix_rounds + 1):
            label = "重新编译" if attempt > 0 else "编译"
            print(f"正在{label}...")
            try:
                result = client.build(project_dir, fqbn)
                if result.success:
                    print(f"编译成功: {result.build_path}")
                    break
                else:
                    err_msg = result.output
                    print(f"编译失败: {err_msg[:500]}{'...' if len(err_msg) > 500 else ''}")
                    if attempt < max_fix_rounds:
                        try:
                            sketch_file = project_dir / f"{args.project_name}.ino"
                            current_code = sketch_file.read_text(encoding="utf-8")
                            fixed = generate_arduino_code_fix(
                                args.prompt, current_code, err_msg, work_dir=client.work_dir
                            )
                            sketch_file.write_text(fixed, encoding="utf-8")
                            print(f"  [修复] 第 {attempt + 1} 轮修正代码")
                        except Exception as fix_e:
                            print(f"修复失败: {fix_e}", file=sys.stderr)
                            return 1
                    else:
                        print(f"已达最大修复轮数 ({max_fix_rounds})", file=sys.stderr)
                        return 1
            except Exception as e:
                print(f"编译错误: {e}", file=sys.stderr)
                return 1
        
        # 上传（如果需要）
        if args.flash:
            boards = client.detect_boards()
            if not boards:
                print("未检测到板卡", file=sys.stderr)
                return 1
            port = boards[0].port
            try:
                result = client.upload(project_dir, fqbn, port=port)
                if result.success:
                    print(f"上传成功到 {result.port}")
                else:
                    print(f"上传失败: {result.message}", file=sys.stderr)
                    return 1
            except Exception as e:
                print(f"上传错误: {e}", file=sys.stderr)
                return 1
    
    return 0


def _cmd_detect(client: ArduinoClient, args) -> int:
    """检测板卡命令"""
    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()
        use_rich = True
    except ImportError:
        use_rich = False
    
    if args.type:
        board = client.detect_board_by_type(args.type)
        if not board:
            if use_rich:
                console.print(f"[red]未检测到 {args.type} 板卡[/red]")
            else:
                print(f"未检测到 {args.type} 板卡", file=sys.stderr)
            return 1
        
        if use_rich:
            table = Table(title=f"找到 {args.type} 板卡", show_header=True, header_style="bold cyan")
            table.add_column("属性", style="cyan")
            table.add_column("值", style="green")
            table.add_row("串口", board.port)
            if board.fqbn:
                table.add_row("FQBN", board.fqbn)
            if board.name:
                table.add_row("名称", board.name)
            console.print(table)
        else:
            print(f"✅ 找到 {args.type} 板卡:")
            print(f"  串口: {board.port}")
            if board.fqbn:
                print(f"  FQBN: {board.fqbn}")
            if board.name:
                print(f"  名称: {board.name}")
    else:
        boards = client.detect_boards()
        if not boards:
            if use_rich:
                console.print("[red]未检测到 Arduino 板卡[/red]")
            else:
                print("未检测到 Arduino 板卡", file=sys.stderr)
            return 1
        
        if use_rich:
            table = Table(title=f"检测到 {len(boards)} 个板卡", show_header=True, header_style="bold cyan")
            table.add_column("序号", style="cyan", width=6)
            table.add_column("串口", style="green")
            table.add_column("FQBN", style="yellow")
            table.add_column("名称", style="blue")
            for i, board in enumerate(boards, 1):
                table.add_row(
                    str(i),
                    board.port,
                    board.fqbn or "-",
                    board.name or "-"
                )
            console.print(table)
        else:
            print(f"✅ 检测到 {len(boards)} 个板卡:")
            for i, board in enumerate(boards, 1):
                print(f"\n{i}. 串口: {board.port}")
                if board.fqbn:
                    print(f"   FQBN: {board.fqbn}")
                if board.name:
                    print(f"   名称: {board.name}")
    return 0


def _cmd_build(client: ArduinoClient, args) -> int:
    """编译命令"""
    project_dir = args.project if Path(args.project).is_absolute() else client.work_dir / args.project
    project_dir = Path(project_dir).resolve()
    
    try:
        result = client.build(project_dir, args.fqbn)
        if result.success:
            print(f"编译成功: {result.build_path}")
            if args.flash:
                boards = client.detect_boards()
                if not boards:
                    print("未检测到板卡", file=sys.stderr)
                    return 1
                upload_result = client.upload(project_dir, args.fqbn, port=boards[0].port)
                if upload_result.success:
                    print(f"上传成功到 {upload_result.port}")
                else:
                    print(f"上传失败: {upload_result.message}", file=sys.stderr)
                    return 1
        else:
            print(f"编译失败: {result.output}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"编译错误: {e}", file=sys.stderr)
        return 1
    
    return 0


def _cmd_upload(client: ArduinoClient, args) -> int:
    """上传命令"""
    project_dir = args.project if Path(args.project).is_absolute() else client.work_dir / args.project
    project_dir = Path(project_dir).resolve()
    
    try:
        result = client.upload(project_dir, args.fqbn, port=args.port)
        if result.success:
            print(f"上传成功到 {result.port}")
        else:
            print(f"上传失败: {result.message}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"上传错误: {e}", file=sys.stderr)
        return 1
    
    return 0


def _cmd_demo(client: ArduinoClient, args) -> int:
    """Demo 命令"""
    if args.scenario == "blink":
        try:
            project_dir = client.demo_blink(
                board_type=args.board,
                pin=args.pin,
                interval=args.interval,
                flash=args.flash,
            )
            print(f"Demo 完成: {project_dir}")
        except Exception as e:
            print(f"Demo 失败: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
