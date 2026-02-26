"""Arduino 编译模块"""
import re
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from .errors import BuildError, ConfigurationError
from .models import CompileResult
from .board_detector import BoardDetector

log = logging.getLogger("arduino_client")

_HEADER_RE = re.compile(r":\s*fatal error:\s*(\S+\.h):\s*No such file or directory")

HEADER_TO_LIB = {
    "U8g2lib.h": "U8g2",
    "U8x8lib.h": "U8g2",
    "Adafruit_SSD1306.h": "Adafruit SSD1306",
    "Adafruit_GFX.h": "Adafruit GFX Library",
    "RTClib.h": "RTClib",
    "Wire.h": None,
    "SPI.h": None,
    "Servo.h": "Servo",
    "DHT.h": "DHT sensor library",
    "Adafruit_NeoPixel.h": "Adafruit NeoPixel",
    "FastLED.h": "FastLED",
    "LiquidCrystal_I2C.h": "LiquidCrystal I2C",
    "SD.h": "SD",
    "ArduinoJson.h": "ArduinoJson",
    "WiFi.h": None,
    "PubSubClient.h": "PubSubClient",
    "Stepper.h": "Stepper",
    "IRremote.h": "IRremote",
    "OneWire.h": "OneWire",
    "DallasTemperature.h": "DallasTemperature",
}

LIB_NAME_NORMALIZE = {
    "u8g2": "U8g2",
    "adafruit_ssd1306": "Adafruit SSD1306",
    "adafruit ssd1306": "Adafruit SSD1306",
    "adafruit_gfx": "Adafruit GFX Library",
    "adafruit gfx library": "Adafruit GFX Library",
    "adafruit gfx": "Adafruit GFX Library",
    "rtclib": "RTClib",
    "dht": "DHT sensor library",
    "dht sensor library": "DHT sensor library",
    "fastled": "FastLED",
    "neopixel": "Adafruit NeoPixel",
    "adafruit neopixel": "Adafruit NeoPixel",
    "liquidcrystal_i2c": "LiquidCrystal I2C",
    "liquidcrystal i2c": "LiquidCrystal I2C",
    "arduinojson": "ArduinoJson",
    "irremote": "IRremote",
    "onewire": "OneWire",
    "dallastemperature": "DallasTemperature",
    "pubsubclient": "PubSubClient",
    "servo": "Servo",
    "stepper": "Stepper",
    "sd": "SD",
    "wire": None,
    "spi": None,
}


class Builder:
    """Arduino 项目编译器"""
    
    def __init__(self, detector: Optional[BoardDetector] = None):
        self.detector = detector or BoardDetector()

    # ------------------------------------------------------------------
    #  库安装
    # ------------------------------------------------------------------

    def install_libraries(self, lib_names: List[str]) -> List[Tuple[str, bool, str]]:
        """通过 arduino-cli 安装一组库，返回 [(名称, 是否成功, 消息)]。"""
        results = []
        for raw_name in lib_names:
            name = LIB_NAME_NORMALIZE.get(raw_name.lower().strip(), raw_name.strip())
            if name is None:
                results.append((raw_name, True, "内置库，无需安装"))
                continue
            log.info("安装库: %s", name)
            print(f"  [库] 安装 {name} ...")
            try:
                proc = subprocess.run(
                    [self.detector.cli_path, "lib", "install", name],
                    capture_output=True, text=True, timeout=120,
                    encoding="utf-8", errors="replace",
                )
                ok = proc.returncode == 0
                msg = ((proc.stdout or "") + (proc.stderr or "")).strip()
                if ok:
                    log.info("库安装成功: %s", name)
                    print(f"  [库] {name} 安装成功")
                else:
                    log.warning("库安装失败: %s — %s", name, msg[:200])
                    print(f"  [库] {name} 安装失败: {msg[:200]}")
                results.append((name, ok, msg))
            except Exception as e:
                log.warning("库安装异常: %s — %s", name, e)
                print(f"  [库] {name} 安装异常: {e}")
                results.append((name, False, str(e)))
        return results

    @staticmethod
    def detect_missing_libraries(build_output: str) -> List[str]:
        """从编译输出中提取缺失的头文件并映射到库名。"""
        missing = []
        for match in _HEADER_RE.finditer(build_output):
            header = match.group(1)
            lib = HEADER_TO_LIB.get(header)
            if lib is None and header not in HEADER_TO_LIB:
                lib = header.replace(".h", "")
            if lib and lib not in missing:
                missing.append(lib)
        return missing

    @staticmethod
    def extract_error_lines(build_output: str, max_chars: int = 1500) -> str:
        """从完整编译输出中提取关键错误行，避免被无关信息挤掉。"""
        error_lines = []
        for line in build_output.splitlines():
            lower = line.lower()
            if "error:" in lower or "fatal error:" in lower or "undefined reference" in lower:
                error_lines.append(line.strip())
        if error_lines:
            return "\n".join(error_lines)[:max_chars]
        return build_output[:max_chars]

    # ------------------------------------------------------------------
    #  编译
    # ------------------------------------------------------------------

    def compile_sketch(
        self,
        sketch_path: Path,
        fqbn: str,
        build_path: Optional[Path] = None
    ) -> CompileResult:
        """编译 Arduino 工程
        
        Args:
            sketch_path: 工程文件 (.ino) 路径或所在目录
            fqbn: 板卡 FQBN
            build_path: 可选，编译输出目录（默认 sketch_dir/build）
            
        Returns:
            编译结果
        """
        try:
            # 若传入的是 .ino 文件，取其所在目录
            if sketch_path.is_file():
                sketch_dir = sketch_path.parent
            else:
                sketch_dir = sketch_path
            
            # 未指定时使用 sketch_dir/build
            if build_path is None:
                build_path = sketch_dir / "build"
            
            # 创建编译目录
            build_path.mkdir(parents=True, exist_ok=True)
            
            log.info(f"编译工程: {sketch_dir} for {fqbn}")
            
            # 使用指定 build 路径编译
            result = subprocess.run(
                [
                    self.detector.cli_path, "compile",
                    "--fqbn", fqbn,
                    "--build-path", str(build_path),
                    str(sketch_dir)
                ],
                capture_output=True,
                text=True,
                timeout=600,
                encoding="utf-8",
                errors="replace",
            )
            
            success = result.returncode == 0
            output = (result.stdout or "") + (result.stderr or "")
            
            if success:
                log.info(f"编译成功: {sketch_dir}")
            else:
                log.error(f"编译失败: {sketch_dir}")
            
            errors = []
            if not success:
                # 解析错误信息
                for line in output.split('\n'):
                    if 'error:' in line.lower():
                        errors.append(line.strip())
                        log.debug(f"编译错误: {line.strip()}")
            
            return CompileResult(
                success=success,
                output=output,
                errors=errors if errors else None,
                build_path=str(build_path) if success else None
            )
        except subprocess.TimeoutExpired:
            log.error("编译超时")
            raise BuildError("编译超时")
        except Exception as e:
            log.error(f"编译错误: {e}", exc_info=True)
            raise BuildError(f"编译错误: {e}")
