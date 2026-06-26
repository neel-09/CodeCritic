from dotenv import load_dotenv
load_dotenv()
from backend.state import State
from backend.database.generation_cache import check_cache, increment_hit_count, get_spec_hash , get_prompt_hash , check_prompt_cache

def Cache_Node(state: State):
    spec_hash = get_spec_hash(state["code_spec"], state["circuit_spec"], state["target_board"])
    cached = check_cache(spec_hash)
    increment_hit_count(spec_hash)
    return {
        "sketch_ino": cached["sketch_ino"],
        "diag_json": cached["diagram_json"],
        "pass_score": cached["pass_score"],
        "spec_hash": spec_hash,
    }

def Cache_Lookup_Node(state: State):
    prompt_hash = get_prompt_hash(state["user_prompt"], state["target_board"])
    cached = check_prompt_cache(prompt_hash)
    if cached:
        increment_hit_count(prompt_hash)
        return {
            "sketch_ino":  cached["sketch_ino"],
            "diag_json":   cached["diagram_json"],
            "pass_score":  cached["pass_score"],
            "prompt_hash": prompt_hash,
            "cache_hit":   True,
        }
    return {"cache_hit": False, "prompt_hash": prompt_hash}
