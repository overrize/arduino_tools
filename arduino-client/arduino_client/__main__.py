"""允许使用 python -m arduino_client 运行 CLI"""
try:
    from .cli_rich import main
except ImportError:
    from .cli import main

if __name__ == "__main__":
    exit(main())
