from dotenv import load_dotenv
load_dotenv()
import json , sys , os
from backend.state import State
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def Compiler_Node(state : State):

    latest_code = state["sketch_ino"]
    retry_count = state["retry_count"]

    # if not state.get("diag_json"):
    #     return {
    #         "compile_error": ["No circuit diagram — skipping compilation"],
    #         "retry_count": state["retry_count"] + 1
    #     }
    
    server_params = StdioServerParameters(
    command=sys.executable,
    args=["backend/mcp_servers/compiler_server.py"],
    cwd=r"D:\codecritic",
    env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
)
    try :    
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                output = await session.call_tool("compile_sketch", {
                    "sketch_code": latest_code,
                    "fqbn": state["target_fqbn"]
                })
                result = output.content[0].text # returns string
                #sys.stderr.write(f"RESULT: '{result}'\n")
                sys.stderr.write(f"IS_Compiler_ERROR: {output.isError}\n")
                if output.isError: # for tool error
                    return {"compile_error": [result], "retry_count": retry_count + 1}

    except BaseException as e:
        import traceback
        with open(r"D:\codecritic\debug1.txt", "w") as f:
            f.write(traceback.format_exc())
        return {"compile_error": [str(e)], "retry_count": retry_count + 1}

    parsed = json.loads(result)
    if parsed["status"] == "success":
        return {"sketch_ino": latest_code, "compile_error": [] , "hex_path": parsed.get("hex_path", "")}
    else:
        return {"compile_error": parsed["errors"], "retry_count": retry_count + 1} # for code error
    
    