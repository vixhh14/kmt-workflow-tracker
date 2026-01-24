#!/usr/bin/env python3
"""
COMPREHENSIVE FIX - Fix ALL Google Sheets issues at once
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
    print("🔐 Connecting...")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)

def fix_filing_tasks(spreadsheet):
    """Add title column to filing tasks"""
    print("\n" + "="*80)
    print("🔧 FIX 1: Adding 'title' column to Filing Tasks")
    print("="*80)
    
    try:
        sheet = spreadsheet.worksheet("filingtasks")
        headers = sheet.row_values(1)
        
        if 'title' in headers:
            print("✅ 'title' column already exists")
            return
        
        # Insert title column at position 2 (after filing_task_id)
        print("➕ Inserting 'title' column...")
        sheet.insert_cols([[]], col=2)
        sheet.update_cell(1, 2, 'title')
        
        # Populate titles from part_item
        all_data = sheet.get_all_values()
        headers = sheet.row_values(1)  # Refresh headers
        
        part_col = headers.index('part_item') if 'part_item' in headers else -1
        
        for row_idx in range(2, len(all_data) + 1):
            row = sheet.row_values(row_idx)
            if part_col >= 0 and part_col < len(row):
                part = row[part_col]
                title = part if part else "Filing Task"
                sheet.update_cell(row_idx, 2, title)
                print(f"  Row {row_idx}: title = '{title}'")
        
        print("✅ Added 'title' column to filing tasks")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def fix_tasks_columns(spreadsheet):
    """Add project and due_date columns to Tasks"""
    print("\n" + "="*80)
    print("🔧 FIX 2: Adding 'project' and 'due_date' columns to Tasks")
    print("="*80)
    
    try:
        sheet = spreadsheet.worksheet("Tasks")
        headers = sheet.row_values(1)
        
        # Add 'project' column if missing
        if 'project' not in headers:
            print("➕ Adding 'project' column...")
            # Insert after project_id (position 3)
            project_id_pos = headers.index('project_id') + 1 if 'project_id' in headers else 3
            sheet.insert_cols([[]], col=project_id_pos + 1)
            sheet.update_cell(1, project_id_pos + 1, 'project')
            print(f"✅ Added 'project' column at position {project_id_pos + 1}")
            
            # Refresh headers
            headers = sheet.row_values(1)
        
        # Add 'due_date' column if missing
        if 'due_date' not in headers:
            print("➕ Adding 'due_date' column...")
            # Insert after due_datetime
            due_datetime_pos = headers.index('due_datetime') + 1 if 'due_datetime' in headers else 8
            sheet.insert_cols([[]], col=due_datetime_pos + 1)
            sheet.update_cell(1, due_datetime_pos + 1, 'due_date')
            print(f"✅ Added 'due_date' column at position {due_datetime_pos + 1}")
            
            # Refresh headers
            headers = sheet.row_values(1)
        
        # Now populate the columns
        print("\n📝 Populating columns...")
        all_data = sheet.get_all_values()
        headers = sheet.row_values(1)
        
        project_col = headers.index('project')
        project_id_col = headers.index('project_id') if 'project_id' in headers else -1
        due_date_col = headers.index('due_date')
        due_datetime_col = headers.index('due_datetime') if 'due_datetime' in headers else -1
        
        # Get projects for lookup
        try:
            projects_sheet = spreadsheet.worksheet("Projects")
            projects_data = projects_sheet.get_all_values()
            projects_headers = projects_data[0]
            
            pid_idx = projects_headers.index('project_id')
            pname_idx = projects_headers.index('project_name')
            
            project_map = {}
            for row in projects_data[1:]:
                if pid_idx < len(row) and pname_idx < len(row):
                    project_map[row[pid_idx]] = row[pname_idx]
            
            print(f"  📊 Loaded {len(project_map)} projects")
        except:
            project_map = {}
        
        # Update each task row
        for row_idx in range(2, len(all_data) + 1):
            row = sheet.row_values(row_idx)
            
            # Populate project from project_id
            if project_id_col >= 0 and project_id_col < len(row):
                project_id = row[project_id_col]
                if project_id in project_map:
                    project_name = project_map[project_id]
                    sheet.update_cell(row_idx, project_col + 1, project_name)
                    print(f"  Row {row_idx}: project = '{project_name}'")
            
            # Copy due_datetime to due_date
            if due_datetime_col >= 0 and due_datetime_col < len(row):
                due_datetime = row[due_datetime_col]
                if due_datetime:
                    sheet.update_cell(row_idx, due_date_col + 1, due_datetime)
                    print(f"  Row {row_idx}: due_date = '{due_datetime}'")
        
        print("✅ Populated 'project' and 'due_date' columns")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def fix_unit_c(spreadsheet):
    """Delete Unit C"""
    print("\n" + "="*80)
    print("🔧 FIX 3: Removing Unit C")
    print("="*80)
    
    try:
        sheet = spreadsheet.worksheet("units")
        all_data = sheet.get_all_values()
        headers = all_data[0]
        
        name_col = headers.index('name') if 'name' in headers else 1
        is_deleted_col = headers.index('is_deleted') if 'is_deleted' in headers else -1
        
        for row_idx, row in enumerate(all_data[1:], start=2):
            if name_col < len(row) and row[name_col] == "Unit C":
                if is_deleted_col >= 0:
                    sheet.update_cell(row_idx, is_deleted_col + 1, "true")
                    print(f"✅ Marked Unit C as deleted (row {row_idx})")
                else:
                    print(f"⚠️ No is_deleted column, deleting row {row_idx}")
                    sheet.delete_rows(row_idx)
                    print(f"✅ Deleted Unit C row")
                break
        
    except Exception as e:
        print(f"❌ Error: {e}")

def verify_fixes(spreadsheet):
    """Verify all fixes"""
    print("\n" + "="*80)
    print("✅ VERIFICATION")
    print("="*80)
    
    issues = []
    
    # Check filing tasks
    try:
        sheet = spreadsheet.worksheet("filingtasks")
        headers = sheet.row_values(1)
        if 'title' not in headers:
            issues.append("❌ Filing tasks: 'title' column still missing")
        else:
            print("✅ Filing tasks: 'title' column exists")
    except Exception as e:
        issues.append(f"❌ Filing tasks: {e}")
    
    # Check tasks
    try:
        sheet = spreadsheet.worksheet("Tasks")
        headers = sheet.row_values(1)
        if 'project' not in headers:
            issues.append("❌ Tasks: 'project' column still missing")
        else:
            print("✅ Tasks: 'project' column exists")
        
        if 'due_date' not in headers:
            issues.append("❌ Tasks: 'due_date' column still missing")
        else:
            print("✅ Tasks: 'due_date' column exists")
    except Exception as e:
        issues.append(f"❌ Tasks: {e}")
    
    # Check units
    try:
        sheet = spreadsheet.worksheet("units")
        all_data = sheet.get_all_values()
        headers = all_data[0]
        name_col = headers.index('name') if 'name' in headers else 1
        
        unit_names = [row[name_col] for row in all_data[1:] if name_col < len(row)]
        
        if "Unit C" in unit_names:
            issues.append("❌ Units: Unit C still exists")
        else:
            print("✅ Units: Unit C removed")
    except Exception as e:
        issues.append(f"❌ Units: {e}")
    
    if issues:
        print("\n⚠️ ISSUES REMAINING:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n🎉 ALL FIXES APPLIED SUCCESSFULLY!")
    
    return len(issues) == 0

def main():
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE GOOGLE SHEETS FIX")
    print("="*80)
    
    spreadsheet = connect()
    
    # Apply all fixes
    fix_filing_tasks(spreadsheet)
    fix_tasks_columns(spreadsheet)
    fix_unit_c(spreadsheet)
    
    # Verify
    success = verify_fixes(spreadsheet)
    
    print("\n" + "="*80)
    if success:
        print("✅ ALL FIXES COMPLETE!")
        print("="*80)
        print("\n📝 Next steps:")
        print("  1. Refresh your browser (Ctrl+F5)")
        print("  2. Tasks should now show with project and deadline")
        print("  3. Filing tasks should appear")
        print("  4. Everything should work!")
    else:
        print("⚠️ SOME ISSUES REMAIN")
        print("="*80)
        print("\nPlease check the errors above.")
    print()

if __name__ == "__main__":
    main()
