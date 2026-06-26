from backend.api.models import GenerateRequest
from backend.graph import graph
import json
from typing import AsyncIterator
NODE_NAMES = {
    "Reset", "Planner", "Coder", "Dependency", "Dispatch",
    "Compiler", "Circuit_Designer", "Silicon_Critic",
    "Cache", "Cache_Lookup" , "Inspector", "Output"
}

async def stream_graph(req : GenerateRequest) -> AsyncIterator[str]:

    try :
        initial_state = {
            "user_prompt": req.prompt,
            "target_board": req.board,
            "target_fqbn": req.fqbn,
            "retry_count": 0,
            "compile_error": [],
            "pass_score": 0.0,
            "assertion_diff": {},
            "clarification_needed": False,
            "clarification_question": "",
            "simulation_feedback": "",
            "hex_path": "",
            "vcd_data": "",
            "serial_output": "",
            "exit_code": 0,
            "dsl_assertions": [],
            "code_spec": {},
            "circuit_spec": {},
            "error_log": {},
            "complexity_score": 0,
            "spec_hash": "",
            "sketch_ino": "",
            "diag_json": "",
            "lib_txt": "",
        }
        final_state = {}

        async for event in graph.astream_events(initial_state, version="v2"):
            name = event.get("name", "")
            if name not in NODE_NAMES:
                continue
            if event["event"] == "on_chain_start":
                yield f"data: {json.dumps({'type': 'node_start', 'node': name})}\n\n"
            elif event["event"] == "on_chain_end":
                output = event["data"].get("output", {})
                if isinstance(output, dict):
                    final_state.update(output)
                yield f"data: {json.dumps({'type': 'node_complete', 'node': name})}\n\n"

        if final_state.get("clarification_needed"):
            yield f"data: {json.dumps({'type': 'clarification', 'question': final_state.get('clarification_question', '')})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'done', 'result': {
                'sketch_ino':     final_state.get('sketch_ino', ''),
                'diag_json':      final_state.get('diag_json', ''),
                'pass_score':     final_state.get('pass_score', 0.0),
                'assertion_diff': final_state.get('assertion_diff', {}),
                'session_id':     final_state.get('session_id', ''),
            }})}\n\n"

    except Exception as e :
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
