
import os
import sys

# Add the backend directory to the sys.path so we can import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from app.core.sheets_db import verify_sheets_structure
    from app.core.sheets_config import SHEETS_SCHEMA
    from app.services.google_sheets import google_sheets
    
    print("--- Canonical Schema Definition ---")
    for sheet, headers in SHEETS_SCHEMA.items():
        print(f"{sheet}: {headers}")
    print("----------------------------------\n")

    # Run the built-in verification
    verify_sheets_structure()
    
except Exception as e:
    print(f"\n❌ FAILED TO RUN VERIFICATION: {e}")
    import traceback
    traceback.print_exc()
