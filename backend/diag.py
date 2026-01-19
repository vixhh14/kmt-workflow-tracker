import sys
import os
import json

# Add backend to path
sys.path.append(os.getcwd())

try:
    from app.services.google_sheets import google_sheets
    print("Testing Google Sheets connection...")
    
    results = {}
    sheets = ["users", "machines"]
    for s in sheets:
        try:
            ws = google_sheets.get_worksheet(s)
            headers = ws.row_values(1)
            results[s] = {"status": "ok", "headers": headers}
        except Exception as e:
            results[s] = {"status": "error", "message": str(e)}
            
    with open("connection_results.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Results written to connection_results.json")
except Exception as e:
    with open("connection_error.txt", "w") as f:
        f.write(str(e))
    print(f"Critical error: {e}")
