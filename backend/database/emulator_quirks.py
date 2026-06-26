from backend.database.generation_cache import supabase_client

def get_quirks(component: str, assertion_type: str) -> list[dict]:
    result = supabase_client.table("emulator_quirks")\
        .select("*")\
        .eq("component", component)\
        .eq("assertion_type", assertion_type)\
        .eq("resolved", False)\
        .execute()
    return result.data if result.data else []

def add_quirk(component: str, assertion_type: str, description: str, wokwi_version: str):
    supabase_client.table("emulator_quirks").insert({
        "component": component,
        "assertion_type": assertion_type,
        "description": description,
        "wokwi_version": wokwi_version,
        "resolved": False,
        "resolved_version": None
    }).execute()
