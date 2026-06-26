def evaluate_assertions(parsed_vcd: dict, assertions: list, serial_output: str = "") -> tuple[float, dict]:
    # loops through assertions, calls the right helper, returns score + diff
    passed = 0
    total = 0
    diff = {}
    for assertion in assertions:
        total += 1
        atype = assertion["assertion_type"]

        if atype == "timing":
            if not parsed_vcd:
                result, detail = False, {"fail": "no VCD data"}
            else:
                result, detail = evaluate_timing(parsed_vcd, assertion)
        elif atype == "level":
            if not parsed_vcd:
                result, detail = False, {"fail": "no VCD data"}
            else:
                result, detail = evaluate_level(parsed_vcd, assertion)
        elif atype == "serial":
            result, detail = evaluate_serial(serial_output, assertion)
        else:
            result, detail = False, {"skipped": True}

        if result:
            passed += 1
        diff[f"{atype}_{total}"] = detail

    score = passed / total if total > 0 else 0.0
    return score, diff


def evaluate_timing(parsed_vcd: dict, assertion) -> tuple[bool, str]:
    # checks pin toggles at a timestamp
    pin_key = f"D{assertion['pin_number']}"
    events = parsed_vcd.get(pin_key, [])
    
    if not events:
        return False, {"fail": "no events found for pin"}
    
    # Filter value changes first
    all_filtered = []
    last_value = None
    for e in events:
        if e["value"] != last_value:
            all_filtered.append(e)
            last_value = e["value"]

    # Remove t=0 initial state
    filtered = [e for e in all_filtered if e["time_ns"] > 0]
    
    # Then check min_toggles against filtered
    if len(filtered) < assertion["min_toggles"]:
        return False, {"fail": f"only {len(filtered)} toggles, expected {assertion['min_toggles']}"}

    timestamps_ms = [e["time_ns"] / 1_000_000 for e in filtered]
    periods = [timestamps_ms[i+1] - timestamps_ms[i] for i in range(len(timestamps_ms)-1)]
    
    for period in periods:
        if not (assertion["expected_period_ms"] - assertion["tolerance_ms"] <= period <= assertion["expected_period_ms"] + assertion["tolerance_ms"]):
            return False, {"fail": f"period {period}ms out of range"}
    
    return True, {"pass": "all periods within tolerance"}


def evaluate_level(parsed_vcd: dict, assertion) -> tuple[bool, str]:
    # checks pin state at a timestamp
    pin_key = f"D{assertion['pin_number']}"
    events = parsed_vcd.get(pin_key, [])
    if events is None:
        return 0.0, {"error" : "fail"}
    last_value = None
    for event in events:
        if event["time_ns"] / 1_000_000 > assertion["timestamp_ms"]:
            break
        last_value = event["value"]

    expected = 1 if assertion["expected_level"] == "HIGH" else 0
    if last_value == expected:
        return True, {"pass": f"pin is {assertion['expected_level']} at {assertion['timestamp_ms']}ms"}
    return False, {"fail": f"expected {assertion['expected_level']}, got {last_value}"}


def evaluate_serial(serial_output: str, assertion: dict) -> tuple[bool, dict]:
    # checks serial output content against expected patterns
    if not serial_output or not serial_output.strip():
        return False, {"fail": "no serial output captured"}

    lines = [l for l in serial_output.strip().splitlines() if l.strip()]

    min_lines = assertion.get("min_lines", 1)
    if len(lines) < min_lines:
        return False, {"fail": f"only {len(lines)} lines, expected at least {min_lines}"}

    expected_patterns = assertion.get("expected_patterns", [])
    missing = [p for p in expected_patterns if p.lower() not in serial_output.lower()]
    if missing:
        return False, {"fail": f"missing expected patterns: {missing}"}

    nan_count = serial_output.lower().count("nan")
    max_nan_ratio = assertion.get("max_nan_ratio", 0.5)
    if len(lines) > 0 and (nan_count / len(lines)) > max_nan_ratio:
        return False, {"fail": f"too many NaN readings ({nan_count}/{len(lines)} lines)"}

    return True, {"pass": f"serial output matches expected patterns ({nan_count}/{len(lines)} NaN)"}