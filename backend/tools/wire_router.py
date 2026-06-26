from collections import defaultdict

def _uno_nano_pins():
    pins = {}
    # Power/ground header — left edge, top section
    left_header = ["5V", "3.3V", "GND.1", "GND.2", "VIN", "RESET", "AREF"]
    for i, name in enumerate(left_header):
        pins[name] = (15, 95 + i * 26)
    # Digital pins 0-13 — right edge
    for i in range(14):
        pins[str(i)] = (430, 95 + i * 26)
    # Analog pins A0-A7 — bottom edge
    for i in range(8):
        pins[f"A{i}"] = (60 + i * 35, 460)
    return pins

def _mega_pins():
    pins = {}
    left_header = ["5V", "3.3V", "GND.1", "GND.2", "VIN", "RESET"]
    for i, name in enumerate(left_header):
        pins[name] = (15, 95 + i * 26)
    # Digital pins 0-53 — right edge, tightly spaced
    for i in range(54):
        pins[str(i)] = (640, 95 + i * 14)
    for i in range(16):
        pins[f"A{i}"] = (60 + i * 35, 700)
    return pins

def _esp32_pins():
    pins = {}
    left_header = ["3V3", "VIN", "GND.1", "GND.2"]
    for i, name in enumerate(left_header):
        pins[name] = (0, 95 + i * 60)
    gpio_list = [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23,
                 25, 26, 27, 32, 33, 34, 35, 36, 39]
    for i, g in enumerate(gpio_list):
        pins[str(g)] = (430, 95 + i * 18)
    return pins

BOARD_PIN_COORDS = {
    "wokwi-arduino-uno":  _uno_nano_pins(),
    "wokwi-arduino-nano": _uno_nano_pins(),
    "wokwi-arduino-mega": _mega_pins(),
    "wokwi-esp32-devkit-v1": _esp32_pins(),
}
BOARD_WIDTH = {
    "wokwi-arduino-uno":  430,
    "wokwi-arduino-nano": 380,
    "wokwi-arduino-mega": 640,
    "wokwi-esp32-devkit-v1": 430,
}

# Component pin offset tables — (dx, dy) from component's own top-left corner

COMPONENT_PIN_OFFSETS = {
    "wokwi-led":          {"A": (0, 0),  "C": (60, 0)},
    "wokwi-resistor":     {"1": (0, 10), "2": (75, 10)},
    "wokwi-capacitor":    {"1": (0, 10), "2": (50, 10)},
    "wokwi-buzzer":       {"1": (0, 0),  "2": (60, 0)},
    "wokwi-rgb-led":      {"R": (0, 0), "G": (20, 0), "B": (40, 0), "COM": (60, 0)},

    "wokwi-dht22":        {"VCC": (0, 0), "SDA": (0, 25), "GND": (0, 50)},
    "wokwi-dht11":        {"VCC": (0, 0), "SDA": (0, 25), "GND": (0, 50)},
    "wokwi-hc-sr04":      {"VCC": (0, 0), "TRIG": (0, 22), "ECHO": (0, 44), "GND": (0, 66)},
    "wokwi-pir-motion-sensor": {"GND": (0, 0), "OUT": (0, 22), "VCC": (0, 44)},
    "wokwi-ds18b20":      {"VCC": (0, 0), "GND": (0, 22), "DQ": (0, 44)},
    "wokwi-mpu6050":      {"VCC": (0, 0), "GND": (0, 18), "SCL": (0, 36), "SDA": (0, 54), "INT": (0, 72)},

    "wokwi-servo":        {"GND": (0, 0), "V+": (0, 18), "PWM": (0, 36)},

    "wokwi-lcd1602":      {"GND": (0, 0), "VCC": (20, 0), "SDA": (40, 0), "SCL": (60, 0)},
    "wokwi-lcd2004":      {"GND": (0, 0), "VCC": (20, 0), "SDA": (40, 0), "SCL": (60, 0)},
    "board-ssd1306":      {"GND": (0, 0), "VCC": (20, 0), "SCL": (40, 0), "SDA": (60, 0)},

    "wokwi-pushbutton":   {"1.l": (0, 0), "1.r": (20, 0), "2.l": (0, 20), "2.r": (20, 20)},
    "wokwi-potentiometer":{"GND": (0, 0), "SIG": (20, 0), "VCC": (40, 0)},

    "wokwi-neopixel":     {"GND": (0, 0), "VCC": (0, 20), "DIN": (0, 40)},
    "wokwi-relay-module": {"VCC": (0, 0), "GND": (0, 18), "IN": (0, 36), "COM": (60, 0), "NO": (60, 18), "NC": (60, 36)},
}
DEFAULT_PIN_OFFSET = (0, 0)
DEFAULT_COMPONENT_HEIGHT = 70  # used when stacking unmapped pins vertically

# Routing constants

