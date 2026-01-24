#!/usr/bin/env python3
"""
Google Sheets Discovery and Fix Script
First discovers actual sheet names, then applies fixes
"""

import gspread
from google.oauth2.service_account import Credentials
import sys

# Configuration
SPREADSHEET_ID = "1ul_L4G-z-jkcUUYu4cCJfxtytpCx6bz5TeIJPjVuOz8"
SERVICE_ACCOUNT_FILE = "service_account.json"

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def connect_to_sheets():
    """Connect to Google Sheets"""
    print("🔐 Authenticating with Google Sheets...")
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        print("✅ Connected successfully!")
        return spreadsheet
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

def discover_sheets(spreadsheet):
    """Discover all sheet names"""
    print("\n" + "="*60)
    print("🔍 DISCOVERING SHEETS")
    print("="*60)
    
    worksheets = spreadsheet.worksheets()
    print(f"\n📊 Found {len(worksheets)} sheets:")
    
    sheet_info = {}
    for ws in worksheets:
        print(f"\n  📄 Sheet: '{ws.title}'")
        try:
            headers = ws.row_values(1)
            print(f"     Headers: {headers[:5]}...")  # Show first 5 headers
            sheet_info[ws.title] = {
                'worksheet': ws,
                'headers': headers
            }
        except Exception as e:
            print(f"     ⚠️ Could not read headers: {e}")
    
    return sheet_info

def fix_filing_tasks_sheet(sheet_info):
    """Fix filing tasks - find the correct sheet name"""
    print("\n" + "="*60)
    print("🔧 FIX 1: Filing Tasks")
    print("="*60)
    
    # Find sheet with filing_task_id
    filing_sheet = None
    for name, info in sheet_info.items():
        if 'filing_task_id' in info['headers']:
            filing_sheet = info
            print(f"✅ Found filing tasks sheet: '{name}'")
            break
    
    if not filing_sheet:
        print("⚠️ No filing tasks sheet found")
        return
    
    ws = filing_sheet['worksheet']
    headers = filing_sheet['headers']
    
    # Check if title column exists
    if 'title' in headers:
        print("✅ 'title' column already exists")
        return
    
    print("➕ Adding 'title' column...")
    try:
        # Insert after filing_task_id
        insert_pos = headers.index('filing_task_id') + 2
        ws.insert_cols([[]], col=insert_pos)
        ws.update_cell(1, insert_pos, 'title')
        
        # Populate titles
        all_data = ws.get_all_values()
        part_col = headers.index('part_item') if 'part_item' in headers else -1
        
        for row_idx, row in enumerate(all_data[1:], start=2):
            if part_col >= 0 and part_col < len(row):
                title = row[part_col] if row[part_col] else "Filing Task"
                ws.update_cell(row_idx, insert_pos, title)
                print(f"  Row {row_idx}: '{title}'")
        
        print("✅ Added and populated 'title' column")
    except Exception as e:
        print(f"❌ Error: {e}")

def fix_units_sheet(sheet_info):
    """Fix units - find the correct sheet name"""
    print("\n" + "="*60)
    print("🔧 FIX 2: Units")
    print("="*60)
    
    # Find sheet with unit_id or name='Unit A/B/C'
    units_sheet = None
    for name, info in sheet_info.items():
        if 'unit_id' in info['headers'] or name.lower() == 'units':
            units_sheet = info
            print(f"✅ Found units sheet: '{name}'")
            break
    
    if not units_sheet:
        print("⚠️ No units sheet found")
        return
    
    ws = units_sheet['worksheet']
    headers = units_sheet['headers']
    all_data = ws.get_all_values()
    
    name_col = headers.index('name') if 'name' in headers else 1
    desc_col = headers.index('description') if 'description' in headers else 2
    
    print(f"📋 Current units:")
    for row_idx, row in enumerate(all_data[1:], start=2):
        if name_col < len(row):
            current_name = row[name_col]
            print(f"  - {current_name}")
            
            if current_name == "Unit A":
                ws.update_cell(row_idx, name_col + 1, "Unit 1")
                if desc_col < len(row):
                    ws.update_cell(row_idx, desc_col + 1, "Production Unit 1")
                print(f"    ✅ Changed to 'Unit 1'")
            elif current_name == "Unit B":
                ws.update_cell(row_idx, name_col + 1, "Unit 2")
                if desc_col < len(row):
                    ws.update_cell(row_idx, desc_col + 1, "Production Unit 2")
                print(f"    ✅ Changed to 'Unit 2'")
            elif current_name == "Unit C":
                if 'is_deleted' in headers:
                    is_deleted_col = headers.index('is_deleted')
                    ws.update_cell(row_idx, is_deleted_col + 1, "true")
                    print(f"    🗑️ Marked as deleted")
    
    print("✅ Units updated")

def fix_tasks_columns(sheet_info):
    """Fix tasks - add 'project' and 'due_date' columns if missing"""
    print("\n" + "="*60)
    print("🔧 FIX 3: Tasks Columns")
    print("="*60)
    
    # Find tasks sheet
    tasks_sheet = None
    for name, info in sheet_info.items():
        if 'task_id' in info['headers'] and name.lower() in ['tasks', 'task']:
            tasks_sheet = info
            print(f"✅ Found tasks sheet: '{name}'")
            break
    
    if not tasks_sheet:
        print("⚠️ No tasks sheet found")
        return
    
    ws = tasks_sheet['worksheet']
    headers = tasks_sheet['headers']
    
    print(f"📋 Current headers: {headers}")
    
    # Check for 'project' column
    if 'project' not in headers:
        if 'project_id' in headers:
            print("⚠️ Has 'project_id' but missing 'project' column")
            print("💡 Backend will use project_id to resolve project name")
        else:
            print("❌ Missing both 'project' and 'project_id'")
    else:
        print("✅ 'project' column exists")
    
    # Check for 'due_date' column
    if 'due_date' not in headers:
        if 'due_datetime' in headers:
            print("⚠️ Has 'due_datetime' instead of 'due_date'")
            print("💡 Backend should accept 'due_datetime' as well")
        else:
            print("❌ Missing 'due_date' column")
    else:
        print("✅ 'due_date' column exists")

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("🚀 GOOGLE SHEETS DISCOVERY & FIX SCRIPT")
    print("="*60)
    
    # Connect
    spreadsheet = connect_to_sheets()
    
    # Discover sheets
    sheet_info = discover_sheets(spreadsheet)
    
    # Apply fixes
    fix_filing_tasks_sheet(sheet_info)
    fix_units_sheet(sheet_info)
    fix_tasks_columns(sheet_info)
    
    print("\n" + "="*60)
    print("✅ SCRIPT COMPLETE!")
    print("="*60)
    print("📝 Next steps:")
    print("  1. Refresh your browser (Ctrl+F5)")
    print("  2. Check the application")
    print("  3. Issues should be resolved!")
    print()

if __name__ == "__main__":
    main()
