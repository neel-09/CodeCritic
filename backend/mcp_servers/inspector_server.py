from dotenv import load_dotenv
load_dotenv()
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import sys,tempfile,os,subprocess,json
import os

USAGE_FILE_PATH = r"D:\codecritic\debug\wokwi_usage.txt"

def get_used_seconds() -> float:
  
    if not os.path.exists(USAGE_FILE_PATH):
        return 0.0

    total_seconds = 0.0
    try:
        with open(USAGE_FILE_PATH, "r") as file:
            for line in file:
                cleaned_line = line.strip()
                if cleaned_line :
                    total_seconds += float(cleaned_line)
    except Exception as e:
        print(f"Error reading usage file: {e}")
        
    return total_seconds

def log_simulation_seconds(seconds: float):
    
    os.makedirs(os.path.dirname(USAGE_FILE_PATH), exist_ok=True)
    
    with open(USAGE_FILE_PATH, "a") as file:
        file.write(f"{seconds}\n")

from mcp.server.fastmcp import FastMCP
mcp = FastMCP("inspector")
@mcp.tool()
def run_simulation(diag_json: str, hex_content: str, timeout_ms: int = 5000) -> str:

    diag_json = json.loads(diag_json)
    with tempfile.TemporaryDirectory() as tmpdir:
        
        # Write diagram.json
        with open(os.path.join(tmpdir, "diagram.json"), "w") as f:
            f.write(diag_json)
        
        # Write firmware.hex
        with open(os.path.join(tmpdir, "firmware.hex"), "w") as f:
            f.write(hex_content)
        
        # Write wokwi.toml
        with open(os.path.join(tmpdir, "wokwi.toml"), "w") as f:
            f.write('[wokwi]\nversion = 1\nfirmware = "firmware.hex"\nelf = "firmware.hex"\n')

        #sys.stderr.write(f"Running wokwi-cli from: {tmpdir}\n")
        #sys.stderr.write(f"wokwi-cli path: {subprocess.run(['where', 'wokwi-cli'], capture_output=True, text=True).stdout}\n")

        WOKWI_CLI_path = os.getenv("WOKWI_CLI_PATH")
        vcd_output = os.path.join(tmpdir, "output.vcd")

        used = get_used_seconds()
        budget = int(os.getenv("WOKWI_MONTHLY_BUDGET_SECONDS", "3000"))
        if used >= budget:
            return json.dumps({"exit_code": -1, "serial_output": "", "vcd_content": "", 
                            "stderr": f"Wokwi budget exhausted: {used}s used of {budget}s"})
        
        import time
        start = time.time()
        # Run simulation
        result = subprocess.run(
            [WOKWI_CLI_path, "--timeout", str(timeout_ms), "--serial-log-file", "serial.log", "--vcd-file", vcd_output, "."],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env={**os.environ, "WOKWI_CLI_TOKEN": os.getenv("WOKWI_CLI_TOKEN", "")}
        )
        
        elapsed = time.time() - start
        log_simulation_seconds(elapsed)

        # # Read vcd file
        actual_vcd = os.path.join(tmpdir, "output.vcd")
        vcd_content = open(actual_vcd).read() if os.path.exists(actual_vcd) else ""

        if not vcd_content.strip():
            stdout_lines = result.stdout.splitlines()
            vcd_start = next((i for i, l in enumerate(stdout_lines) if l.startswith("$version")), None)
            if vcd_start is not None:
                vcd_content = "\n".join(stdout_lines[vcd_start:])

        os.makedirs(r"D:\codecritic\debug", exist_ok=True)
        #Copy to debug folder
        vcd_path = r"D:\codecritic\debug\output.vcd"
        with open(vcd_path, "w") as f:
            f.write(vcd_content)
        
        # Read serial log
        serial_log = os.path.join(tmpdir, "serial.log")
        serial_output = open(serial_log).read() if os.path.exists(serial_log) else ""
        vcd_content = open(vcd_path).read() if os.path.exists(vcd_path) else ""

        with open(r"D:\codecritic\debug\wokwi_debug.txt", "w") as dbg:
            dbg.write(f"EXIT: {result.returncode}\n")
            dbg.write(f"STDERR: {result.stderr}\n")
            dbg.write(f"STDOUT: {result.stdout}\n")
        return json.dumps({
            "exit_code": result.returncode,
            "serial_output": serial_output,
            "stderr": result.stderr,
            "vcd_content": vcd_content
        })
    
if __name__ == "__main__":
    mcp.run(transport="stdio")
      