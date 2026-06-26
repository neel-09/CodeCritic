from dotenv import load_dotenv
load_dotenv()
from backend.state import State
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json , sys , os

async def Silicon_Critic_Node(state : State):

    diag_json = state["diag_json"]
    hex_path = state["hex_path"]
    timeout_ms = 5000
    server_params = StdioServerParameters(
    command=sys.executable,
    args=["backend/mcp_servers/inspector_server.py"],
    cwd=r"D:\codecritic",
    env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})

    if not diag_json or not hex_path:
        return {
            "pass_score": 0.0, 
            "simulation_feedback": "Missing diagram or hex file",
        }
    try :
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                #tools = await session.list_tools()
                #for t in tools.tools:
                    #if t.name == "run_simulation":
                        #sys.stderr.write(f"SCHEMA: {t.inputSchema}\n")
                with open(hex_path, "r") as f:
                    hex_content = f.read()

                diag_json = state["diag_json"]
                if isinstance(diag_json, dict):
                    diag_json = json.dumps(diag_json)

                # Double-encode so the server's pre-parser unwraps it back to the original string
                diag_json_arg = json.dumps(diag_json)
                
                #sys.stderr.write(f"AFTER: type={type(diag_json)}, repr={repr(diag_json)[:150]}\n")
                output = await session.call_tool("run_simulation", {
                    "diag_json": diag_json_arg,
                    "hex_content": hex_content,
                    "timeout_ms": timeout_ms
                })

                result = output.content[0].text # returns string
                sys.stderr.write(f"IS_Inspector_ERROR: {output.isError}\n")
                #sys.stderr.write(f"INSPECTOR RESULT: {result}\n")
                if output.isError: # for tool error
                        return {"pass_score": 0.0, "simulation_feedback": result,"retry_count": state["retry_count"] + 1}

    except Exception as e:
        import traceback
        with open(r"D:\codecritic\debug.txt", "w") as f:
            f.write(traceback.format_exc())
        return {"pass_score": 0.0, "simulation_feedback": str(e), "retry_count": state["retry_count"] + 1}
        
    parsed = json.loads(result)
    # sys.stderr.write(f"VCD KEYS: {list(parsed['vcd_content'].keys())}\n")
    return {
        "serial_output": parsed["serial_output"],
        "vcd_data": parsed["vcd_content"],
        "exit_code": parsed["exit_code"],
        "pass_score": 0.0,        # Inspector sets this
        "simulation_feedback": "" # Inspector sets this
    }
