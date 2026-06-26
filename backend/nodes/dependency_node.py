from backend.tools.dependency_injector import install_dependencies
from backend.state import State

def Dependency_Node(state : State) :
    
    if not state.get("diag_json"):
        return {
            "lib_txt": "",
            "compile_error": ["Circuit diagram missing — skipping compilation"],
            "retry_count": state["retry_count"] + 1
        }
    
    installed = install_dependencies(state["sketch_ino"])
    return {"lib_txt": ", ".join(installed)}

