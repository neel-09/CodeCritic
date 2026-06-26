import re , subprocess , json , sys

# Headers that ship with the AVR/ESP32 core — never attempt to install these
CORE_HEADERS = {
    "Wire.h", "SPI.h", "Arduino.h", "EEPROM.h",
    "HardwareSerial.h", "avr/pgmspace.h", "math.h",
    "stdint.h", "string.h",
}

def _resolve_library_name(header: str) -> str | None:
    
    if header in CORE_HEADERS:
        return None

    base = header.replace(".h", "")
    result = subprocess.run(
        ["arduino-cli", "lib", "search", base, "--format", "json"],
        capture_output=True, text=True , encoding="utf-8" , errors="replace")
    
    if result.returncode != 0 or not result.stdout.strip():
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    libraries = data.get("libraries", [])
    if not libraries:
        return None

    # Prefer exact header match via provides_includes (most reliable)
    for lib in libraries:
        if header in lib.get("provides_includes", []):
            sys.stderr.write(f"Resolved {header} → {lib['name']} (provides_includes match)\n")
            return lib["name"]

    # No reliable match found — skip rather than install the wrong library
    sys.stderr.write(f"No reliable match for {header} — skipping\n")
    return None

def install_dependencies(sketch_code: str) -> list[str]:
    headers = re.findall(r'#include\s+[<"](.+?)[>"]', sketch_code)

    installed = []
    for header in headers:
        lib_name = _resolve_library_name(header)
        if lib_name is None:
            sys.stderr.write(f"Skipping core header: {header}\n")
            continue

        sys.stderr.write(f"Installing: {lib_name}\n")
        result = subprocess.run(
            ["arduino-cli", "lib", "install", lib_name],
            capture_output=True, text=True , encoding="utf-8" , errors="replace")
        
        if result.returncode != 0:
            sys.stderr.write(f"Install failed for {lib_name}: {result.stderr}\n")
        else:
            installed.append(lib_name)

    return installed