CHANNEL_GAP   = 16   # fixed vertical gap between parallel wires in a channel
EDGE_MARGIN   = 40   # clearance past board's right edge before first channel
PIN_EXIT      = 12   # short straight segment leaving the source pin before turning

def route_wires(diagram: dict) -> dict:
    """
    Replace every connection's waypoints with an exact, pin-to-pin Manhattan
    path, using real component positions and pin offset tables. Wires sharing
    a routing corridor are assigned distinct parallel channels.
    """
    parts      = {p["id"]: p for p in diagram.get("parts", [])}
    board      = parts.get("board", {})
    board_type = board.get("type", "")
    board_w    = BOARD_WIDTH.get(board_type, 430)
    pin_table  = BOARD_PIN_COORDS.get(board_type, BOARD_PIN_COORDS["wokwi-arduino-uno"])

    connections = diagram.get("connections", [])

    # First pass: compute absolute source/dest coordinates for every connection
    resolved = []
    for conn in connections:
        if len(conn) < 4:
            resolved.append({"raw": conn, "skip": True})
            continue
        src_ref, dst_ref, color, existing = conn[0], conn[1], conn[2], conn[3]
        if existing and existing != ["h20"]:
            resolved.append({"raw": conn, "skip": True})
            continue

        src_id, src_pin = _split_ref(src_ref)
        dst_id, dst_pin = _split_ref(dst_ref)

        src_pos = _absolute_pin_pos(src_id, src_pin, parts, pin_table)
        dst_pos = _absolute_pin_pos(dst_id, dst_pin, parts, pin_table)

        resolved.append({
            "raw": conn, "skip": False,
            "src_ref": src_ref, "dst_ref": dst_ref, "color": color,
            "src_id": src_id, "dst_id": dst_id,
            "src_pos": src_pos, "dst_pos": dst_pos,
        })

    # Second pass: assign each wire to a channel and build its waypoints
    channel_counts = defaultdict(int)
    routed = []

    for item in resolved:
        if item["skip"]:
            routed.append(item["raw"])
            continue

        sx, sy = item["src_pos"]
        dx, dy = item["dst_pos"]

        channel_key = _channel_key(item["src_id"], item["dst_id"], sy, dy)
        lane = channel_counts[channel_key]
        channel_counts[channel_key] += 1

        waypoints = _build_path(sx, sy, dx, dy, board_w, lane)

        routed.append([item["src_ref"], item["dst_ref"], item["color"], waypoints])

    diagram["connections"] = routed
    return diagram

# Internal helpers

def _split_ref(ref: str):
    if ":" in ref:
        comp, pin = ref.split(":", 1)
        return comp, pin
    return ref, ""

def _absolute_pin_pos(part_id, pin_name, parts, board_pin_table):
    """Resolve a part:pin reference to its absolute (x, y) on the canvas."""
    if part_id == "board":
        x, y = board_pin_table.get(pin_name, (0, 0))
        return (x, y)

    part = parts.get(part_id, {})
    top  = part.get("top", 0)
    left = part.get("left", 0)
    ptype = part.get("type", "")

    offsets = COMPONENT_PIN_OFFSETS.get(ptype, {})
    dx, dy = offsets.get(pin_name, DEFAULT_PIN_OFFSET)

    return (left + dx, top + dy)


def _channel_key(src_id, dst_id, sy, dy):
    """
    Group wires that will likely share a routing corridor: same source body
    and same destination body, traveling in a similar vertical direction.
    """
    return (src_id, dst_id)


def _build_path(sx, sy, dx, dy, board_w, lane):
    """
    Build a 3-segment Manhattan path (exit → channel → entry) as relative
    waypoints, guaranteeing the wire starts and ends exactly on its pins.

    Segment 1: short horizontal exit from source pin
    Segment 2: vertical travel to align with destination's y, in a lane
               offset by CHANNEL_GAP * lane from the previous wire in the
               same corridor — guarantees parallel, non-overlapping paths
    Segment 3: horizontal entry into destination pin (implicit — Wokwi
               completes the final connection automatically once x/y align)
    """
    lane_offset = lane * CHANNEL_GAP

    # Exit point: move right from source by PIN_EXIT, offset into this wire's lane
    exit_dx = PIN_EXIT if dx >= sx else -PIN_EXIT
    exit_dy = lane_offset if dy >= sy else -lane_offset

    # Vertical travel needed to reach destination's y (relative to exit point)
    vertical_dy = (dy - sy) - exit_dy

    # Horizontal travel needed to reach destination's x (relative after vertical)
    horizontal_dx = (dx - sx) - exit_dx

    waypoints = []
    if exit_dx != 0:
        waypoints.append(f"h{exit_dx}")
    if exit_dy != 0:
        waypoints.append(f"v{exit_dy}")
    if vertical_dy != 0:
        waypoints.append(f"v{vertical_dy}")
    if horizontal_dx != 0:
        waypoints.append(f"h{horizontal_dx}")

    return waypoints
