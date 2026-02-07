"""Arduino MCP Server - Main entry point"""

import re
import logging
from pathlib import Path
from typing import Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import AnyUrl

from .models import ProjectConfig, Component
from .arduino_cli import ArduinoCLI
from .code_generator import CodeGenerator

# Configure logging to stderr (MCP uses stdout for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Defaults to stderr
)
logger = logging.getLogger(__name__)

# Initialize server (lazily initialized)
app = Server("arduino-mcp-server")
_arduino_cli = None


def get_arduino_cli() -> ArduinoCLI:
    """Get or create ArduinoCLI instance (lazy initialization)"""
    global _arduino_cli
    if _arduino_cli is None:
        _arduino_cli = ArduinoCLI()
    return _arduino_cli


def parse_led_blink_intent(user_input: str) -> ProjectConfig:
    """Parse user intent for LED blink project with enhanced pattern matching"""
    config = ProjectConfig()
    user_lower = user_input.lower()
    
    logger.debug(f"Parsing intent from: {user_input}")
    
    # Extract board type (enhanced patterns)
    if re.search(r'\buno\b', user_lower):
        config.board_fqbn = "arduino:avr:uno"
        logger.info("Detected board: Arduino Uno")
    elif re.search(r'\bnano\b', user_lower):
        config.board_fqbn = "arduino:avr:nano"
        logger.info("Detected board: Arduino Nano")
    elif re.search(r'\b(pico|pi\s*pico|raspberry\s*pi\s*pico)\b', user_lower):
        config.board_fqbn = "arduino:mbed_rp2040:pico"
        logger.info("Detected board: Raspberry Pi Pico")
    elif re.search(r'\besp32\b', user_lower):
        config.board_fqbn = "esp32:esp32:esp32"
        logger.info("Detected board: ESP32")
    else:
        logger.warning("No board type detected, using default: Arduino Uno")
    
    # Extract pin number (enhanced patterns)
    # Supports: "13号引脚", "引脚13", "13 号引脚", "pin 13", "GPIO 13", "D13"
    pin_patterns = [
        r'(\d+)\s*号?\s*引脚',  # 13号引脚, 13 号引脚
        r'引脚\s*(\d+)',        # 引脚13
        r'pin\s*[:#]?\s*(\d+)', # pin 13, pin:13, pin#13
        r'gpio\s*(\d+)',        # GPIO 13
        r'd(\d+)',              # D13
        r'p(\d+)',              # P13
    ]
    
    pin = 13  # Default
    for pattern in pin_patterns:
        pin_match = re.search(pattern, user_lower)
        if pin_match:
            pin = int(pin_match.group(1))
            logger.info(f"Detected pin: {pin}")
            break
    else:
        logger.info(f"No pin specified, using default: {pin}")
    
    # Validate pin range
    if pin < 0 or pin > 50:
        logger.warning(f"Pin {pin} out of typical range (0-50), using default 13")
        pin = 13
    
    # Extract interval (enhanced patterns)
    # Supports: "每2秒", "2秒", "2s", "2000ms", "2000毫秒", "every 2 seconds"
    interval = 1000  # Default 1 second
    
    # Try milliseconds first
    ms_patterns = [
        r'(\d+)\s*ms\b',
        r'(\d+)\s*毫秒',
        r'(\d+)\s*millisecond',
    ]
    for pattern in ms_patterns:
        ms_match = re.search(pattern, user_lower)
        if ms_match:
            interval = int(ms_match.group(1))
            logger.info(f"Detected interval: {interval}ms")
            break
    else:
        # Try seconds
        sec_patterns = [
            r'每\s*(\d+\.?\d*)\s*秒',
            r'(\d+\.?\d*)\s*秒',
            r'(\d+\.?\d*)\s*s\b',
            r'every\s*(\d+\.?\d*)\s*second',
        ]
        for pattern in sec_patterns:
            sec_match = re.search(pattern, user_lower)
            if sec_match:
                seconds = float(sec_match.group(1))
                interval = int(seconds * 1000)
                logger.info(f"Detected interval: {seconds}s ({interval}ms)")
                break
        else:
            logger.info(f"No interval specified, using default: {interval}ms")
    
    # Validate interval range
    if interval < 10 or interval > 60000:
        logger.warning(f"Interval {interval}ms out of reasonable range (10-60000ms), using default 1000ms")
        interval = 1000
    
    # Add LED component
    config.components.append(Component(
        type="led",
        name="LED",
        pin=pin,
        mode="OUTPUT"
    ))
    config.blink_interval = interval
    
    logger.debug(f"Parsed config: board={config.board_fqbn}, pin={pin}, interval={interval}ms")
    return config


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="check_arduino_cli",
            description="Check if arduino-cli is installed and ready",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="detect_boards",
            description="Detect connected Arduino boards with connection verification",
            inputSchema={
                "type": "object",
                "properties": {
                    "verify_connection": {
                        "type": "boolean",
                        "description": "Verify that detected boards are actually accessible (default: true)",
                        "default": True
                    },
                    "board_type": {
                        "type": "string",
                        "description": "Optional: filter by board type (e.g., 'pico', 'uno', 'nano')"
                    }
                },
            }
        ),
        Tool(
            name="create_led_blink",
            description="Create LED blink project from natural language description",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "Natural language description (e.g., '用 Arduino Uno 做一个 LED 闪烁，13 号引脚')"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Project name (default: led_blink)",
                        "default": "led_blink"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory (default: ./arduino_projects)",
                        "default": "./arduino_projects"
                    }
                },
                "required": ["user_input"]
            }
        ),
        Tool(
            name="compile_sketch",
            description="Compile an Arduino sketch",
            inputSchema={
                "type": "object",
                "properties": {
                    "sketch_path": {
                        "type": "string",
                        "description": "Path to sketch directory"
                    },
                    "board_fqbn": {
                        "type": "string",
                        "description": "Board FQBN (e.g., arduino:avr:uno)",
                        "default": "arduino:avr:uno"
                    }
                },
                "required": ["sketch_path"]
            }
        ),
        Tool(
            name="upload_sketch",
            description="Upload compiled sketch to Arduino board",
            inputSchema={
                "type": "object",
                "properties": {
                    "sketch_path": {
                        "type": "string",
                        "description": "Path to sketch directory"
                    },
                    "board_fqbn": {
                        "type": "string",
                        "description": "Board FQBN",
                        "default": "arduino:avr:uno"
                    },
                    "port": {
                        "type": "string",
                        "description": "Serial port (auto-detect if not provided)"
                    }
                },
                "required": ["sketch_path"]
            }
        ),
        Tool(
            name="monitor_serial",
            description="Monitor serial output from Arduino",
            inputSchema={
                "type": "object",
                "properties": {
                    "port": {
                        "type": "string",
                        "description": "Serial port"
                    },
                    "baud_rate": {
                        "type": "integer",
                        "description": "Baud rate (default: 9600)",
                        "default": 9600
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Monitor duration in seconds (default: 10)",
                        "default": 10
                    }
                },
                "required": ["port"]
            }
        ),
        Tool(
            name="full_workflow_led_blink",
            description="Complete workflow: parse intent → generate code → compile → upload → monitor",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "Natural language description of LED blink project"
                    },
                    "auto_upload": {
                        "type": "boolean",
                        "description": "Automatically upload after compilation (default: true)",
                        "default": True
                    },
                    "monitor_after_upload": {
                        "type": "boolean",
                        "description": "Monitor serial after upload (default: true)",
                        "default": True
                    }
                },
                "required": ["user_input"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    arduino_cli = get_arduino_cli()
    logger.info(f"Tool called: {name}")
    
    if name == "check_arduino_cli":
        is_installed = arduino_cli.check_installation()
        if is_installed:
            return [TextContent(
                type="text",
                text="✅ arduino-cli is installed and ready"
            )]
        else:
            return [TextContent(
                type="text",
                text="❌ arduino-cli not found. Please install it first:\n"
                     "Windows: winget install ArduinoSA.CLI\n"
                     "Or visit: https://arduino.github.io/arduino-cli/"
            )]
    
    elif name == "detect_boards":
        verify_connection = arguments.get("verify_connection", True)
        board_type = arguments.get("board_type")
        
        # If specific board type requested
        if board_type:
            board = arduino_cli.detect_board_by_type(board_type)
            if not board:
                return [TextContent(
                    type="text",
                    text=f"❌ No {board_type} board detected.\n\n"
                         f"请检查：\n"
                         f"  1. 开发板是否已连接到电脑\n"
                         f"  2. USB 线是否支持数据传输（不是仅充电线）\n"
                         f"  3. 驱动是否已安装\n"
                         f"  4. 串口是否被其他程序占用\n\n"
                         f"💡 提示：可以先在 Wokwi 中仿真测试代码！"
                )]
            
            result = f"✅ Found {board_type} board:\n"
            result += f"  • Port: {board.port}\n"
            if board.fqbn:
                result += f"  • FQBN: {board.fqbn}\n"
            if board.name:
                result += f"  • Name: {board.name}\n"
            result += f"\n✅ Board is connected and accessible"
            
            return [TextContent(type="text", text=result)]
        
        # General board detection
        boards = arduino_cli.detect_boards(verify_connection=verify_connection)
        if not boards:
            return [TextContent(
                type="text",
                text="❌ No Arduino boards detected.\n\n"
                     "请检查：\n"
                     "  1. 开发板是否已连接到电脑\n"
                     "  2. USB 线是否支持数据传输（不是仅充电线）\n"
                     "  3. 驱动是否已安装\n"
                     "  4. 串口是否被其他程序占用（Arduino IDE、串口监视器等）\n\n"
                     "💡 提示：可以先在 Wokwi 中仿真测试代码！"
            )]
        
        result = f"✅ Detected {len(boards)} board(s):\n\n"
        for i, board in enumerate(boards, 1):
            result += f"{i}. Port: {board.port}\n"
            if board.fqbn:
                result += f"   FQBN: {board.fqbn}\n"
            if board.name:
                result += f"   Name: {board.name}\n"
            result += f"   Status: {'✅ Accessible' if verify_connection else '⚠️  Not verified'}\n\n"
        
        if verify_connection:
            result += "✅ All boards are connected and accessible"
        else:
            result += "⚠️  Connection not verified - boards may be in use"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "create_led_blink":
        # 从用户输入中解析 LED 闪烁项目的配置
        user_input = arguments["user_input"]
        project_name = arguments.get("project_name", "led_blink")
        output_dir = arguments.get("output_dir", "./arduino_projects")
        
        # 解析用户意图，提取板卡类型、引脚号、间隔等信息
        config = parse_led_blink_intent(user_input)
        
        # 生成代码和 Wokwi 仿真文件
        generator = CodeGenerator(Path(output_dir))
        sketch_dir = generator.generate_led_blink(config, project_name, include_wokwi=True)
        
        # 🔧 关键：编译代码以生成固件文件（.hex/.uf2/.bin）
        # Wokwi 仿真需要这些编译产物才能运行
        print(f"📦 正在编译项目以生成固件文件...")
        compile_result = arduino_cli.compile_sketch(sketch_dir, config.board_fqbn)
        
        led = config.components[0]
        result = f"✅ LED Blink 项目创建成功！\n\n"
        result += f"📁 位置: {sketch_dir}\n"
        result += f"📌 板卡: {config.board_fqbn}\n"
        result += f"📍 LED 引脚: {led.pin}\n"
        result += f"⏱️  闪烁间隔: {config.blink_interval}ms\n\n"
        
        # 显示编译结果
        if compile_result.success:
            result += f"✅ 编译成功\n"
            if compile_result.build_path:
                result += f"📦 固件位置: {compile_result.build_path}\n"
        else:
            result += f"⚠️  编译失败（仿真文件仍可用）\n"
        
        result += f"\n📦 生成的文件:\n"
        result += f"  • {project_name}.ino (Arduino 源代码)\n"
        result += f"  • simulation/diagram.json (Wokwi 电路图)\n"
        result += f"  • simulation/wokwi.toml (Wokwi 配置)\n"
        result += f"  • build/{project_name}.ino.hex (编译产物)\n\n"
        result += f"🎮 Wokwi 仿真:\n"
        result += f"  1. 在 VS Code 中打开项目文件夹\n"
        result += f"  2. 打开 simulation/diagram.json\n"
        result += f"  3. 按 F1 → 'Wokwi: Start Simulator'\n"
        result += f"  4. 查看电路并测试代码！\n\n"
        result += f"📋 下一步:\n"
        result += f"  • [在 Wokwi 中测试] - 查看接线和仿真\n"
        result += f"  • [上传到硬件] - 使用 upload_sketch 工具\n"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "compile_sketch":
        sketch_path = Path(arguments["sketch_path"])
        board_fqbn = arguments.get("board_fqbn", "arduino:avr:uno")
        
        result = arduino_cli.compile_sketch(sketch_path, board_fqbn)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"✅ Compilation successful!\n\n{result.output}"
            )]
        else:
            error_msg = f"❌ Compilation failed:\n\n{result.output}"
            if result.errors:
                error_msg += "\n\nErrors:\n" + "\n".join(result.errors)
            return [TextContent(type="text", text=error_msg)]
    
    elif name == "upload_sketch":
        sketch_path = Path(arguments["sketch_path"])
        board_fqbn = arguments.get("board_fqbn", "arduino:avr:uno")
        port = arguments.get("port")
        
        result = arduino_cli.upload_sketch(sketch_path, board_fqbn, port)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"✅ Upload successful!\n\nPort: {result.port}\n\n{result.message}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"❌ Upload failed:\n\n{result.message}"
            )]
    
    elif name == "monitor_serial":
        port = arguments["port"]
        baud_rate = arguments.get("baud_rate", 9600)
        duration = arguments.get("duration", 10)
        
        lines = arduino_cli.monitor_serial(port, baud_rate, duration)
        
        result = f"📡 Serial Monitor (Port: {port}, Baud: {baud_rate})\n"
        result += f"Duration: {duration}s\n\n"
        result += "\n".join(lines) if lines else "No output received"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "full_workflow_led_blink":
        user_input = arguments["user_input"]
        auto_upload = arguments.get("auto_upload", True)
        monitor_after = arguments.get("monitor_after_upload", True)
        
        output = "🚀 Starting full LED blink workflow...\n\n"
        
        # Step 1: Parse and generate (with Wokwi)
        output += "Step 1: Parsing intent and generating code...\n"
        config = parse_led_blink_intent(user_input)
        generator = CodeGenerator(Path("./arduino_projects"))
        sketch_dir = generator.generate_led_blink(config, "led_blink", include_wokwi=True)
        
        led = config.components[0]
        output += f"✅ Code generated at: {sketch_dir}\n"
        output += f"   📌 Board: {config.board_fqbn}\n"
        output += f"   📍 LED Pin: {led.pin}\n"
        output += f"   ⏱️  Interval: {config.blink_interval}ms\n\n"
        
        # Show Wokwi simulation option
        output += "🎮 Wokwi Simulation Files Generated:\n"
        output += f"   • diagram.json (circuit diagram)\n"
        output += f"   • wokwi.toml (configuration)\n\n"
        output += "📋 下一步选择：\n"
        output += "   1. [在 Wokwi 中仿真] - 先测试代码和接线\n"
        output += "      • 在 VS Code 中打开 diagram.json\n"
        output += "      • 按 F1 → 'Wokwi: Start Simulator'\n"
        output += "      • 查看电路接线和运行效果\n"
        output += "   2. [直接上传到硬件] - 如果已经接好线\n\n"
        output += "💡 推荐：先在 Wokwi 中仿真，确认接线正确后再上传硬件！\n\n"
        
        # Step 2: Compile
        output += "Step 2: Compiling...\n"
        compile_result = arduino_cli.compile_sketch(sketch_dir, config.board_fqbn)
        if not compile_result.success:
            output += f"❌ Compilation failed:\n{compile_result.output}\n"
            return [TextContent(type="text", text=output)]
        output += "✅ Compilation successful\n\n"
        
        # Step 3: Upload (if auto_upload is True)
        if auto_upload:
            output += "Step 3: Detecting board and uploading...\n"
            
            # Try to detect specific board type from config
            board_type = None
            if "pico" in config.board_fqbn.lower():
                board_type = "pico"
            elif "uno" in config.board_fqbn.lower():
                board_type = "uno"
            elif "nano" in config.board_fqbn.lower():
                board_type = "nano"
            
            # Detect with verification
            if board_type:
                output += f"Looking for {board_type} board...\n"
                board = arduino_cli.detect_board_by_type(board_type)
                if not board:
                    output += f"❌ No {board_type} board detected.\n\n"
                    output += "请检查：\n"
                    output += f"  1. {board_type.upper()} 开发板是否已连接\n"
                    output += "  2. USB 线是否支持数据传输\n"
                    output += "  3. 驱动是否已安装\n"
                    output += "  4. 串口是否被占用\n\n"
                    output += "💡 建议：先在 Wokwi 中仿真测试！\n"
                    return [TextContent(type="text", text=output)]
                boards = [board]
                output += f"✅ Found {board_type} at {board.port}\n"
            else:
                boards = arduino_cli.detect_boards(verify_connection=True)
                if not boards:
                    output += "❌ No board detected.\n\n"
                    output += "请检查：\n"
                    output += "  1. 开发板是否已连接\n"
                    output += "  2. USB 线是否支持数据传输\n"
                    output += "  3. 驱动是否已安装\n"
                    output += "  4. 串口是否被占用\n\n"
                    output += "💡 建议：先在 Wokwi 中仿真测试！\n"
                    return [TextContent(type="text", text=output)]
                output += f"✅ Found board at {boards[0].port}\n"
            
            upload_result = arduino_cli.upload_sketch(
                sketch_dir, 
                config.board_fqbn, 
                boards[0].port
            )
            if not upload_result.success:
                output += f"❌ Upload failed:\n{upload_result.message}\n"
                return [TextContent(type="text", text=output)]
            output += f"✅ Upload successful to {upload_result.port}\n\n"
            
            # Step 4: Monitor
            if monitor_after:
                output += "Step 4: Monitoring serial output...\n"
                lines = arduino_cli.monitor_serial(upload_result.port, config.serial_baud, 5)
                output += "\n".join(lines[:10]) if lines else "No output"
                output += "\n\n"
            
            output += "🎉 Workflow complete! Your LED should be blinking now.\n"
        else:
            output += "\n✅ Code ready! Next steps:\n"
            output += "   • Test in Wokwi simulator first (recommended)\n"
            output += "   • Or upload to hardware when ready\n"
        
        return [TextContent(type="text", text=output)]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


def main():
    """Main entry point"""
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
