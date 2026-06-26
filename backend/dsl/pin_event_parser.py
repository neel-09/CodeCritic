def get_pin_timestamps(parsed_vcd: dict, pin_key: str) -> list[int]:
    # returns a list of timestamps for a given pin
    events = parsed_vcd.get(pin_key, [])
    if events is None:
        return []
    return [e["time_ns"] // 1_000_000 for e in events]
