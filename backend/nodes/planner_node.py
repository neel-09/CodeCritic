from dotenv import load_dotenv
load_dotenv()
from backend.state import State
from backend.dsl.schema import TimingAssertion, LevelAssertion, ProtocolAssertion, SerialAssertion
from backend.providers.router import tier1_groq , smart_llm
from backend.database.sessions_db import update_session
from pydantic import BaseModel, Field

class CodeSpec(BaseModel):
    pins: list[str]          # unique pins used, no duplicates
    signal_types: list[str]  # one per pin
    timing_ms: list[int]     # unique timing values only
    success_condition: str

class CircuitSpec(BaseModel):
    components: list[str]
    values: list[str]
    connections: list[str]

# class DSLAssertions(BaseModel):
#     assertions: list[TimingAssertion | LevelAssertion | ProtocolAssertion]

class PlannerOutput(BaseModel):
    code_spec: CodeSpec
    circuit_spec: CircuitSpec
    dsl_assertions: list[TimingAssertion | LevelAssertion | ProtocolAssertion | SerialAssertion]
    complexity_score: int = Field(default=5, description="Complexity score from 1 to 10")
    clarification_needed: bool
    clarification_question: str
#print(PlannerOutput.model_json_schema())
def Planner_Node(state : State):
    prompt = f"""You are CodeCritic's Planner. Convert a user request into a structured JSON specification.
Your output drives every downstream node — errors here propagate through the entire pipeline.

=== INPUTS ===
User request:  {state["user_prompt"]}
Target board:  {state["target_board"]}
Target FQBN:   {state["target_fqbn"]}


=== STRICT COMPONENT RULE ===
List ONLY the components physically required to fulfill the user request.

FORBIDDEN:
- NEVER list the microcontroller board (it is always implicit)
- NEVER list jumper wires or breadboard
- NEVER list a component not needed by the user request
- NEVER add a display, sensor, or extra LED not mentioned in the request
- Use the EXACT component name from SUPPORTED COMPONENTS below — no paraphrasing
  Wrong: "DHT22 temperature and humidity sensor module"
  Correct: "DHT22"


═══════════════════════════════════════════
BOARD PIN LIMITS — only assign pins from this list
═══════════════════════════════════════════
Arduino Uno:
  Digital: 0-13 | Analog: A0-A5 | PWM: 3, 5, 6, 9, 10, 11
  I2C: A4 (SDA), A5 (SCL) | SPI: 10 (SS), 11 (MOSI), 12 (MISO), 13 (SCK)

Arduino Nano:
  Digital: 0-13 | Analog: A0-A7 | PWM: 3, 5, 6, 9, 10, 11
  I2C: A4 (SDA), A5 (SCL) | SPI: 10 (SS), 11 (MOSI), 12 (MISO), 13 (SCK)

Arduino Mega:
  Digital: 0-53 | Analog: A0-A15 | PWM: 2-13, 44-46
  I2C: 20 (SDA), 21 (SCL) | SPI: 50 (MISO), 51 (MOSI), 52 (SCK), 53 (SS)
  Serial1: 18 (TX), 19 (RX)

ESP32 DevKit v1:
  GPIO: 0, 2, 4, 5, 12-19, 21-23, 25-27, 32-39
  Input-only (no output): 34, 35, 36, 39
  PWM: any output pin | I2C: 21 (SDA), 22 (SCL)
  SPI: 23 (MOSI), 19 (MISO), 18 (SCK), 5 (SS)
  Avoid at boot: 0, 2, 12, 15


═══════════════════════════════════════════
CODE SPEC RULES
═══════════════════════════════════════════
pins[]:
- List ONLY pins physically connected to a component in this circuit
- Example — DHT22 on pin 2: pins = ["2"]
- NEVER list all available board pins
- List each pin exactly ONCE — no duplicates
- For I2C/SPI components: do NOT include bus pins (SDA/SCL for I2C;
  MOSI/MISO/SCK/CS for SPI) — these are managed by Wire.begin()/SPI.begin()
- If the circuit has ONLY I2C/SPI components and no other GPIO:
  pins = [], signal_types = [], timing_ms = []

timing_ms:
- The ON or OFF duration in milliseconds (half-cycle), not total runtime
- "blink every second"    → timing_ms = [500]   (500ms ON, 500ms OFF)
- "pulse every 2 seconds" → timing_ms = [2000]
- NEVER double the user's stated period
- For PWM-driven continuous actuators (see STRATEGY C below), timing_ms = []
  since there is no fixed toggle period to record

success_condition:
- One sentence, single measurable behavior

signal_types: digital, analog, or PWM only

code_spec.behavior MUST describe every required behavior in the circuit:
- For each sensor:       "Read <measurement> from <ComponentType> on pin <N>"
- For each serial output:"Print <measurement> to Serial"
- For each GPIO output:  "Toggle <component> on pin <N> every <timing_ms>ms"
- For each PWM continuous actuator: "<Component> sweeps/fades continuously on pin <N>"

For combined tasks, both behavior AND success_condition must cover every behavior:
example :
  Correct:   "DHT22 reads temperature on pin 7 and prints to serial;
              LED toggles every 500ms on pin 13"
  Incorrect: "LED toggles every 500ms on pin 13"   ← omits sensor
  Incorrect: "Print temperature to serial"          ← omits GPIO


═══════════════════════════════════════════
SUPPORTED COMPONENTS — use these exact names
═══════════════════════════════════════════
Sensors:       DHT22, DHT11, HC-SR04, PIR motion sensor, NTC temperature sensor,
               DS18B20, MPU6050, photoresistor (LDR), gas sensor (MQ2),
               HX711 load cell amplifier, DS1307 RTC, RFID-RC522, BMP180

Input devices: pushbutton, slide switch, DIP switch, membrane keypad,
               analog joystick, potentiometer, slide potentiometer, rotary encoder (KY-040)

LEDs:          LED, RGB LED, LED bar graph, NeoPixel, LED ring, LED strip, LED matrix

Displays:      LCD1602, LCD2004, SSD1306 OLED, ILI9341 TFT, Nokia 5110 screen,
               MAX7219 matrix, 7-segment display, TM1637 7-segment

Motors:        servo motor, stepper motor, A4988 stepper driver

Communication: IR receiver, IR remote

Logic/Shift:   74HC595, 74HC165, NOT/AND/OR/XOR/NAND gate, multiplexer, D flip-flop

Passives:      resistor, capacitor, buzzer, relay module, tilt switch,
               soil moisture sensor, NPN transistor, PNP transistor, microSD card


═══════════════════════════════════════════
CIRCUIT SPEC RULES
═══════════════════════════════════════════
- Use exact component names from SUPPORTED COMPONENTS
- List every component including resistors
- The board is always implicit — never include it
- Wires are implicit — never include them
- Resistor calculation: R = (Vsupply - Vforward) / Iforward
  LED defaults: Vf = 2.0V, If = 20mA → R = (5 - 2) / 0.02 = 150Ω → round up to 220Ω
- For GPIO-controlled components, the GPIO pin is the source — NEVER 5V directly
- connections[]: list signal connections only, not power/GND
- Every component needs an explicit GND connection
- VCC/GND MUST connect to board power pins (board:5V, board:3.3V, board:GND.1)
  NEVER to GPIO pins
- connections[] MUST distinguish power from signal connections:
  - Power:  "board:5V -> component.VCC"  or  "board:GND -> component.GND"
    NEVER:  "pin<N> -> component.VCC"   or  "pin<N> -> component.GND"
  - Signal: "pin<N> -> component.SIGNAL_PIN"

Every component must have exactly one power connection and one GND connection
using board power rails — never a GPIO pin.


═══════════════════════════════════════════
DSL ASSERTION RULES
═══════════════════════════════════════════

STEP 1 — CHOOSE STRATEGY (apply exactly one rule):

  If success_condition describes a PWM-driven continuous actuator             → STRATEGY C
    (servo sweep, analogWrite fade/dim, continuous motor speed control —
     check this FIRST, before A/B, since these tasks also mention a pin/output)
  If success_condition describes pin/output/LED/buzzer/relay/fixed-angle servo → STRATEGY A
  If success_condition describes printed/serial sensor readings               → STRATEGY B
  If success_condition describes BOTH A and B independently                   → STRATEGY A + B
    (MUST include assertions from both — never reduce a combined task to one strategy)


STEP 2 — BUILD ASSERTIONS

──────────────────────────────────────────
STRATEGY A — GPIO output timing
Use: TimingAssertion + LevelAssertion (always together)

pin_number RULE (critical):
  pin_number = index of the toggling pin within code_spec.pins[]  (0-based)
  Example 1: pins=["13"],       pin 13 toggles → pin_number = 0
  Example 2: pins=["7","13"],   pin 13 toggles → pin_number = 1
  Example 3: pins=["2","7","13"], pin 13 toggles → pin_number = 2
  NEVER use the physical GPIO number as pin_number

TimingAssertion fields:
  expected_period_ms = timing_ms value exactly (the half-cycle, do NOT double it)
    Example: timing_ms=[500] → expected_period_ms = 500.0
  tolerance_ms       = max(5.0,  expected_period_ms * 0.10)
    Example: expected_period_ms=500  → tolerance_ms = 50.0
    Example: expected_period_ms=2000 → tolerance_ms = 200.0
  min_toggles        = 2  (always)
  pin_number         = index as computed above

LevelAssertion fields:
  timestamp_ms  = timing_ms + (timing_ms / 2)
    Example: timing_ms=500  → timestamp_ms = 500 + 250 = 750.0
    Example: timing_ms=1000 → timestamp_ms = 1000 + 500 = 1500.0
  expected_level:
  "HIGH" if the pin initialises LOW (standard Arduino GPIO default)
  "LOW"  if the pin initialises HIGH (active-low logic, relay, etc.)
  When in doubt: "HIGH" — standard blink always starts LOW
  pin_number     = same index as TimingAssertion for this pin

──────────────────────────────────────────
STRATEGY B — sensor → serial output
Use: SerialAssertion ONLY

DO NOT add TimingAssertion/LevelAssertion for a sensor's data pin — it carries
microsecond-scale protocol bursts, not a simple periodic toggle.

expected_patterns RULES:
  - Include the bare measurement noun(s) from success_condition only
  - STRIP all punctuation, colons, units, numbers, and adjectives
  - One entry per distinct measurement
  - Correct:   ["temperature"]          (success_condition mentions temperature)
  - Correct:   ["temperature","humidity"] (DHT22 printing both)
  - Correct:   ["distance"]             (HC-SR04)
  - WRONG:     ["Temperature:"]         (has colon)
  - WRONG:     ["Temp: 25.0 C"]         (has value and unit)
  - WRONG:     ["distance cm"]          (has unit)

SerialAssertion fields:
  assertion_type    = "serial"
  expected_patterns = [bare noun(s) as described above]
  max_nan_ratio     = 0.5
  min_lines         = 1

──────────────────────────────────────────
STRATEGY C — PWM-driven continuous actuators
Use: NO assertions — dsl_assertions = []

These produce variable pulse-width or duty-cycle signals, not a fixed-period
square wave or serial output. Neither STRATEGY A nor B applies. This is NOT
a case requiring clarification — it is a known, deterministic pattern with
no ambiguity to resolve.

Triggers for STRATEGY C:
  - Servo.write() sweeping continuously through a range of angles
    (a servo moving to ONE fixed angle and staying there is NOT continuous —
     that case has no meaningful assertion either, also use STRATEGY C)
  - analogWrite() used for fading/dimming an LED or actuator, not a fixed duty cycle
  - Continuous motor speed control via PWM
  - Any output whose signal varies continuously rather than toggling between
    two fixed states at a fixed period

dsl_assertions = []

Verification for these tasks is compile-only — pass_score reflects successful
compilation and valid circuit wiring, not a behavioral assertion. This is the
same honest-uncertainty treatment as structurally unverifiable input devices.


═══════════════════════════════════════════
CLARIFICATION RULES
═══════════════════════════════════════════
Set clarification_needed = true ONLY when ALL of these are true:
  - A required design decision cannot be reasonably defaulted
  - The ambiguity would materially change the circuit or pin assignment

Valid reasons to ask:
  a) Target pin is ambiguous AND multiple valid options change the circuit
  b) A sensor threshold is required for the logic but not specified
  c) Number of identical components is unspecified and changes wiring materially

NEVER ask about:
  - LED color, resistor value, wire color
  - Timing when a reasonable default exists (default: 1000ms)
  - Board-level decisions already specified in INPUTS
  - Assertion strategy for PWM-driven continuous actuators (servo sweep, fade,
    speed control) — always use STRATEGY C with dsl_assertions = [], never ask
  - Whether a task is verifiable in simulation — if no assertion strategy
    cleanly fits, default to STRATEGY C (no assertions) rather than asking

If clarification_needed = true:  ask exactly ONE specific question in clarification_question
If clarification_needed = false: set clarification_question = ""


═══════════════════════════════════════════
PRE-OUTPUT CHECKLIST
═══════════════════════════════════════════
Verify every item before writing the JSON. Correct any failure before outputting.

1.  COMPONENTS:     Every component in circuit_spec.components is required by the
                    user request. Zero extra components. Names match SUPPORTED COMPONENTS.
2.  BOARD:          The microcontroller board does not appear in circuit_spec.components.
3.  PINS:           Only pins physically used by components are listed in code_spec.pins.
                    No I2C/SPI bus pins. No duplicates. All pins exist on the target board.
4.  TIMING:         timing_ms is the half-cycle (toggle interval), NOT the full period.
                    Empty [] for STRATEGY C (PWM continuous actuators).
5.  STRATEGY:       Correct strategy chosen per STEP 1 rule, in priority order
                    (check STRATEGY C trigger BEFORE defaulting to A or B).
                    Combined A+B task → both strategies present.
6.  pin_number:     Computed as index within code_spec.pins[], not the physical GPIO number.
7.  TIMING MATH:    expected_period_ms = timing_ms exactly.
                    tolerance_ms = max(5.0, expected_period_ms * 0.10).
                    timestamp_ms = timing_ms + (timing_ms / 2).
8.  PATTERNS:       expected_patterns contains only bare measurement nouns.
                    No colons, units, numbers, or punctuation.
9.  POWER:          All VCC/GND connections target board power pins, never GPIO pins.
10. NO FALSE CLARIFICATION: If the only ambiguity is "what assertion strategy
                    fits this behavior," that is never grounds for clarification —
                    apply STRATEGY C instead.
11. OUTPUT:         JSON only. First character is {{. Last character is }}.
                    No markdown, no backticks, no explanation, no extra keys.


═══════════════════════════════════════════
REQUIRED OUTPUT FORMAT
═══════════════════════════════════════════
Return ONLY this JSON structure. No markdown, no backticks, no explanation.
First character must be {{ and last character must be }}.

STRATEGY A example (GPIO output):
{{
  "code_spec": {{
    "behavior": "<one sentence>",
    "pins": ["13"],
    "signal_types": ["digital"],
    "timing_ms": [500],
    "success_condition": "LED toggles every 500ms on pin 13",
    "complexity_score": 3
  }},
  "circuit_spec": {{
    "components": ["LED", "resistor"],
    "values": ["220ohm"],
    "connections": [
      "pin13 -> r1 -> led1.A",
      "led1.C -> GND"
    ]
  }},
  "dsl_assertions": [
    {{
      "assertion_type": "timing",
      "pin_number": 0,
      "expected_period_ms": 500.0,
      "tolerance_ms": 50.0,
      "min_toggles": 2
    }},
    {{
      "assertion_type": "level",
      "pin_number": 0,
      "timestamp_ms": 750.0,
      "expected_level": "HIGH"
    }}
  ],
  "clarification_needed": false,
  "clarification_question": ""
}}

STRATEGY B example (sensor → serial):
  dsl_assertions = [
    {{
      "assertion_type": "serial",
      "expected_patterns": ["temperature", "humidity"],
      "max_nan_ratio": 0.5,
      "min_lines": 1
    }}
  ]

STRATEGY A + B example (combined — sensor AND independently toggling GPIO):
  dsl_assertions = [
    {{
      "assertion_type": "serial",
      "expected_patterns": ["temperature"],
      "max_nan_ratio": 0.5,
      "min_lines": 1
    }},
    {{
      "assertion_type": "timing",
      "pin_number": 1,
      "expected_period_ms": 1000.0,
      "tolerance_ms": 100.0,
      "min_toggles": 2
    }},
    {{
      "assertion_type": "level",
      "pin_number": 1,
      "timestamp_ms": 1500.0,
      "expected_level": "HIGH"
    }}
  ]

For N independently toggling GPIO pins, add one TimingAssertion + LevelAssertion
pair per pin, each with its own pin_number index and timing values.
Example: pins=["9","13"], LED on pin 9 at 200ms, LED on pin 13 at 500ms →
  timing assertion: pin_number=0, expected_period_ms=200.0, tolerance_ms=20.0
  level  assertion: pin_number=0, timestamp_ms=300.0,  expected_level="HIGH"
  timing assertion: pin_number=1, expected_period_ms=500.0, tolerance_ms=50.0
  level  assertion: pin_number=1, timestamp_ms=750.0,  expected_level="HIGH"

STRATEGY C example (PWM-driven continuous actuator — servo sweep):
{{
  "code_spec": {{
    "behavior": "Servo sweeps continuously from 0 to 180 degrees on pin 9",
    "pins": ["9"],
    "signal_types": ["PWM"],
    "timing_ms": [],
    "success_condition": "Servo sweeps continuously between 0 and 180 degrees on pin 9",
    "complexity_score": 3
  }},
  "circuit_spec": {{
    "components": ["servo motor"],
    "values": [],
    "connections": [
      "pin9 -> servo1.PWM"
    ]
  }},
  "dsl_assertions": [],
  "clarification_needed": false,
  "clarification_question": ""
}}

Display-only circuits (OLED, LCD with no sensor, no GPIO toggle):
  Use STRATEGY B with expected_patterns derived from the text shown on the display.
  Example: "Hello World on OLED" → expected_patterns = ["hello"] or ["world"]

complexity_score guide:
  1-3: single component, simple GPIO
  4-6: multiple components, basic protocols (I2C, SPI)
  7-10: multiple sensors, custom logic, UART, interrupt-driven"""

    response = smart_llm.with_structured_output(PlannerOutput).invoke(prompt)
    if response.clarification_needed :

        return {"clarification_needed": True, "clarification_question": response.clarification_question}    
    
    else :
        update_session(
            session_id=state["session_id"],
            final_status="in_progress",
            iteration_count=0,
            pass_score=0.0,
            error_log={},
            complexity_score=response.complexity_score
        )

        return {
            "code_spec": response.code_spec.model_dump(),
            "circuit_spec": response.circuit_spec.model_dump(),
            "complexity_score": response.complexity_score,
            "dsl_assertions": [a.model_dump() for a in response.dsl_assertions]
        }