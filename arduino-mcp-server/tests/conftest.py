"""Pytest fixtures for Arduino MCP Server CI tests"""

import os
import tempfile
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output, cleaned up after test."""
    tmpdir = tempfile.mkdtemp(prefix="arduino_mcp_test_")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def project_config_uno():
    """Sample ProjectConfig for Arduino Uno LED blink."""
    from arduino_mcp_server.models import ProjectConfig, Component

    return ProjectConfig(
        board_fqbn="arduino:avr:uno",
        components=[
            Component(type="led", name="LED", pin=13, mode="OUTPUT")
        ],
        blink_interval=1000,
        serial_enabled=True,
    )


@pytest.fixture
def project_config_pico():
    """Sample ProjectConfig for Raspberry Pi Pico LED blink."""
    from arduino_mcp_server.models import ProjectConfig, Component

    return ProjectConfig(
        board_fqbn="arduino:mbed_rp2040:pico",
        components=[
            Component(type="led", name="LED", pin=25, mode="OUTPUT")
        ],
        blink_interval=500,
        serial_enabled=True,
    )


def has_arduino_cli() -> bool:
    """Check if arduino-cli is installed and working."""
    try:
        from arduino_mcp_server.arduino_cli import ArduinoCLI

        cli = ArduinoCLI()
        return cli.check_installation()
    except Exception:
        return False


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests, no external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests, require arduino-cli"
    )
    config.addinivalue_line(
        "markers", "hardware: Hardware tests, require physical board"
    )
