import json

def get_component_for_channel(diag_json: str, channel: str) -> str:
    """Returns component type for a given logic analyzer channel e.g. 'D0'"""
    diagram = json.loads(diag_json)
    
    # Build id → type map
    part_types = {p["id"]: p["type"] for p in diagram["parts"]}
    
    # Find which component pin connects to la:channel
    for conn in diagram["connections"]:
        pin1, pin2 = conn[0], conn[1]
        if pin2 == f"la:{channel}":
            comp_id = pin1.split(":")[0]
            return part_types.get(comp_id, "unknown")
        if pin1 == f"la:{channel}":
            comp_id = pin2.split(":")[0]
            return part_types.get(comp_id, "unknown")
    
    return "unknown"