import os

def clean_env_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Cleaning {filepath}...")
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    json_buffer = ""
    in_json = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check for start of JSON key
        if stripped.startswith("GOOGLE_SHEETS_JSON="):
            # If it's a one-liner already
            if stripped.endswith("}") and not stripped.endswith("=}"): # simple check
                 # Check if quoted
                 val = stripped.split("=", 1)[1]
                 if not (val.startswith("'") or val.startswith('"')):
                     # Wrap in single quotes
                     cleaned_lines.append(f"GOOGLE_SHEETS_JSON='{val}'\n")
                 else:
                     cleaned_lines.append(line)
                 continue
            
            # Start capturing multi-line
            in_json = True
            json_buffer = stripped.split("=", 1)[1] # Get content after =
            continue
            
        if in_json:
            json_buffer += stripped
            if stripped.endswith("}"):
                in_json = False
                # We have the full JSON string in buffer. 
                # It likely contains double quotes internally. 
                # We should wrap it in single quotes.
                # Also escape any single quotes inside just in case (rare for JSON)
                json_buffer = json_buffer.replace("'", "\\'")
                cleaned_lines.append(f"GOOGLE_SHEETS_JSON='{json_buffer}'\n")
            continue
            
        cleaned_lines.append(line)
        
    with open(filepath, 'w') as f:
        f.writelines(cleaned_lines)
    print(f"Finished cleaning {filepath}")

# Paths assuming script runs from backend/ directory or root? 
# Current CWD is backend/. So paths are .env and .env.production
clean_env_file('.env')
clean_env_file('.env.production')
