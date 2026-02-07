"""Hardware tests - require physical Arduino board, SKIPPED in CI by default"""

import os
import pytest


# Skip all tests in this module unless ARDUINO_HARDWARE_TEST=1
pytestmark = pytest.mark.skipif(
    os.environ.get("ARDUINO_HARDWARE_TEST") != "1",
    reason="Hardware tests skipped (set ARDUINO_HARDWARE_TEST=1 to run)",
)


@pytest.mark.hardware
class TestUpload:
    """Upload tests - require connected board."""

    def test_upload_sketch(self, temp_output_dir, project_config_uno):
        """Upload compiled sketch to board. Requires Uno connected."""
        from arduino_mcp_server.code_generator import CodeGenerator
        from arduino_mcp_server.arduino_cli import ArduinoCLI

        generator = CodeGenerator(temp_output_dir)
        project_dir = generator.generate_led_blink(
            project_config_uno, "upload_test", include_wokwi=True
        )

        cli = ArduinoCLI()
        compile_result = cli.compile_sketch(
            project_dir, project_config_uno.board_fqbn
        )
        assert compile_result.success, "Compilation must succeed before upload"

        boards = cli.detect_boards(verify_connection=True)
        pytest.skip("No board connected") if not boards else None

        upload_result = cli.upload_sketch(
            project_dir,
            project_config_uno.board_fqbn,
            port=boards[0].port,
        )
        assert upload_result.success, upload_result.message
