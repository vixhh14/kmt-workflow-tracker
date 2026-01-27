
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

try:
    from app.core.sheets_db import verify_sheets_structure
    print("Running verify_sheets_structure()...")
    verify_sheets_structure()
    print("SUCCESS: verify_sheets_structure() completed without errors.")
except Exception as e:
    print(f"FAILURE: verify_sheets_structure() failed with: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
