
import os
import re

def fix_env_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Fixing {filepath}...")
    with open(filepath, 'r') as f:
        content = f.read()

    # Regex to find GOOGLE_SHEETS_JSON=... and handle multi-line or unquoted
    # This is a bit complex to do perfectly with regex, so let's do line processing state machine
    
    lines = content.splitlines()
    new_lines = []
    
    buffer = ""
    is_capturing_json = False
    
    for line in lines:
        stripped = line.strip()
        
        # Detect start of the variable
        if stripped.startswith("GOOGLE_SHEETS_JSON=") or is_capturing_json:
            if stripped.startswith("GOOGLE_SHEETS_JSON="):
                is_capturing_json = True
                # Remove prefix
                val_start = stripped.find("=") + 1
                buffer = stripped[val_start:]
            else:
                buffer += " " + stripped
            
            # Check if it looks like we reached the end
            # Heuristic: ends with '}' or '}' followed by quote
            if buffer.strip().endswith("}") or buffer.strip().endswith("}'") or buffer.strip().endswith('}"'):
                is_capturing_json = False
                
                # Cleanup the buffer
                clean_json = buffer.strip()
                # Remove outer quotes if they exist and are matching
                if (clean_json.startswith("'") and clean_json.endswith("'")) or \
                   (clean_json.startswith('"') and clean_json.endswith('"')):
                    clean_json = clean_json[1:-1]
                
                # IMPORTANT: Escape existing single quotes because we will wrap in single quotes
                clean_json_escaped = clean_json.replace("'", "\\'")
                
                # Reconstruct the line
                new_lines.append(f"GOOGLE_SHEETS_JSON='{clean_json_escaped}'")
                buffer = ""
            continue
            
        new_lines.append(line)
        
    with open(filepath, 'w') as f:
        f.write("\n".join(new_lines))
    print(f"Fixed {filepath}")

fix_env_file('.env')
fix_env_file('.env.production')
