def parse_vcd(vcd_content: str) -> dict:

    """Parses a raw VCD string into a dictionary mapping variable names 
       to their timestamped value changes."""
    
    var_map = {}  # Maps VCD symbols (like '!') to human-readable names (like 'D0')
    parsed_data = {}
    
    current_time = 0
    
    for line in vcd_content.strip().splitlines():
        line = line.strip()
        if not line:
            continue
            
        # 1. Parse variable definitions
        # Example: $var wire 1 ! D0 $end
        if line.startswith("$var"):
            parts = line.split()
            if len(parts) >= 5:
                symbol = parts[3]
                name = parts[4]
                var_map[symbol] = name
                parsed_data[name] = []
                
        # 2. Parse time updates
        # Example: #5000000000
        elif line.startswith("#"):
            current_time = int(line[1:])
            
        # 3. Parse 1-bit / multi-bit value changes
        # Ignore other $ command lines (like $timescale, $end, $dumpvars)
        elif not line.startswith("$") and len(line) >= 2:
            if line.startswith("b"):  # multi-bit: "b1010 !"
                parts = line[1:].split()
                if len(parts) == 2:
                    val_str = parts[0]
                    symbol = parts[1].strip()
                    value = val_str  # keep as binary string
                else:
                    continue
            else:  # 1-bit: "1!" or "0!"
                val_str = line[0]
                symbol = line[1:].strip()
                value = int(val_str) if val_str in ('0', '1') else val_str

            if symbol in var_map:
                var_name = var_map[symbol]
                parsed_data[var_name].append({
                    "time_ns": current_time,
                    "value": value
                })
                
    return parsed_data