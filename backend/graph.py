from dotenv import load_dotenv
load_dotenv()
import uuid
from backend.state import State
from langgraph.graph import StateGraph,START,END
from backend.nodes.coder_node import Coder_Node
from backend.nodes.compiler_node import Compiler_Node
from backend.nodes.planner_node import Planner_Node
from backend.nodes.output_node import Output_Node
from backend.database.generation_cache import get_spec_hash , check_cache , increment_hit_count
from backend.database.sessions_db import create_session
from backend.nodes.dependency_node import Dependency_Node
from backend.nodes.circuit_designer_node import Circuit_Designer_Node
from backend.nodes.silicon_critic_node import Silicon_Critic_Node
from backend.nodes.cache_node import Cache_Node , Cache_Lookup_Node
from backend.nodes.inspector_node import Inspector_Node

graph_builder = StateGraph(State)
        
def Dispatch_Node(state: State): # for parallel execution
    return {}

def Reset_Node(state : State):
    session_id = str(uuid.uuid4())
    create_session(
        session_id,
        state["user_prompt"],
        state["target_board"],
        state.get("complexity_score", 0)
    )
    return {"compile_error": [], 
            "retry_count": 0, 
            "session_id": session_id, 
            "error_log": {}, 
            "hex_path": "", 
            "pass_score": 0.0, 
            "assertion_diff": {}, 
            "simulation_feedback": "", 
            "diag_json": "" , 
            "dsl_assertions": [],
            "serial_output": "",
            "vcd_data": "",
            "exit_code": 0,}

def route_compiler(state: State):
    if state["compile_error"]:
        if state["retry_count"] > 2:
            return "max_retries"
        return "error"
    return "success"

def route_cache_lookup(state: State):
    if state["cache_hit"]:
        return "cached"
    return "continue"

def route_planner(state: State):
    if state["clarification_needed"]:
        return "clarification"
    spec_hash = get_spec_hash(state["code_spec"], state["circuit_spec"], state["target_board"])
    if check_cache(spec_hash):
        return "cached"
    return "continue"

def route_inspector(state: State):
    if state["pass_score"] >= 0.7:
        return "success"
    if state["retry_count"] > 2:
        return "max_retries"
    return "retry"

graph_builder.add_node("Coder", Coder_Node)
graph_builder.add_node("Compiler",Compiler_Node)
graph_builder.add_node("Reset",Reset_Node)
graph_builder.add_node("Planner",Planner_Node)
graph_builder.add_node("Output", Output_Node)
graph_builder.add_node("Dependency", Dependency_Node)
graph_builder.add_node("Dispatch", Dispatch_Node)
graph_builder.add_node("Circuit_Designer", Circuit_Designer_Node)
graph_builder.add_node("Silicon_Critic", Silicon_Critic_Node)
graph_builder.add_node("Cache", Cache_Node)
graph_builder.add_node("Inspector", Inspector_Node)
graph_builder.add_node("Cache_Lookup", Cache_Lookup_Node)


graph_builder.add_edge(START,"Reset")
graph_builder.add_edge("Reset", "Cache_Lookup")
graph_builder.add_edge("Dispatch", "Coder")
graph_builder.add_edge("Dispatch", "Circuit_Designer")
graph_builder.add_edge("Circuit_Designer", "Dependency") 
graph_builder.add_edge("Coder", "Dependency")
graph_builder.add_edge("Dependency", "Compiler")
graph_builder.add_edge("Silicon_Critic", "Inspector")
graph_builder.add_edge("Cache", "Output")
graph_builder.add_edge("Output", END)

graph_builder.add_conditional_edges(
    "Compiler",
    route_compiler,
    {
        "success": "Silicon_Critic",
        "error": "Coder",
        "max_retries": "Output"
    })

graph_builder.add_conditional_edges(
    "Planner",
    route_planner,
    {
        "continue": "Dispatch",
        "clarification": END,
        "cached": "Cache"
    }
)

graph_builder.add_conditional_edges(
    "Cache_Lookup", 
    route_cache_lookup, 
    {
        "cached": "Output",
        "continue" : "Planner"
    }
)

graph_builder.add_conditional_edges(
    "Inspector",
    route_inspector,
    {
        "success": "Output",
        "retry": "Dispatch",
        "max_retries": "Output"
    }
)

graph = graph_builder.compile()

