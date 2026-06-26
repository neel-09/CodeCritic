from dotenv import load_dotenv
load_dotenv()
import sys , re
from backend.state import State
from backend.providers.router import fast_llm
from backend.tools.comment_stripper import strip_comments

def Coder_Node(state : State):

    if state["compile_error"] == [] :

        prompt = f"""You are an expert Arduino programmer working inside CodeCritic, an autonomous EDA pipeline.
Your sole task is to write a complete, immediately-compilable Arduino sketch from the specification below.

=== INPUTS ===
- Board:              {state["target_board"]}
- FQBN:               {state["target_fqbn"]}
- Code Specification: {state["code_spec"]}
- DSL Assertions:     {state.get("dsl_assertions", [])}
- Libraries:          {state.get("lib_txt", "")}
- Circuit Specification: {state["circuit_spec"]}


=== STRICT COMPONENT RULE ===
You MUST implement ONLY the components and features listed in Code Specification.

FORBIDDEN:
- NEVER #include a library for a component not listed in Code Specification
- NEVER add a display (OLED, LCD, TFT) unless Code Specification explicitly lists one
- NEVER add a sensor, actuator, or peripheral not present in Code Specification
- NEVER substitute one component for another:
    if spec says DHT22   → use DHT22,   NEVER DHT11
    if spec says HC-SR04 → use HC-SR04, NEVER a different ultrasonic library
    if spec says SSD1306 → use Adafruit_SSD1306, NEVER a different display type
- NEVER add Serial.print statements for sensors not in Code Specification
- NEVER add boilerplate, demo code, or "nice to have" features
- Every component listed in Circuit Specification MUST have a corresponding
  #include and a complete working implementation — never a placeholder,
  never a comment, never a hardcoded value standing in for a sensor read


=== STRICT PIN RULE ===
- Use ONLY the pin numbers defined in code_spec.pins for every digitalWrite(),
  digitalRead(), analogRead(), analogWrite(), pinMode(), and library .begin() call
- NEVER invent a pin number not listed in Code Specification
- NEVER call pinMode(), digitalRead(), or digitalWrite() on any pin used by
  a library via Wire.begin(), SPI.begin(), or a sensor/display .begin() call
  (I2C pins SDA/SCL and SPI pins MOSI/MISO/SCK/SS are managed by their libraries)


=== STRICT SENSOR RULE ===
- ALWAYS use the actual sensor library to read real values
- NEVER use hardcoded, placeholder, simulated, or random sensor values
- NEVER write lines like: float t = 25.0; or int dist = 100;
- A sketch with hardcoded sensor values is WRONG regardless of whether it compiles
- If the sensor read fails (isnan, timeout, etc.), print an error to Serial and
  return early — NEVER fall through with a fake value


=== CODE STRUCTURE RULES ===
File layout — in this exact order:
  1. Board/FQBN comment: // Board: {state["target_board"]}
  2. All #include statements
  3. All #define constants
  4. All global variable and object declarations
  5. setup() function
  6. loop() function
  7. Any helper functions

Globals:
- Every variable or object used in both setup() and loop() MUST be declared globally
- NEVER declare a sensor object, pin constant, or state variable inside setup() or loop()

Timing:
- When the sketch has two or more concurrent periodic tasks (e.g. blink LED every
  1 s AND read sensor every 2 s), use millis()-based non-blocking timing for ALL tasks
- NEVER use delay() when multiple independent timed tasks exist in the same loop()
- A single-task sketch (blink only, or serial print only) may use delay()

Board-specific:
- NEVER use while (!Serial) on Arduino Uno, Nano, or Mega — these boards have no
  native USB and this line blocks forever with no serial monitor attached
- while (!Serial) is only permitted for boards with native USB (Arduino Leonardo,
  Micro, Due, or any ESP32/ESP8266 variant)


=== SERIAL OUTPUT RULES ===
DSL Assertions: {state.get("dsl_assertions", [])}

- If any assertion has type "serial", Serial.print/println output MUST include
  each word in expected_patterns as a label before the value, case-insensitive match.
  Example: if expected_patterns includes "Temperature", write:
    Serial.print("Temperature: ");
    Serial.println(t);
- If the sketch includes a display (OLED/LCD) AND a serial assertion exists,
  mirror ALL displayed values to Serial.print/println with the same labels
- Serial.begin() baud rate: use 9600 unless Code Specification states otherwise
- NEVER add Serial.print statements for data not required by dsl_assertions


=== LIBRARY RULES ===
- If lib_txt specifies a library, use it — do not substitute an alternative
- Use the library's standard, documented API only
- Do not call internal or undocumented library methods
- Install order does not matter; assume all listed libraries are available

COMMENT RULES — DEFAULT TO ZERO COMMENTS:
Comments are FORBIDDEN by default. The sketch must compile and be understood
from code alone, not from narration.

ONLY these exact comments are permitted, nothing else:
  // Board: <board name>
  // FQBN: <fqbn>

EVERYTHING ELSE IS FORBIDDEN, including:
  - Comments explaining what a line does ("// read temperature", "// toggle LED")
  - Comments narrating assertion logic or timing math
  - Comments showing worked examples or step traces ("// 0ms: LOW, 500ms: HIGH")
  - Comments justifying a design decision ("// using millis() for non-blocking timing")
  - Comments on #include lines
  - Comments inside setup() or loop()
  - Comments above function definitions
  - TODO comments, placeholder comments, or comments of any kind

If you feel the urge to write a comment to explain code, that is a signal the
code itself should be clearer — rename the variable instead of commenting it.

NEVER leave an empty conditional block (if/else with no body) as a result of
unresolved reasoning. Either implement the branch or remove it entirely.

=== PRE-OUTPUT CHECKLIST ===
Before writing any code, verify every item. If any check fails, correct the
sketch first — do not output until all pass.

1. COMPONENTS:  Every #include corresponds to a component in Code Specification.
                Zero libraries for components not in the spec.
2. SENSOR TYPE: The exact sensor model from Code Specification is used.
                No substitutions.
3. PIN NUMBERS: Every pin used matches a pin defined in code_spec.pins.
                No invented pin numbers.
4. REAL VALUES: Zero hardcoded sensor values. All readings come from library calls.
5. GLOBALS:     Every object and variable used across functions is declared globally.
6. TIMING:      millis() used if two or more concurrent periodic tasks exist.
7. SERIAL WAIT: while (!Serial) absent for Uno, Nano, Mega.
8. SERIAL OUT:  All expected_patterns from serial assertions present as labels.
9. SCOPE:       No #include, object declaration, or pin define inside setup()/loop().
10. OUTPUT:     First character is // or #. No markdown, no backticks, no explanation.


=== OUTPUT INSTRUCTIONS ===
OUTPUT ONLY RAW .ino CODE.
No markdown code blocks, no backticks, no explanation before or after the code.
The very first character must be // or #.
Any character outside the sketch will cause the compiler to fail."""
        
        response = fast_llm.invoke(prompt)
        sketch_ino = re.sub(r"```(?:cpp|ino|c\+\+)?\n|\n```|```", "", response.content).strip()
        sketch_ino = strip_comments(sketch_ino)
        return {"sketch_ino": sketch_ino}
    
    elif state["simulation_feedback"] :

        sys.stderr.write(f"SIMULATION_FEEDBACK: {state.get('simulation_feedback', 'NONE')}\n")
        sys.stderr.write(f"COMPILE_ERROR: {state['compile_error']}\n")

        prompt = f"""You are fixing an Arduino sketch for {state["target_board"]} that compiled
successfully but failed simulation verification.
 
=== ORIGINAL SKETCH ===
{state["sketch_ino"]}
 
=== CODE SPECIFICATION ===
{state["code_spec"]}
 
=== DSL ASSERTIONS ===
{state.get("dsl_assertions", [])}
 
=== SIMULATION FEEDBACK ===
{state["simulation_feedback"]}

- Circuit Specification:
{state["circuit_spec"]}
 
 
=== FIX RULES BY FAILURE TYPE ===
 
SERIAL ASSERTION FAILURE ("missing expected patterns: [X]"):
- Add Serial.print("X: ") immediately before the relevant value's Serial.println()
- The label must contain every word in expected_patterns (case-insensitive match)
- Do NOT change sensor read logic — only add or correct the Serial.print label
 
TIMING ASSERTION FAILURE (toggle period incorrect):
- Adjust only the interval constant that controls the failing pin's toggle frequency
- Do NOT touch unrelated timing values or delay() calls
 
LEVEL ASSERTION FAILURE (pin never HIGH or never LOW):
- Verify pinMode() is OUTPUT for the pin
- Verify digitalWrite() targets the exact pin number from code_spec.pins
- Do NOT change any other pin
 
 
=== STRICTLY FORBIDDEN ===
- NEVER hardcode a sensor value to make a serial assertion pass
  Wrong:   float t = 25.0;
  Correct: float t = dht.readTemperature();
- NEVER add a component, library, or feature not in Code Specification
- NEVER add a new #include not present in the original sketch
- NEVER change pin numbers
- NEVER change the sensor or component type
- NEVER rewrite or restructure sections of the sketch unrelated to the failure
 
If your fix requires changing how a behavior is implemented, REMOVE the
previous implementation entirely — never leave two competing implementations
of the same behavior in the same sketch.
 
=== PRE-OUTPUT CHECKLIST ===
1. Root cause of each failed assertion identified and directly fixed
2. Zero hardcoded sensor values — all readings from library calls
3. No new #include added, no new component introduced
4. All pin numbers identical to the original sketch
5. Serial labels contain all words from expected_patterns
6. Working sections of the sketch are byte-for-byte identical to the original
7. First character is // or #. No markdown, no backticks, no explanation.
 
 
OUTPUT ONLY THE COMPLETE FIXED .ino CODE.
No markdown, no backticks, no explanation. First character must be // or #."""
        temp = 0.0 if state["retry_count"] == 0 else 0.4
        response = fast_llm.bind(temperature=temp).invoke(prompt)
        sketch_ino = re.sub(r"```(?:cpp|ino|c\+\+)?\n|\n```|```", "", response.content).strip()
        sketch_ino = strip_comments(sketch_ino)
        return {"sketch_ino": sketch_ino}
    
    else:

        prompt = f"""You are fixing a compilation error in an Arduino sketch for {state["target_board"]}.
 
=== ORIGINAL SKETCH ===
{state["sketch_ino"]}
 
=== COMPILE ERRORS ===
{state["compile_error"]}
 
=== CODE SPECIFICATION (reference only — do not change intent or components) ===
{state["code_spec"]}

- Circuit Specification: {state["circuit_spec"]}
 
 
=== FIX RULES ===
- Fix ONLY the lines directly responsible for the errors listed in COMPILE ERRORS
- Do NOT rewrite, restructure, or refactor any section not mentioned in the errors
- Preserve all working logic, pin assignments, variable names, and library calls exactly
 
 
=== STRICTLY FORBIDDEN ===
- NEVER add a new #include not present in the original sketch
- NEVER add a component, sensor, or peripheral not in Code Specification
- NEVER change pin numbers
- NEVER change the sensor or component type
- NEVER hardcode sensor values to avoid a runtime or compilation error
- NEVER remove Serial.print statements that exist in the original sketch
 
 
=== PRE-OUTPUT CHECKLIST ===
1. Only error-causing lines changed — all other code is untouched
2. No new #include added
3. No new component or library introduced
4. All pin numbers identical to the original sketch
5. No hardcoded sensor values introduced
6. All Serial.print/println statements from the original are preserved
7. First character is // or #. No markdown, no backticks, no explanation.
 
 
OUTPUT ONLY THE COMPLETE FIXED .ino CODE.
No markdown, no backticks, no explanation. First character must be // or #."""
 

        temp = 0.0 if state["retry_count"] == 0 else 0.4
        response = fast_llm.bind(temperature=temp).invoke(prompt)
        sketch_ino = re.sub(r"```(?:cpp|ino|c\+\+)?\n|\n```|```", "", response.content).strip()
        sketch_ino = strip_comments(sketch_ino)
        return {"sketch_ino": sketch_ino}
    
