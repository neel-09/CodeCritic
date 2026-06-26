from dotenv import load_dotenv
load_dotenv()
import os , supabase , json , hashlib

supabase_client = supabase.create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

def get_spec_hash(code_spec: dict, circuit_spec: dict, board: str) -> str:
    combined = json.dumps({
        "code_spec": code_spec,
        "circuit_spec": circuit_spec,
        "board": board
    }, sort_keys=True)
    return hashlib.sha256(combined.encode()).hexdigest()

def check_cache(spec_hash) :
    result = supabase_client.table("generation_cache").select("*").eq("spec_hash", spec_hash).execute()
    if result.data :
        return result.data[0] 
    else :
        None 

def get_prompt_hash(prompt: str, board: str) -> str:
    normalized = " ".join(prompt.lower().strip().split())
    return hashlib.sha256(f"{normalized}|{board.lower()}".encode()).hexdigest()

def check_prompt_cache(prompt_hash: str):
    result = supabase_client.table("generation_cache").select("*").eq("prompt_hash", prompt_hash).execute()
    return result.data[0] if result.data else None

def save_to_cache(spec_hash, board, prompt, sketch_ino, diagram_json, pass_score , prompt_hash) :
    supabase_client.table("generation_cache").upsert({
    "spec_hash": spec_hash,
    "board": board,
    "prompt": prompt,
    "sketch_ino": sketch_ino,
    "diagram_json": diagram_json,
    "pass_score": pass_score,
    "prompt_hash" : prompt_hash
}, on_conflict="prompt_hash").execute()
    
def increment_hit_count(prompt_hash):
    result = (
        supabase_client.table("generation_cache")
        .select("hit_count")
        .eq("prompt_hash", prompt_hash)
        .execute()
    )

    if not result.data:
        return

    current = result.data[0]["hit_count"] or 0
    supabase_client.table("generation_cache").update({
        "hit_count": current + 1
    }).eq("prompt_hash", prompt_hash).execute()