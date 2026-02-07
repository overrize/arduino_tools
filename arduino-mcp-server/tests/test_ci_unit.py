"""Unit tests - no external dependencies, always run in CI"""

import json
import pytest
from pathlib import Path


@pytest.mark.unit
class TestModels:
    """Test data models."""

    def test_project_config_defaults(self):
        from arduino_mcp_server.models import ProjectConfig

        config = ProjectConfig()
        assert config.board_fqbn == "arduino:avr:uno"
        assert config.blink_interval == 1000
        assert config.serial_enabled is True
        assert config.serial_baud == 9600

    def test_component_creation(self):
        from arduino_mcp_server.models import Component

        led = Component(type="led", name="LED", pin=13, mode="OUTPUT")
        assert led.type == "led"
        assert led.pin == 13
        assert led.mode == "OUTPUT"


@pytest.mark.unit
class TestIntentParsing:
    """Test parse_led_blink_intent function."""

    def test_parse_uno_chinese(self):
        from arduino_mcp_server.server import parse_led_blink_intent

        config = parse_led_blink_intent("用 Arduino Uno 做一个 LED 闪烁，13 号引脚")
        assert config.board_fqbn == "arduino:avr:uno"
        assert config.components[0].pin == 13

    def test_parse_nano_english(self):
        from arduino_mcp_server.server import parse_led_blink_intent

        config = parse_led_blink_intent(
            "Arduino Nano LED blink pin 7 every 2 seconds"
        )
        assert config.board_fqbn == "arduino:avr:nano"
        assert config.components[0].pin == 7
        assert config.blink_interval == 2000

    def test_parse_pico(self):
        from arduino_mcp_server.server import parse_led_blink_intent

        config = parse_led_blink_intent("Pico LED 闪烁 25 号引脚")
        assert config.board_fqbn == "arduino:mbed_rp2040:pico"
        assert config.components[0].pin == 25

    def test_parse_default_pin_when_missing(self):
        from arduino_mcp_server.server import parse_led_blink_intent

        config = parse_led_blink_intent("Uno LED blink")
        assert config.components[0].pin == 13  # Default for Uno

    def test_parse_default_interval(self):
        from arduino_mcp_server.server import parse_led_blink_intent

        config = parse_led_blink_intent("Uno LED blink pin 13")
        assert config.blink_interval == 1000  # Default 1 second


@pytest.mark.unit
class TestCodeGeneration:
    """Test code generation (no arduino-cli, no compilation)."""

    def test_generate_led_blink_uno(self, temp_output_dir, project_config_uno):
        from arduino_mcp_server.code_generator import CodeGenerator

        generator = CodeGenerator(temp_output_dir)
        project_dir = generator.generate_led_blink(
            project_config_uno, "test_led", include_wokwi=True
        )

        assert project_dir.exists()
        sketch_file = project_dir / "test_led.ino"
        assert sketch_file.exists()
        content = sketch_file.read_text()
        assert "LED_PIN" in content
        assert "pinMode(LED_PIN, OUTPUT)" in content
        assert "delay(1000)" in content

    def test_generate_creates_simulation_dir(
        self, temp_output_dir, project_config_uno
    ):
        from arduino_mcp_server.code_generator import CodeGenerator

        generator = CodeGenerator(temp_output_dir)
        project_dir = generator.generate_led_blink(
            project_config_uno, "test_wokwi", include_wokwi=True
        )

        simulation_dir = project_dir / "simulation"
        assert simulation_dir.exists()
        diagram = simulation_dir / "diagram.json"
        wokwi_toml = simulation_dir / "wokwi.toml"
        assert diagram.exists()
        assert wokwi_toml.exists()

    def test_wokwi_diagram_valid_json(
        self, temp_output_dir, project_config_uno
    ):
        from arduino_mcp_server.code_generator import CodeGenerator

        generator = CodeGenerator(temp_output_dir)
        project_dir = generator.generate_led_blink(
            project_config_uno, "test_json", include_wokwi=True
        )

        diagram_path = project_dir / "simulation" / "diagram.json"
        with open(diagram_path) as f:
            diagram = json.load(f)

        assert "version" in diagram
        assert "parts" in diagram
        assert "connections" in diagram
        assert len(diagram["parts"]) >= 1

    def test_generate_without_wokwi(self, temp_output_dir, project_config_uno):
        from arduino_mcp_server.code_generator import CodeGenerator

        generator = CodeGenerator(temp_output_dir)
        project_dir = generator.generate_led_blink(
            project_config_uno, "no_wokwi", include_wokwi=False
        )

        assert (project_dir / "no_wokwi.ino").exists()
        simulation_dir = project_dir / "simulation"
        assert not (simulation_dir / "diagram.json").exists()


@pytest.mark.unit
class TestTemplates:
    """Test template retrieval."""

    def test_get_led_blink_template(self):
        from arduino_mcp_server.templates import get_template

        template = get_template("led_blink")
        assert "LED_PIN" in template
        assert "{{ pin }}" in template

    def test_get_button_led_template(self):
        from arduino_mcp_server.templates import get_template

        template = get_template("button_led")
        assert "BUTTON_PIN" in template
        assert "LED_PIN" in template
