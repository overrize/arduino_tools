"""Raspberry Pi Pico workflow test"""

from pathlib import Path
from src.arduino_mcp_server.models import ProjectConfig, Component
from src.arduino_mcp_server.code_generator import CodeGenerator
from src.arduino_mcp_server.arduino_cli import ArduinoCLI


def test_pico_workflow():
    """Test complete workflow with Raspberry Pi Pico"""
    print("=" * 60)
    print("Raspberry Pi Pico - LED Blink Test")
    print("=" * 60)
    
    # Initialize
    cli = ArduinoCLI()
    
    # Step 1: Check installation
    print("\n[Step 1] Checking arduino-cli installation...")
    if not cli.check_installation():
        print("❌ arduino-cli not found")
        return False
    print("✅ arduino-cli is installed")
    
    # Step 2: Check for Pico in BOOTSEL mode
    print("\n[Step 2] Checking for Raspberry Pi Pico...")
    import os
    if os.path.exists("D:\\"):
        # Check if it's RPI-RP2
        try:
            with open("D:\\INFO_UF2.TXT", "r") as f:
                content = f.read()
                if "RP2040" in content:
                    print("✅ Raspberry Pi Pico detected in BOOTSEL mode (D:)")
                    print("   This is the USB mass storage mode for uploading UF2 files")
        except:
            pass
    
    # Step 3: Create project for Pico
    print("\n[Step 3] Creating LED blink project for Pico...")
    print("   Using pin 25 (onboard LED)")
    
    config = ProjectConfig(
        board_fqbn="arduino:mbed_rp2040:pico",
        components=[
            Component(type="led", name="LED", pin=25, mode="OUTPUT")
        ],
        blink_interval=1000,
        serial_enabled=True
    )
    
    generator = CodeGenerator(Path("./test_output"))
    sketch_dir = generator.generate_led_blink(config, "pico_blink")
    print(f"✅ Project created at: {sketch_dir}")
    
    # Show the generated code
    sketch_file = sketch_dir / "pico_blink.ino"
    print("\n[Generated Code Preview]")
    print("-" * 60)
    with open(sketch_file, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:20], 1):
            print(f"{i:2d}: {line}", end="")
    print("-" * 60)
    
    # Step 4: Compile
    print("\n[Step 4] Compiling for Raspberry Pi Pico...")
    compile_result = cli.compile_sketch(sketch_dir, config.board_fqbn)
    if not compile_result.success:
        print(f"❌ Compilation failed:")
        print(compile_result.output)
        return False
    print("✅ Compilation successful")
    
    # Step 5: Upload instructions
    print("\n[Step 5] Upload Instructions")
    print("=" * 60)
    print("To upload to Raspberry Pi Pico:")
    print()
    print("Option 1: Using BOOTSEL mode (Current)")
    print("  1. Keep Pico in BOOTSEL mode (RPI-RP2 drive visible)")
    print("  2. The compiled UF2 file will be copied to the drive")
    print("  3. Pico will automatically reboot and run the program")
    print()
    print("Option 2: Using Serial (After first upload)")
    print("  1. After first upload, Pico will appear as a serial port")
    print("  2. You can then upload directly via serial")
    print()
    
    # Try to upload
    print("\n[Attempting Upload]")
    if os.path.exists("D:\\"):
        print("✅ Pico is in BOOTSEL mode")
        print("   Uploading via UF2...")
        
        # For Pico in BOOTSEL mode, arduino-cli will handle the UF2 upload
        upload_result = cli.upload_sketch(sketch_dir, config.board_fqbn, None)
        if upload_result.success:
            print(f"✅ Upload successful!")
            print("\n🎉 Your Pico should now be running the LED blink program!")
            print("   The onboard LED (pin 25) should be flashing.")
            print("\n   After the Pico reboots, it will appear as a serial port")
            print("   and you can upload new programs without BOOTSEL mode.")
        else:
            print(f"⚠️  Upload via arduino-cli: {upload_result.message}")
            print("\nManual upload option:")
            print(f"  1. Find the UF2 file in: {sketch_dir}")
            print(f"  2. Copy it to the RPI-RP2 drive (D:)")
            print(f"  3. Pico will automatically reboot")
    else:
        print("⚠️  Pico not in BOOTSEL mode")
        print("\nTo enter BOOTSEL mode:")
        print("  1. Disconnect Pico from USB")
        print("  2. Hold the BOOTSEL button")
        print("  3. Connect USB while holding BOOTSEL")
        print("  4. Release BOOTSEL button")
        print("  5. Pico should appear as RPI-RP2 drive")
    
    print("\n" + "=" * 60)
    return True


if __name__ == "__main__":
    test_pico_workflow()
