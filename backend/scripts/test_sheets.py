
import os
import sys

# Add backend to path
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_path)

from app.services.google_sheets import google_sheets

def test_connection():
    print("🔍 Testing Google Sheets Connection...")
    try:
        ss = google_sheets._get_spreadsheet()
        print(f"✅ Connected to Spreadsheet: {ss.title}")
        
        worksheets = ss.worksheets()
        print("\n📊 Available Worksheets:")
        for ws in worksheets:
            print(f" - {ws.title}")
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
