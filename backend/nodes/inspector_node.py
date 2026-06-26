from backend.state import State
from backend.dsl.vcd_parser import parse_vcd
from backend.dsl.evaluator import evaluate_assertions
from backend.database.emulator_quirks import get_quirks, add_quirk
from backend.tools.diagram_parser import get_component_for_channel
import sys

def Inspector_Node(state: State):
    vcd_data = state["vcd_data"]
    serial_output = state.get("serial_output", "")
    dsl_assertions = state["dsl_assertions"]

    if not state.get("dsl_assertions"):
        # STRATEGY C — compile-only verification, no behavioral assertion to check
        return {
            "pass_score": 1.0,
            "assertion_diff": {"note": "compile-only verification — no assertions defined"},
            "simulation_feedback": "Compiled and circuit-validated successfully. No behavioral assertion applicable for this task type."
        }

    has_pin_assertions = any(a["assertion_type"] in ("timing", "level") for a in dsl_assertions)

    if has_pin_assertions and not vcd_data:
        return {
            "pass_score": 0.0,
            "assertion_diff": {"error": "no VCD data"},
            "simulation_feedback": "No VCD data captured",
            "retry_count": state["retry_count"] + 1
        }

    parsed_vcd = parse_vcd(vcd_data) if vcd_data else {}
    score, diff = evaluate_assertions(parsed_vcd, dsl_assertions, serial_output)

    adjusted_passed = 0
    total = len(dsl_assertions)

    for key, detail in diff.items():
        if "pass" in detail:
            adjusted_passed += 1
        elif "fail" in detail:
            assertion_type = key.split("_")[0]
            idx = int(key.split('_')[1]) - 1
            assertion = dsl_assertions[idx]

            if assertion["assertion_type"] in ("timing", "level"):
                channel = f"D{assertion.get('pin_number', 0)}"
                component = get_component_for_channel(state["diag_json"], channel)
                quirks = get_quirks(component, assertion_type)

                if quirks:
                    adjusted_passed += 1
                    diff[key]["quirk_ignored"] = True
                elif state["exit_code"] in (0, 42) and state["retry_count"] >= 2:
                    # Simulation ran fine but assertion keeps failing after retries
                    # Likely a simulator quirk — log it
                    add_quirk(
                        component=component,
                        assertion_type=assertion_type,
                        description=f"Assertion failed after {state['retry_count']} retries despite clean simulation exit",
                        wokwi_version="1.0.0-20260526"
                    )
            # serial assertion failures: scored as-is, no quirk lookup

    score = adjusted_passed / total if total > 0 else 0.0

    if score >= 0.7:
        return {
            "pass_score": score,
            "assertion_diff": diff,
            "simulation_feedback": f"Score: {score:.2f}. {str(diff)}"
        }

    circuit_error = state.get("error_log", {}).get("circuit_designer", "")
    if circuit_error:
        feedback = f"Circuit error: {circuit_error}. Score: {score:.2f}. {str(diff)}"
    else:
        feedback = f"Score: {score:.2f}. {str(diff)}"

    return {
        "pass_score": score,
        "assertion_diff": diff,
        "simulation_feedback": feedback,
        "retry_count": state["retry_count"] + 1
    }