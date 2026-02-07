"""Integration tests - require arduino-cli, run in CI when arduino-cli is installed"""

import subprocess
import pytest
from pathlib import Path


def _arduino_cli_available() -> bool:
    """Check if arduino-cli is in PATH and working."""
    try:
        result = subprocess.run(
            ["arduino-cli", "version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


requires_arduino_cli = pytest.mark.skipif(
    not _arduino_cli_available(),
    reason="arduino-cli not installed or not in PATH",
)


@pytest.mark.integration
@requires_arduino_cli
class TestArduinoCLIWrapper:
    """Test ArduinoCLI wrapper with real arduino-cli."""

    def test_check_installation(self):
        from arduino_mcp_server.arduino_cli import ArduinoCLI

        cli = ArduinoCLI()
        assert cli.check_installation() is True

    def test_detect_boards_no_verify(self):
        """Detect boards without connection verification (works without hardware)."""
        from arduino_mcp_server.arduino_cli import ArduinoCLI

        cli = ArduinoCLI()
        boards = cli.detect_boards(verify_connection=False)
        # May be empty if no board connected - that's OK
        assert isinstance(boards, list)


@pytest.mark.integration
@requires_arduino_cli
class TestCompilation:
    """Test sketch compilation (requires arduino core installed)."""

    def test_compile_led_blink(self, temp_output_dir, project_config_uno):
        from arduino_mcp_server.code_generator import CodeGenerator
        from arduino_mcp_server.arduino_cli import ArduinoCLI

        generator = CodeGenerator(temp_output_dir)
        project_dir = generator.generate_led_blink(
            project_config_uno, "compile_test", include_wokwi=True
        )

        cli = ArduinoCLI()
        result = cli.compile_sketch(project_dir, project_config_uno.board_fqbn)

        assert result.success is True, f"Compilation failed: {result.output}"
        assert result.build_path is not None
        build_path = Path(result.build_path)
        assert build_path.exists()
        # Check for .hex file (AVR) or .uf2 (Pico)
        hex_files = list(build_path.glob("*.hex"))
        uf2_files = list(build_path.glob("*.uf2"))
        assert len(hex_files) > 0 or len(uf2_files) > 0


@pytest.mark.integration
@requires_arduino_cli
class TestLibrarySearch:
    """Test library search (network may be slow)."""

    def test_search_library(self):
        from arduino_mcp_server.arduino_cli import ArduinoCLI

        cli = ArduinoCLI()
        results = cli.search_library("Servo")
        # May be empty on network issues
        assert isinstance(results, list)
