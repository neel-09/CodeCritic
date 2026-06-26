from backend.state import State
import json,re

KNOWN_WOKWI_COMPONENTS = {
    # ── Microcontrollers ──────────────────────────────────────────────────
    "wokwi-arduino-uno",
    "wokwi-arduino-nano",
    "wokwi-arduino-mega",
    "wokwi-attiny85",
    "wokwi-esp32-devkit-v1",
    "wokwi-esp32-s2-devkit",
    "wokwi-esp32-s3-devkit",
    "wokwi-esp32-c3-devkit",
    "wokwi-pi-pico",
    "board-st-nucleo-c031c6",
    "board-st-nucleo-l031k6",
    "board-stm32-bluepill",

    # ── Sensors ───────────────────────────────────────────────────────────
    "wokwi-dht22",
    "wokwi-dht11",
    "wokwi-hc-sr04",
    "wokwi-pir-motion-sensor",
    "wokwi-ntc-temperature-sensor",
    "wokwi-ds18b20",
    "wokwi-mpu6050",
    "wokwi-photoresistor-sensor",
    "wokwi-gas-sensor",              # MQ2
    "wokwi-hx711",
    "wokwi-ds1307",
    "board-mfrc522",                 # RFID reader
    "board-bmp180",

    # ── Input Devices ─────────────────────────────────────────────────────
    "wokwi-pushbutton",
    "wokwi-pushbutton-6mm",
    "wokwi-slide-switch",
    "wokwi-dip-switch-8",
    "wokwi-membrane-keypad",
    "wokwi-analog-joystick",
    "wokwi-potentiometer",
    "wokwi-slide-potentiometer",
    "wokwi-ky-040",                  # Rotary encoder

    # ── LEDs ──────────────────────────────────────────────────────────────
    "wokwi-led",
    "wokwi-rgb-led",
    "wokwi-led-bar-graph",
    "wokwi-neopixel",                # WS2812 single LED
    "wokwi-led-ring",                # WS2812 ring
    "wokwi-led-strip",               # WS2812 strip
    "wokwi-led-matrix",              # WS2812 matrix
    "wokwi-nlsf595",                 # SPI tri-color LED driver

    # ── Displays ──────────────────────────────────────────────────────────
    "wokwi-lcd1602",
    "wokwi-lcd2004",
    "wokwi-ssd1306",
    "board-ssd1306",
    "board-grove-oled-sh1107",
    "wokwi-ili9341",                 # 2.8" TFT color display
    "wokwi-nokia-5110-screen",
    "wokwi-max7219-matrix",
    "wokwi-7segment",
    "wokwi-tm1637-7segment",

    # ── Motors ────────────────────────────────────────────────────────────
    "wokwi-servo",
    "wokwi-stepper-motor",
    "wokwi-biaxial-stepper",
    "wokwi-a4988",                   # stepper driver

    # ── Communication ─────────────────────────────────────────────────────
    "wokwi-ir-receiver",
    "wokwi-ir-remote",

    # ── Logic Gates & Shift Registers ─────────────────────────────────────
    "wokwi-74hc595",
    "wokwi-74hc165",
    "wokwi-not-gate",
    "wokwi-and-gate",
    "wokwi-or-gate",
    "wokwi-xor-gate",
    "wokwi-nand-gate",
    "wokwi-mux",
    "wokwi-flipflop-d",
    "wokwi-flipflop-dsr",

    # ── Passives & Other ──────────────────────────────────────────────────
    "wokwi-resistor",
    "wokwi-capacitor",
    "wokwi-buzzer",
    "wokwi-relay-module",
    "wokwi-ks2e-m-dc5",              # DPDT relay
    "wokwi-tilt-switch",
    "wokwi-soil-moisture-sensor",
    "wokwi-npn-transistor",
    "wokwi-pnp-transistor",
    "wokwi-microsd-card",
    "wokwi-logic-analyzer",
    "wokwi-clock-generator",
    "wokwi-breadboard",
    "wokwi-breadboard-half",
    "wokwi-breadboard-mini",
    "wokwi-text",
}

BOARD_COMPONENTS = {
    "wokwi-arduino-uno", "wokwi-arduino-nano", "wokwi-arduino-mega",
    "wokwi-esp32-devkit-v1"}

UTILITY_COMPONENTS = {
    "wokwi-logic-analyzer", "wokwi-microsd-card"}

SIGNAL_COMPONENTS = KNOWN_WOKWI_COMPONENTS - BOARD_COMPONENTS - UTILITY_COMPONENTS

import re

