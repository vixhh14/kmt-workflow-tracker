#!/usr/bin/env python3
"""
Emergency Diagnostic - Check actual Google Sheets data RIGHT NOW
"""

import gspread
from google.oauth2.service_account import Credentials
import sys

SPREADSHEET_ID = "1ul_L4G-z-jkcUUYu4cCJfxtytpCx6bz5TeIJPjVuOz8"
SERVICE_ACCOUNT_FILE = "service_account.json"

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def connect():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)

def check_projects(spreadsheet):
    """Check Projects sheet"""
    print("\n" + "="*80)
    print("📊 PROJECTS CHECK")
    print("="*80)
    
    try:
        sheet = spreadsheet.worksheet("Projects")
        all_data = sheet.get_all_values()
        headers = all_data[0]
        
        print(f"\n📋 Headers: {headers}")
        
        is_deleted_col = headers.index('is_deleted') if 'is_deleted' in headers else -1
        name_col = headers.index('project_name') if 'project_name' in headers else 1
        
        print(f"\n📊 Projects in Google Sheets:")
        for row_idx, row in enumerate(all_data[1:], start=2):
            if name_col < len(row):
                name = row[name_col]
                is_deleted = row[is_deleted_col] if is_deleted_col >= 0 and is_deleted_col < len(row) else "false"
                status = "🗑️ DELETED" if str(is_deleted).lower() in ['true', '1', 'yes'] else "✅ ACTIVE"
                print(f"  Row {row_idx}: {name:20s} - {status} (is_deleted={is_deleted})")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_tasks(spreadsheet):
    """Check Tasks sheet"""
    print("\n" + "="*80)
    print("📊 TASKS CHECK")
    print("="*80)
    
    try:
        sheet = spreadsheet.worksheet("Tasks")
        all_data = sheet.get_all_values()
        headers = all_data[0]
        
        print(f"\n📋 Headers: {headers}")
        
        title_col = headers.index('title') if 'title' in headers else -1
        is_deleted_col = headers.index('is_deleted') if 'is_deleted' in headers else -1
        
        print(f"\n📊 Tasks in Google Sheets:")
        active_count = 0
        deleted_count = 0
        
        for row_idx, row in enumerate(all_data[1:], start=2):
            if title_col >= 0 and title_col < len(row):
                title = row[title_col]
                is_deleted = row[is_deleted_col] if is_deleted_col >= 0 and is_deleted_col < len(row) else "false"
                
                if str(is_deleted).lower() in ['true', '1', 'yes']:
                    deleted_count += 1
                    print(f"  Row {row_idx}: {title:20s} - 🗑️ DELETED")
                else:
                    active_count += 1
                    print(f"  Row {row_idx}: {title:20s} - ✅ ACTIVE")
        
        print(f"\n📊 Summary: {active_count} active, {deleted_count} deleted")
        
        if active_count == 0:
            print("❌ NO ACTIVE TASKS FOUND - This is why tasks page is empty!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_filing_tasks(spreadsheet):
    """Check Filing Tasks"""
    print("\n" + "="*80)
    print("📊 FILING TASKS CHECK")
    print("="*80)
    
    # Try to find the filing tasks sheet
    worksheets = spreadsheet.worksheets()
    filing_sheet = None
    
    for ws in worksheets:
        headers = ws.row_values(1)
        if 'filing_task_id' in [h.lower() for h in headers]:
            filing_sheet = ws
            print(f"✅ Found filing tasks in sheet: '{ws.title}'")
            break
    
    if not filing_sheet:
        print("❌ NO FILING TASKS SHEET FOUND!")
        return
    
    all_data = filing_sheet.get_all_values()
    headers = all_data[0]
    
    print(f"\n📋 Headers: {headers}")
    
    title_col = headers.index('title') if 'title' in [h.lower() for h in headers] else -1
    part_col = headers.index('part_item') if 'part_item' in [h.lower() for h in headers] else -1
    
    print(f"\n📊 Filing Tasks in Google Sheets:")
    for row_idx, row in enumerate(all_data[1:], start=2):
        if part_col >= 0 and part_col < len(row):
            part = row[part_col]
            title = row[title_col] if title_col >= 0 and title_col < len(row) else "NO TITLE"
            print(f"  Row {row_idx}: {part:15s} - Title: {title}")
    
    if len(all_data) == 1:
        print("❌ NO FILING TASKS FOUND - Sheet is empty!")

def check_units(spreadsheet):
    """Check Units"""
    print("\n" + "="*80)
    print("📊 UNITS CHECK")
    print("="*80)
    
    # Try to find units sheet
    worksheets = spreadsheet.worksheets()
    units_sheet = None
    
    for ws in worksheets:
        headers = ws.row_values(1)
        if 'unit_id' in [h.lower() for h in headers]:
            units_sheet = ws
            print(f"✅ Found units in sheet: '{ws.title}'")
            break
    
    if not units_sheet:
        print("❌ NO UNITS SHEET FOUND!")
        return
    
    all_data = units_sheet.get_all_values()
    headers = all_data[0]
    
    name_col = headers.index('name') if 'name' in [h.lower() for h in headers] else 1
    
    print(f"\n📊 Units in Google Sheets:")
    for row_idx, row in enumerate(all_data[1:], start=2):
        if name_col < len(row):
            name = row[name_col]
            if name in ['Unit A', 'Unit B', 'Unit C']:
                print(f"  Row {row_idx}: {name} ❌ OLD NAME (should be Unit 1/2)")
            else:
                print(f"  Row {row_idx}: {name} ✅")

def main():
    print("\n" + "="*80)
    print("🚨 EMERGENCY DIAGNOSTIC - CURRENT GOOGLE SHEETS STATE")
    print("="*80)
    
    spreadsheet = connect()
    
    check_projects(spreadsheet)
    check_tasks(spreadsheet)
    check_filing_tasks(spreadsheet)
    check_units(spreadsheet)
    
    print("\n" + "="*80)
    print("✅ DIAGNOSTIC COMPLETE")
    print("="*80)
    print("\nThis shows the ACTUAL current state of your Google Sheets.")
    print("If data looks wrong here, that's why the app isn't working!")
    print()

if __name__ == "__main__":
    main()
