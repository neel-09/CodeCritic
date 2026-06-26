from dotenv import load_dotenv
load_dotenv()
import sys, os
#sys.stderr.write("STAGE 1: dotenv loaded\n")
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import sys,tempfile,os,subprocess,json
#sys.stderr.write("STAGE 2: stdlib imported\n")

from backend.cache.hex_cache import get_hash, check_cache, save_to_cache
#sys.stderr.write("STAGE 3: hex_cache imported\n")

from mcp.server.fastmcp import FastMCP
#sys.stderr.write("STAGE 4: FastMCP imported\n")

mcp = FastMCP("compile_sketch")
subprocess.run(["arduino-cli", "lib", "update-index"], capture_output=True)
#sys.stderr.write("STAGE 5: FastMCP instance created\n")
@mcp.tool()
def compile_sketch(sketch_code : str , fqbn : str):

    hash = get_hash(sketch_code)
    hex_content = check_cache(hash)
    if hex_content is not None:
        hex_path = os.path.join(os.getenv("HEX_CACHE_DIR"), f"{hash}.hex")
        return json.dumps({"status": "success", "hex": hex_content, "hex_path": hex_path})
    else:
        sketch_folder = tempfile.mkdtemp()
        folder_name = os.path.basename(sketch_folder)
        sketch_file = os.path.join(sketch_folder, f"{folder_name}.ino")
        with open(sketch_file, "w") as f:
            f.write(sketch_code)

        result = subprocess.run(["arduino-cli", "compile", "--fqbn", fqbn, "--format", "json", sketch_folder] , capture_output=True , text=True , encoding="utf-8" , errors="replace")
        
        if result.returncode == 0: # for successful compilation
            output_json = json.loads(result.stdout)
            build_path = output_json["builder_result"]["build_path"]
            hex_path = os.path.join(build_path, f"{folder_name}.ino.hex")
            with open(hex_path, "r") as f:
                hex_content = f.read()
            hex_path = save_to_cache(hash, hex_content)
            return json.dumps({"status": "success", "hex": hex_content , "hex_path": hex_path})
        else:
            try:
                error_json = json.loads(result.stdout)
                compiler_err = error_json.get("compiler_err", "")
                # Extract just the error lines, skip empty lines
                error_lines = [line for line in compiler_err.split("\n") if "error:" in line]
                errors = error_lines if error_lines else [compiler_err]
            except:
                errors = [result.stdout]
            return json.dumps({"status": "error", "errors": errors})

if __name__ == "__main__":
    #sys.stderr.write("STAGE 6: calling mcp.run()\n")
    mcp.run(transport="stdio")