def normalize_wokwi_type(raw: str) -> str:
    raw = raw.lower().strip()

    # Strip numeric value + unit prefixes (e.g. "220ohm resistor" -> "resistor")
    raw = re.sub(r'[\d\.]+\s*(ohm|kohm|k|mohm|uf|nf|pf|v|mhz)\s*', '', raw).strip()

    # Exact aliases for components whose wokwi-id doesn't share a recognizable
    # substring with common phrasing (word-order swaps / abbreviation mismatches)
    ALIASES = {
        "resistor":      "wokwi-resistor",
        "led":           "wokwi-led",
        "pushbutton":    "wokwi-pushbutton",
        "button":        "wokwi-pushbutton",
        "rfidrc522":     "board-mfrc522",
        "rc522":         "board-mfrc522",
        "photoresistor": "wokwi-photoresistor-sensor",
        "ldr":           "wokwi-photoresistor-sensor",
        "dipswitch":     "wokwi-dip-switch-8",
        "multiplexer":   "wokwi-mux",
        "dflipflop":     "wokwi-flipflop-d",
        "dsrflipflop":   "wokwi-flipflop-dsr",
    }

    # Compact form: strip everything except letters/digits
    raw_compact = re.sub(r'[^a-z0-9]', '', raw)

    if raw in ALIASES:
        return ALIASES[raw]
    if raw_compact in ALIASES:
        return ALIASES[raw_compact]

    # Fuzzy match against KNOWN_WOKWI_COMPONENTS, longest id first so more
    # specific parts win (e.g. "rgb-led"/"led-ring" beat plain "led" for
    # "RGB LED"/"LED ring"; "tm1637-7segment" beats "7segment")
    for wokwi_id in sorted(KNOWN_WOKWI_COMPONENTS, key=len, reverse=True):
        core = re.sub(r'[^a-z0-9]', '', wokwi_id.replace("wokwi-", "").replace("board-", ""))
        if len(core) >= 4 and core in raw_compact:
            return wokwi_id

    return raw

def validate_circuit(state : State)-> tuple[bool, list[str]] :
    
    diag = state.get("diag_json")
        
    try:
        diagram = json.loads(diag)
    except (json.JSONDecodeError, TypeError) as e:
        return False, [str(e)]
    
    if diagram.get("version") != 1 :
        return False, ["Diagram version must be 1"]
        
    if diagram.get("parts") is None or type(diagram.get("parts")) != list or len(diagram.get("parts")) == 0 :
        return False, ["Diagram must have at least one part"]
    
    seen_ids = set()   
    warnings = [] 
    for part in diagram.get("parts"):

        if part.get("id") is None or type(part.get("id")) != str :
            return False, ["Part id must be a string"]
        
        if part.get("id") in seen_ids:
            return False, [f"Duplicate part id: {part.get('id')}"]
        seen_ids.add(part.get("id"))

        if part.get("type") is None or type(part.get("type")) != str :
            return False, ["Part type must be a string"]
        
        if part.get("top") is None or type(part.get("top")) not in (int, float) :
            return False, ["Part top must be an int or float"]
        
        if part.get("left") is None or type(part.get("left")) not in (int, float) :
            return False, ["Part left must be an int or float"]
        component_type = normalize_wokwi_type(part.get("type", ""))
        if component_type not in KNOWN_WOKWI_COMPONENTS:
            warnings.append(f"Unknown component type: {part.get('type')}, skipping")
            continue
        
        
    if diagram.get("connections") is None or type(diagram.get("connections")) != list :
        return False, ["Diagram must have at least one connection"]
        
    part_types = {p["id"]: p["type"] for p in diagram["parts"]}

    for conn in diagram.get("connections"):
        if not isinstance(conn, list) or len(conn) < 2:
            return False, ["Connection must be a list with at least 2 elements"]

        for pin_ref in conn[:2]:
            if ":" not in pin_ref:
                return False, [f"Invalid pin reference: {pin_ref}"]
            comp_id = pin_ref.split(":")[0]
            if comp_id not in seen_ids:
                return False, [f"Connection references unknown component: {comp_id}"]

        # Power-pin check — both endpoints, every connection
        errors = []
        POWER_INPUT_PINS = {"5V", "3.3V", "3V3", "VIN", "GND.1", "GND.2", "GND"}
        COMPONENT_POWER_PINS = {"VCC", "V+", "VIN", "PWR", "+", "VMOT", "VDD", "GND"} 
        PASSIVE_COMPONENTS = {"wokwi-resistor", "wokwi-capacitor"}
        for pin_ref, other_ref in [(conn[0], conn[1]), (conn[1], conn[0])]:
            source_pin = pin_ref.split(":")[1].split(".")[0].upper() if ":" in pin_ref else ""
            if source_pin in {"GND", "-"}:
                continue
            if source_pin not in POWER_INPUT_PINS:  # ← the missing gate
                continue
            other_parts = other_ref.split(":")
            other_id = other_parts[0]
            other_pin_name = other_parts[1] if len(other_parts) > 1 else ""
            other_type = part_types.get(other_id, "")

            if other_type in SIGNAL_COMPONENTS and other_type not in PASSIVE_COMPONENTS:
                if other_pin_name.upper() not in COMPONENT_POWER_PINS:
                    errors.append(
                        f"Power pin {pin_ref} connected directly to {other_type} '{other_id}' — use GPIO pin instead"
                    )
                    return False, errors

    return True, []
