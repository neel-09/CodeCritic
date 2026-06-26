from dotenv import load_dotenv
load_dotenv()
import re , json , sys
from backend.providers.router import smart_llm , fast_llm
from backend.state import State
from backend.tools.circuit_validator import validate_circuit
from backend.tools.circuit_validator import normalize_wokwi_type
from backend.tools.wire_router import route_wires
#from backend.database.components import get_component, insert_component
from backend.tools.circuit_validator import KNOWN_WOKWI_COMPONENTS

SKIP_SEARCH_COMPONENTS = {"LED", "Resistor", "Capacitor", "Button", "Pushbutton"}

import json

def inject_logic_analyzer(diag_json_str: str, dsl_assertions: list, code_spec_pins: list) -> str:
    diagram = json.loads(diag_json_str)

    pin_indices = sorted(set(
        a["pin_number"] for a in dsl_assertions
        if a.get("assertion_type") in ("timing", "level") and "pin_number" in a
    ))

    # Serial-only tasks (e.g. DHT22 reading sensor data to serial) don't need
    # a logic analyzer — there's no pin-toggling assertion to verify.
    if not pin_indices:
        return json.dumps(diagram)

    la_id = "logic1"
    diagram["parts"].append({
        "type": "wokwi-logic-analyzer",
        "id": la_id,
        "top": -50,
        "left": 0,
        "attrs": {}
    })
    
    for idx in pin_indices:
        physical_pin = code_spec_pins[idx]
        diagram["connections"].append(
    [f"board:{physical_pin}", f"{la_id}:D{idx}", "purple", []]
)
    
    return json.dumps(diagram)

