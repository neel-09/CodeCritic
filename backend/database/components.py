from backend.database.generation_cache import supabase_client

def get_component(name : str) :
    result = supabase_client.table("components").select("*").eq("name", name).execute()
    if result.data :
        return result.data[0]
    else :
        return None

def insert_component(name, wokwi_id, protocol=None, voltage=None, pinout=None, electrical=None, datasheet_url=None, i2c_address=None, verified=False) :
    
    supabase_client.table("components").insert({
        "name": name,
        "wokwi_id": wokwi_id,
        "protocol": protocol,
        "voltage": voltage,
        "pinout": pinout,
        "electrical": electrical,
        "datasheet_url": datasheet_url,
        "i2c_address": i2c_address,
        "verified": verified}).execute()

def update_component(name: str, updates: dict) :

    supabase_client.table("components").update(updates).eq("name", name).execute()
