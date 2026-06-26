from dotenv import load_dotenv
load_dotenv()
from backend.state import State
from backend.database.sessions_db import update_session 
from backend.database.generation_cache import save_to_cache , get_spec_hash

def Output_Node(state: State):
    if not state["compile_error"] and state.get("pass_score", 0.0) >= 0.7:
        final_status = "success"
    else:
        final_status = "max_retries"

    # compute spec_hash early — use cached value or compute fresh
    spec_hash = state.get("spec_hash", "")
    
    if final_status == "success" and not spec_hash and not state.get("cache_hit"):
        spec_hash = get_spec_hash(state["code_spec"], state["circuit_spec"], state["target_board"])
        save_to_cache(
            spec_hash=spec_hash,
            board=state["target_board"],
            prompt=state["user_prompt"],
            sketch_ino=state["sketch_ino"],
            diagram_json=state["diag_json"],
            pass_score=state.get("pass_score", 1.0),
            prompt_hash=state.get("prompt_hash"),
        )

    update_session(
    state["session_id"],
    final_status,
    state.get("retry_count", 0),
    state.get("pass_score", 1.0),
    state.get("error_log", ""),
    state.get("complexity_score", 0),
    spec_hash,
    state.get("hex_path", ""),)

    return {"spec_hash": spec_hash}
