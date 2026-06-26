from dotenv import load_dotenv
load_dotenv()
import os
import supabase

supabase_client = supabase.create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

def create_session(session_id , user_prompt , target_board , complexity_score ) :
    supabase_client.table("sessions").insert({"session_id" : session_id,
                                                        "user_prompt" : user_prompt,
                                                        "board" : target_board,
                                                        "complexity" : complexity_score}).execute()

def update_session(session_id, final_status, iteration_count, pass_score, error_log, complexity_score, spec_hash=None, hex_path=None):
    supabase_client.table("sessions").update({
        "final_status": final_status,
        "iteration_count": iteration_count,
        "pass_score": pass_score,
        "error_log": error_log,
        "complexity": complexity_score,
        "spec_hash": spec_hash,
        "hex_path": hex_path,
    }).eq("session_id", session_id).execute()

def get_session(session_id) :
    result = supabase_client.table("sessions").select("*").eq("session_id", session_id).execute()
    if result.data :
        return result.data[0] 
    else :
        return None