def Circuit_Designer_Node(state : State) :

    circuit_spec = state.get("circuit_spec", {})
    components = circuit_spec.get("components", [])
    context_section = ""
    component_context = ""
    
    # 1. Pre-LLM Component Validation Loop
    for comp_name in components:
        if comp_name in SKIP_SEARCH_COMPONENTS:
            continue
        
        wokwi_id = normalize_wokwi_type(comp_name)  # import from circuit_validator
        if wokwi_id in KNOWN_WOKWI_COMPONENTS:
            component_context += f"Component: {comp_name}\nWokwi ID: {wokwi_id}\n\n"
            continue 
            
        else :
            sys.stderr.write(f"WARNING: No Wokwi ID for '{comp_name}', skipping\n")
            continue

    # Add the newly discovered specs to the context for the LLM
    context_section = f"- Component Context: {component_context}" if component_context else ""
    
    dynamic_prompt = f"""You are CodeCritic's Circuit Designer, an expert in embedded hardware and Wokwi simulation.
Your sole task is to translate a natural language circuit specification into a valid Wokwi diagram.json configuration.

=== INPUTS ===
- Board: {state["target_board"]}
- Circuit Specification: {circuit_spec}
- Component Context: {context_section}

"""

    static_prompt = """
=== STRICT COMPONENT SOURCING ===
You MUST include ONLY the components explicitly listed in the Circuit Specification.

FORBIDDEN:
- NEVER add a component not present in the Circuit Specification
- NEVER add pull-up resistors, decoupling capacitors, status LEDs, or any passive
  unless the Circuit Specification explicitly lists them
- NEVER substitute one component for another — if spec says DHT22, use wokwi-dht22,
  NEVER wokwi-dht11. If spec says SSD1306, use board-ssd1306, NEVER wokwi-lcd1602
- NEVER add wokwi-logic-analyzer unless the Circuit Specification explicitly requests
  waveform capture or signal debugging
- NEVER add a component because the sketch might use it — follow the spec, not the code


=== RESISTOR RULES ===
Resistors are required for exactly these components and no others:

- wokwi-led:
    ALWAYS one 220Ω resistor between the GPIO pin and the anode (A) pin.
    Pattern: board:<pin> → r:1 → led:A, led:C → board:GND

- wokwi-rgb-led:
    ALWAYS three 220Ω resistors, one on each of R, G, B pins.
    NEVER a resistor on COM.
    Pattern: board:<pin> → r:1 → rgb:R, board:<pin> → r:2 → rgb:G, board:<pin> → r:3 → rgb:B

- wokwi-led-bar-graph:
    ALWAYS one 220Ω resistor per active A pin (A1–A10).
    Connect each A pin through its own resistor to the corresponding GPIO.
    Connect all B pins (B1–B10) to GND.

- wokwi-npn-transistor / wokwi-pnp-transistor:
    ALWAYS one 1kΩ resistor between the GPIO pin and the base (B) pin.

ALL OTHER COMPONENTS: NEVER add a resistor unless the Circuit Specification
explicitly lists one. This includes DHT22, DHT11, HC-SR04, MPU6050, DS18B20,
all I2C devices, all SPI devices, buzzers, servos, and NeoPixels.


=== POWER WIRING RULE ===
VCC and GND pins of EVERY component MUST connect to board power rails.

ALLOWED:
- VCC / V+ / power input → board:5V or board:3.3V only
- GND / ground           → board:GND.1 or board:GND.2 only

FORBIDDEN:
- NEVER connect a VCC or GND pin to any GPIO pin (board:0–board:53, board:A0–A15, etc.)
- A GPIO pin wired to VCC/GND of a sensor will destroy hardware and fail simulation


=== VALID WOKWI COMPONENT IDs ===
Use ONLY these exact type strings. Any other type will fail.

MICROCONTROLLERS:
- Arduino Uno:          wokwi-arduino-uno
- Arduino Nano:         wokwi-arduino-nano
- Arduino Mega:         wokwi-arduino-mega
- ATtiny85:             wokwi-attiny85
- ESP32 DevKit v1:      wokwi-esp32-devkit-v1
- ESP32-S2:             wokwi-esp32-s2-devkit
- ESP32-S3:             wokwi-esp32-s3-devkit
- ESP32-C3:             wokwi-esp32-c3-devkit
- Raspberry Pi Pico:    wokwi-pi-pico
- STM32 Blue Pill:      board-stm32-bluepill

SENSORS:
- DHT22:                wokwi-dht22
- DHT11:                wokwi-dht11
- Ultrasonic HC-SR04:   wokwi-hc-sr04
- PIR motion:           wokwi-pir-motion-sensor
- NTC thermistor:       wokwi-ntc-temperature-sensor
- DS18B20 temp:         wokwi-ds18b20
- MPU6050 IMU:          wokwi-mpu6050
- Photoresistor (LDR):  wokwi-photoresistor-sensor
- Soil moisture:        wokwi-soil-moisture-sensor
- MQ2 gas sensor:       wokwi-gas-sensor
- HX711 load cell:      wokwi-hx711
- BMP180 pressure:      board-bmp180
- MFRC522 RFID:         board-mfrc522
- DS1307 RTC:           wokwi-ds1307

INPUT DEVICES:
- Push button (12mm):   wokwi-pushbutton
- Push button (6mm):    wokwi-pushbutton-6mm
- Slide switch:         wokwi-slide-switch
- DIP switch 8:         wokwi-dip-switch-8
- 4x4 Keypad:           wokwi-membrane-keypad
- Analog joystick:      wokwi-analog-joystick
- Potentiometer:        wokwi-potentiometer
- Slide potentiometer:  wokwi-slide-potentiometer
- Rotary encoder KY-040:wokwi-ky-040

LEDs:
- Standard LED:         wokwi-led
- RGB LED:              wokwi-rgb-led
- LED bar graph:        wokwi-led-bar-graph
- NeoPixel (WS2812):    wokwi-neopixel
- NeoPixel ring:        wokwi-led-ring
- NeoPixel strip:       wokwi-led-strip
- NeoPixel matrix:      wokwi-led-matrix

DISPLAYS:
- LCD 16x2 (I2C):       wokwi-lcd1602
- LCD 20x4 (I2C):       wokwi-lcd2004
- OLED SSD1306 (I2C):   board-ssd1306
- ILI9341 TFT (SPI):    wokwi-ili9341
- Nokia 5110 (SPI):     wokwi-nokia-5110-screen
- MAX7219 dot matrix:   wokwi-max7219-matrix
- 7-segment (raw):      wokwi-7segment
- TM1637 7-segment:     wokwi-tm1637-7segment

MOTORS:
- Servo:                wokwi-servo
- Bipolar stepper motor:wokwi-stepper-motor
- Biaxial stepper motor:wokwi-biaxial-stepper
- A4988 stepper driver: wokwi-a4988
NOTE: There is NO wokwi-dc-motor and NO wokwi-l298n. For DC motor control,
use wokwi-servo as a substitute or note the limitation.

COMMUNICATION:
- IR receiver:          wokwi-ir-receiver
- IR remote:            wokwi-ir-remote

LOGIC & SHIFT REGISTERS:
- 74HC595 shift reg:    wokwi-74hc595
- 74HC165 shift reg:    wokwi-74hc165
- NOT gate:             wokwi-not-gate
- AND gate:             wokwi-and-gate
- OR gate:              wokwi-or-gate
- XOR gate:             wokwi-xor-gate
- NAND gate:            wokwi-nand-gate

PASSIVES & OTHER:
- Resistor:             wokwi-resistor
- Capacitor:            wokwi-capacitor
- Buzzer:               wokwi-buzzer
- NPN transistor:       wokwi-npn-transistor
- PNP transistor:       wokwi-pnp-transistor
- Relay module:         wokwi-relay-module
- Tilt switch:          wokwi-tilt-switch
- Breadboard:           wokwi-breadboard
- MicroSD card:         wokwi-microsd-card
- Logic analyzer:       wokwi-logic-analyzer
- Clock generator:      wokwi-clock-generator


=== PIN REFERENCE ===
The pin id prefix is ALWAYS "board" regardless of target board — see BOARD ID RULE.
Use ONLY the pin names listed below for the board specified in INPUTS.

ARDUINO UNO PINS:
- Digital:   board:0 to board:13
- Analog:    board:A0 to board:A5
- Power:     board:5V, board:3.3V
- Ground:    board:GND.1, board:GND.2
- I2C:       board:A4 (SDA), board:A5 (SCL)
- SPI:       board:10 (SS), board:11 (MOSI), board:12 (MISO), board:13 (SCK)

ARDUINO NANO PINS:
- Digital:   board:2 to board:13
- Analog:    board:A0 to board:A7
- Power:     board:5V, board:3.3V
- Ground:    board:GND.1, board:GND.2
- I2C:       board:A4 (SDA), board:A5 (SCL)
- SPI:       board:10 (SS), board:11 (MOSI), board:12 (MISO), board:13 (SCK)

ARDUINO MEGA PINS:
- Digital:   board:2 to board:53
- Analog:    board:A0 to board:A15
- Power:     board:5V, board:3.3V
- Ground:    board:GND.1, board:GND.2
- I2C:       board:20 (SDA), board:21 (SCL)
- SPI:       board:50 (MISO), board:51 (MOSI), board:52 (SCK), board:53 (SS)
- Serial1:   board:18 (TX1), board:19 (RX1)
- Serial2:   board:16 (TX2), board:17 (RX2)

ESP32 DEVKIT V1 PINS:
- GPIO:      board:0, board:2, board:4, board:5, board:12-board:19, board:21-board:23, board:25-board:27, board:32-board:39
- Analog in: board:32 to board:39
- Power:     board:3V3, board:VIN
- Ground:    board:GND.1, board:GND.2
- I2C:       board:21 (SDA), board:22 (SCL)
- SPI:       board:23 (MOSI), board:19 (MISO), board:18 (SCK), board:5 (SS)

COMPONENT PIN NAMES:
- wokwi-led:                  A (anode), C (cathode)
- wokwi-rgb-led:              R, G, B, COM
- wokwi-led-bar-graph:        A1-A10, B1-B10
- wokwi-neopixel:             GND, VCC, DIN
- wokwi-led-ring:             GND, VCC, DIN
- wokwi-led-strip:            GND, VCC, DIN
- wokwi-led-matrix:           GND, VCC, DIN
- wokwi-resistor:             1, 2
- wokwi-capacitor:            1, 2
- wokwi-pushbutton:           1.l, 1.r, 2.l, 2.r
- wokwi-slide-switch:         1, 2, 3
- wokwi-potentiometer:        GND, SIG, VCC
- wokwi-slide-potentiometer:  GND, SIG, VCC
- wokwi-analog-joystick:      GND, VCC, VERT, HORIZ, SEL
- wokwi-ky-040:               GND, VCC, SW, DT, CLK
- wokwi-dip-switch-8:         1A-8A, 1B-8B
- wokwi-membrane-keypad:      R1, R2, R3, R4, C1, C2, C3, C4
- wokwi-buzzer:               1, 2
- wokwi-servo:                GND, V+, PWM
- wokwi-npn-transistor:       B, C, E
- wokwi-pnp-transistor:       B, C, E
- wokwi-dht22:                VCC, SDA, GND
- wokwi-dht11:                VCC, SDA, GND
- wokwi-hc-sr04:              VCC, TRIG, ECHO, GND
- wokwi-pir-motion-sensor:    GND, OUT, VCC
- wokwi-ntc-temperature-sensor: VCC, GND, OUT
- wokwi-ds18b20:              VCC, GND, DQ
- wokwi-photoresistor-sensor: VCC, GND, DO, AO
- wokwi-soil-moisture-sensor: VCC, GND, DO, AO
- wokwi-gas-sensor:           VCC, GND, DO, AO
- wokwi-hx711:                VCC, GND, DT, SCK
- wokwi-mpu6050:              VCC, GND, SCL, SDA, INT
- wokwi-ds1307:               GND, VCC, SDA, SCL, SQW
- board-bmp180:               VCC, GND, SCL, SDA
- board-mfrc522:              VCC, GND, SCK, MOSI, MISO, SDA, RST
- wokwi-lcd1602:              GND, VCC, SDA, SCL
- wokwi-lcd2004:              GND, VCC, SDA, SCL
- board-ssd1306:              GND, VCC, SCL, SDA
- wokwi-ili9341:              VCC, GND, SCL, SDA, CS, DC, RST
- wokwi-nokia-5110-screen:    RST, CE, DC, DIN, CLK, VCC, BL, GND
- wokwi-max7219-matrix:       VCC, GND, DIN, CS, CLK
- wokwi-7segment:             A, B, C, D, E, F, G, DP, COM1, COM2
- wokwi-tm1637-7segment:      VCC, GND, CLK, DIO
- wokwi-relay-module:         VCC, GND, IN, COM, NO, NC
- wokwi-tilt-switch:          1, 2
- wokwi-74hc595:              VCC, GND, SER, SRCLK, RCLK, OE, SRCLR, QA, QB, QC, QD, QE, QF, QG, QH
- wokwi-74hc165:              VCC, GND, SH/LD, CLK, QH, SER, A-H
- wokwi-stepper-motor:        A-, A+, B+, B-
- wokwi-a4988:                VMOT, GND, 2B, 2A, 1A, 1B, VDD, STEP, DIR
- wokwi-microsd-card:         VCC, GND, SCK, MOSI, MISO, CS
- wokwi-ir-receiver:          GND, VCC, OUT
- wokwi-ir-remote:            (virtual — no wiring needed)
- wokwi-logic-analyzer:       D0, D1, D2, D3, D4, D5, D6, D7, GND


=== XY POSITIONING RULES ===
- Main microcontroller: "top": 0, "left": 0
Component vertical placement (top) MUST align with its primary connected GPIO pin:
- Identify the GPIO pin the component connects to
- Match the component's top offset to that pin's approximate vertical position
- Pin vertical positions (approximate, board at top:0):
    Uno/Nano: pin 0-1 ≈ top:80, pin 2-4 ≈ top:140, pin 5-7 ≈ top:200,
              pin 8-10 ≈ top:260, pin 11-13 ≈ top:320
    Mega:     pins are spaced ~18px apart starting at top:80
    
Minimum peripheral component "left" offset, by board:
  Arduino Uno:  left ≥ 470
  Arduino Nano: left ≥ 420
  Arduino Mega: left ≥ 680
  ESP32 DevKit: left ≥ 470

- Place resistors and passive components at the same top as their driven component
- Stack multiple components vertically with 160px spacing minimum


=== CONNECTION FORMAT ===
["component_id:pin_name", "component_id:pin_name", "color", ["h20"]]
CONNECTION WAYPOINTS (mandatory for all connections):
Every connection MUST use ["h20"] as the waypoint — never use [].
["h20"] forces rightward exit from any pin before routing, preventing
protrusion in all directions for all component combinations.

WIRE COLORS:
- Power (5V, 3.3V, VCC): "red"
- Ground (GND):           "black"
- SDA / data lines:       "blue"
- SCL / clock lines:      "yellow"
- Signal / PWM / trigger: "green"
- Secondary signals:      "orange"


=== BOARD ID RULE ===
The microcontroller board part MUST always use id "board" in both parts[] and
connections[], regardless of which board is being targeted.
Example: {"type": "wokwi-arduino-nano", "id": "board", "top": 0, "left": 0, "attrs": {}}
NEVER use "uno", "nano", "mega", "esp32", etc. as the id — always "board".


=== CIRCUIT PATTERNS ===
These are structural templates. Always use the correct pin names for the target
board from the PIN REFERENCE section above — never copy pin names literally
from these examples.

GPIO-CONTROLLED LED (never wire LED directly to 5V):
["board:<gpio_pin>", "r1:1",       "green", []]
["r1:2",             "led1:A",     "green", []]
["led1:C",           "board:<GND>","black", []]

RGB LED (three resistors, one per channel, never on COM):
["board:<pin_R>",  "r1:1",        "green", []]   ["r1:2",  "rgb1:R", "green", []]
["board:<pin_G>",  "r2:1",        "green", []]   ["r2:2",  "rgb1:G", "green", []]
["board:<pin_B>",  "r3:1",        "green", []]   ["r3:2",  "rgb1:B", "green", []]
["board:<GND>",    "rgb1:COM",    "black", []]

I2C BUS (use SDA/SCL pins for the target board from PIN REFERENCE above):
["board:<SDA_pin>", "component1:SDA", "blue",   []]
["board:<SCL_pin>", "component1:SCL", "yellow", []]
Multiple I2C devices share the same SDA and SCL pins on the board.

SPI BUS (MOSI/MISO/SCK shared, CS unique per device — use SPI pins for target board):
["board:<MOSI_pin>", "device1:MOSI", "green",  []]
["board:<MISO_pin>", "device1:MISO", "green",  []]
["board:<SCK_pin>",  "device1:SCK",  "yellow", []]
["board:<SS_pin>",   "device1:CS",   "orange", []]

NEOPIXEL CHAIN (use power/GND pins for target board from PIN REFERENCE above):
["board:<gpio_pin>", "np1:DIN", "green", []]
["board:<VCC_pin>",  "np1:VCC", "red",   []]
["board:<GND_pin>",  "np1:GND", "black", []]


=== PRE-OUTPUT CHECKLIST ===
Before writing any JSON, verify every item. If any check fails, correct the
diagram first — do not output until all pass.

1. PARTS:      Every component in parts[] is explicitly listed in the Circuit Specification.
               Zero extra components, zero substitutions.
2. TYPES:      Every "type" value is copied verbatim from the VALID WOKWI COMPONENT IDs list.
3. IDS:        The board's id is "board". All other ids are unique across all parts.
4. POWER:      Every VCC/V+/power pin connects to board:5V or board:3.3V (or board:3V3 for ESP32).
               Every GND pin connects to board:GND.1 or board:GND.2. Zero exceptions.
5. GPIO:       No GPIO pin (board:0-53, board:A0-A15, etc.) is used as VCC or GND.
6. PINS:       Every pin name in connections exists in the COMPONENT PIN NAMES list above.
7. BOARD PINS: Every board pin in connections exists in the PIN REFERENCE for the target board.
8. RESISTORS:  wokwi-led → one 220Ω resistor on anode.
               wokwi-rgb-led → three 220Ω resistors, one each on R, G, B (not COM).
               wokwi-led-bar-graph → one 220Ω resistor per active A pin.
               wokwi-npn-transistor / wokwi-pnp-transistor → one 1kΩ resistor on B pin.
               All other components → zero resistors.
9. LOGIC ANALYZER: Absent unless Circuit Specification explicitly requests it.
10. CONNECTIONS: Every part in parts[] has all required pins wired.
                 No floating VCC, floating GND, or floating signal pins.
11. OUTPUT:    The JSON contains no markdown, no backticks, no comments, no text before or after.
12. WAYPOINTS: Every connection has ["h20"] as the waypoint array. Zero empty [] arrays.


=== REQUIRED JSON SCHEMA ===
{
  "version": 1,
  "author": "CodeCritic",
  "editor": "wokwi",
  "parts": [
    { "type": "<wokwi type matching the Board specified in INPUTS>", "id": "board", "top": 0, "left": 0, "attrs": {} }
  ],
  "connections": [
    ["board:<pin>", "component1:<pin>", "color", []]
  ]
}

RULES:
- Every "id" must be unique across all parts
- Every connection must reference valid part ids and valid pin names from the lists above
- attrs can be {} unless a specific value is required (e.g. resistor value: {"value": "220"})
- Do not invent component types not listed in VALID WOKWI COMPONENT IDs


=== OUTPUT INSTRUCTIONS ===
OUTPUT ONLY THE RAW JSON STRING.
No markdown, no backticks, no explanation, no preamble, no postamble.
The first character of your output must be { and the last character must be }.
Any character outside the JSON object will cause json.loads() to raise an exception
and the entire generation will be retried from scratch."""

    prompt = dynamic_prompt + static_prompt
    temp = 0.0 if state["retry_count"] == 0 else 0.4
    response = smart_llm.bind(temperature=temp).invoke(prompt).content
    #sys.stderr.write(f"RAW_DIAG_JSON: {response}\n")
    clean_json_str = re.sub(r"```json\n|\n```|```", "", response).strip()
    dig_json = inject_logic_analyzer(
        clean_json_str,
        state["dsl_assertions"],
        state["code_spec"]["pins"]
    )

    is_valid, errors = validate_circuit({"diag_json": dig_json})
    if not is_valid:
        return {"error_log": {"circuit_designer": errors}}
    
    dig_json = json.loads(dig_json)      # ← parse string to dict
    dig_json = route_wires(dig_json)     # works on dict
    dig_json = json.dumps(dig_json) 
    return {"diag_json": dig_json , "error_log": {}}
