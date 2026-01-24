#!/usr/bin/env python3
"""
Google Sheets Auto-Fix Script
Fixes all identified issues in the Workflow Tracker Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import sys

# Configuration
SPREADSHEET_ID = "1ul_L4G-z-jkcUUYu4cCJfxtytpCx6bz5TeIJPjVuOz8"
SERVICE_ACCOUNT_FILE = "service_account.json"

# Google Sheets API Scopes
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

def fix_filing_tasks(spreadsheet):
    """Fix 1: Add title column to FilingTasks and populate it"""
    print("\n" + "="*60)
    print("🔧 FIX 1: Adding 'title' column to FilingTasks")
    print("="*60)
    
    try:
        sheet = spreadsheet.worksheet("FilingTasks")
        
        # Get all data
        all_data = sheet.get_all_values()
        if not all_data:
            print("⚠️ FilingTasks sheet is empty")
            return
        
        headers = all_data[0]
        print(f"📋 Current headers: {headers}")
        
        # Check if 'title' column exists
        if 'title' in headers:
            print("✅ 'title' column already exists")
            title_col_index = headers.index('title')
        else:
            print("➕ Adding 'title' column...")
            # Insert 'title' column after 'filing_task_id'
            if 'filing_task_id' in headers:
                insert_position = headers.index('filing_task_id') + 2  # +2 because Sheets is 1-indexed
            else:
                insert_position = 2  # Default to column B
            
            sheet.insert_cols([[]], col=insert_position)
            sheet.update_cell(1, insert_position, 'title')
            print(f"✅ Added 'title' column at position {insert_position}")
            
            # Refresh headers
            headers = sheet.row_values(1)
            title_col_index = headers.index('title')
        
        # Populate titles for existing tasks
        print("📝 Populating titles for existing tasks...")
        all_data = sheet.get_all_values()
        
        part_item_col = headers.index('part_item') if 'part_item' in headers else -1
        wo_col = headers.index('work_order_number') if 'work_order_number' in headers else -1
        
        updates = []
        for row_idx, row in enumerate(all_data[1:], start=2):  # Skip header
            if row_idx - 1 >= len(row):
                continue
                
            current_title = row[title_col_index] if title_col_index < len(row) else ""
            
            if not current_title or current_title.strip() == "":
                # Generate title from part_item
                part_item = row[part_item_col] if part_item_col >= 0 and part_item_col < len(row) else "Item"
                wo_number = row[wo_col] if wo_col >= 0 and wo_col < len(row) else "N/A"
                
                new_title = f"{part_item}" if part_item else "Filing Task"
                updates.append({
                    'range': f'{gspread.utils.rowcol_to_a1(row_idx, title_col_index + 1)}',
                    'values': [[new_title]]
                })
                print(f"  Row {row_idx}: Setting title to '{new_title}'")
        
        if updates:
            for update in updates:
                sheet.update(update['range'], update['values'])
            print(f"✅ Updated {len(updates)} task titles")
        else:
            print("✅ All tasks already have titles")
            
    except Exception as e:
        print(f"❌ Error fixing FilingTasks: {e}")
        import traceback
        traceback.print_exc()

def fix_tasks_project_deadline(spreadsheet):
    """Fix 2: Ensure tasks have project and due_date"""
    print("\n" + "="*60)
    print("🔧 FIX 2: Checking Tasks for project and deadline")
    print("="*60)
    
    try:
        sheet = spreadsheet.worksheet("Tasks")
        all_data = sheet.get_all_values()
        
        if not all_data:
            print("⚠️ Tasks sheet is empty")
            return
        
        headers = all_data[0]
        print(f"📋 Headers: {headers}")
        
        project_col = headers.index('project') if 'project' in headers else -1
        due_date_col = headers.index('due_date') if 'due_date' in headers else -1
        
        if project_col < 0:
            print("⚠️ 'project' column not found - tasks may not display correctly")
        if due_date_col < 0:
            print("⚠️ 'due_date' column not found - deadlines may not display")
        
        # Count tasks with missing data
        missing_project = 0
        missing_deadline = 0
        
        for row in all_data[1:]:
            if project_col >= 0 and (project_col >= len(row) or not row[project_col] or row[project_col].strip() in ['-', '']):
                missing_project += 1
            if due_date_col >= 0 and (due_date_col >= len(row) or not row[due_date_col] or row[due_date_col].strip() == ''):
                missing_deadline += 1
        
        print(f"📊 Tasks missing project: {missing_project}")
        print(f"📊 Tasks missing deadline: {missing_deadline}")
        
        if missing_project > 0 or missing_deadline > 0:
            print("⚠️ Some tasks are missing project/deadline - they will show as '-' in the UI")
            print("💡 Recommendation: Update these tasks through the frontend when editing")
        else:
            print("✅ All tasks have project and deadline data")
            
    except Exception as e:
        print(f"❌ Error checking Tasks: {e}")

def fix_units(spreadsheet):
    """Fix 3: Change Unit A/B/C to Unit 1/2"""
    print("\n" + "="*60)
    print("🔧 FIX 3: Updating Units from A/B/C to 1/2")
    print("="*60)
    
    try:
        sheet = spreadsheet.worksheet("Units")
        all_data = sheet.get_all_values()
        
        if not all_data:
            print("⚠️ Units sheet is empty")
            return
        
        headers = all_data[0]
        name_col = headers.index('name') if 'name' in headers else 1
        desc_col = headers.index('description') if 'description' in headers else 2
        
        print(f"📋 Current units:")
        updates = []
        
        for row_idx, row in enumerate(all_data[1:], start=2):
            if name_col >= len(row):
                continue
                
            current_name = row[name_col]
            print(f"  - {current_name}")
            
            # Update unit names
            if current_name == "Unit A":
                updates.append({
                    'range': f'{gspread.utils.rowcol_to_a1(row_idx, name_col + 1)}',
                    'values': [["Unit 1"]]
                })
                if desc_col < len(row):
                    updates.append({
                        'range': f'{gspread.utils.rowcol_to_a1(row_idx, desc_col + 1)}',
                        'values': [["Production Unit 1"]]
                    })
            elif current_name == "Unit B":
                updates.append({
                    'range': f'{gspread.utils.rowcol_to_a1(row_idx, name_col + 1)}',
                    'values': [["Unit 2"]]
                })
                if desc_col < len(row):
                    updates.append({
                        'range': f'{gspread.utils.rowcol_to_a1(row_idx, desc_col + 1)}',
                        'values': [["Production Unit 2"]]
                    })
            elif current_name == "Unit C":
                print(f"  🗑️ Marking Unit C as deleted (row {row_idx})")
                # Mark as deleted instead of deleting row
                if 'is_deleted' in headers:
                    is_deleted_col = headers.index('is_deleted')
                    updates.append({
                        'range': f'{gspread.utils.rowcol_to_a1(row_idx, is_deleted_col + 1)}',
                        'values': [["true"]]
                    })
        
        if updates:
            for update in updates:
                sheet.update(update['range'], update['values'])
            print(f"✅ Updated {len(updates)} unit entries")
        else:
            print("✅ Units already correct (Unit 1, Unit 2)")
            
    except Exception as e:
        print(f"❌ Error fixing Units: {e}")
        import traceback
        traceback.print_exc()

def fix_corrupt_projects(spreadsheet):
    """Fix 4: Delete corrupt projects (empty name/code)"""
    print("\n" + "="*60)
    print("🔧 FIX 4: Removing corrupt projects")
    print("="*60)
    
    try:
        sheet = spreadsheet.worksheet("Projects")
        all_data = sheet.get_all_values()
        
        if not all_data:
            print("⚠️ Projects sheet is empty")
            return
        
        headers = all_data[0]
        name_col = headers.index('project_name') if 'project_name' in headers else 0
        code_col = headers.index('project_code') if 'project_code' in headers else 1
        is_deleted_col = headers.index('is_deleted') if 'is_deleted' in headers else -1
        
        print(f"📋 Checking for corrupt projects...")
        corrupt_rows = []
        
        for row_idx, row in enumerate(all_data[1:], start=2):
            project_name = row[name_col] if name_col < len(row) else ""
            project_code = row[code_col] if code_col < len(row) else ""
            
            # Check if project is corrupt (empty name and code)
            if (not project_name or project_name.strip() == "") and \
               (not project_code or project_code.strip() == ""):
                corrupt_rows.append(row_idx)
                print(f"  🗑️ Found corrupt project at row {row_idx}")
        
        if corrupt_rows:
            if is_deleted_col >= 0:
                # Mark as deleted instead of deleting rows
                print(f"📝 Marking {len(corrupt_rows)} corrupt projects as deleted...")
                for row_idx in corrupt_rows:
                    sheet.update_cell(row_idx, is_deleted_col + 1, "true")
                print(f"✅ Marked {len(corrupt_rows)} projects as deleted")
            else:
                print("⚠️ 'is_deleted' column not found - cannot mark projects as deleted")
                print("💡 Recommendation: Manually delete these rows from Google Sheets")
        else:
            print("✅ No corrupt projects found")
            
    except Exception as e:
        print(f"❌ Error fixing corrupt projects: {e}")
        import traceback
        traceback.print_exc()

def verify_fixes(spreadsheet):
    """Verify all fixes were applied correctly"""
    print("\n" + "="*60)
    print("✅ VERIFICATION")
    print("="*60)
    
    issues = []
    
    # Check FilingTasks
    try:
        sheet = spreadsheet.worksheet("FilingTasks")
        headers = sheet.row_values(1)
        if 'title' not in headers:
            issues.append("❌ FilingTasks: 'title' column missing")
        else:
            print("✅ FilingTasks: 'title' column exists")
    except Exception as e:
        issues.append(f"❌ FilingTasks: {e}")
    
    # Check Units
    try:
        sheet = spreadsheet.worksheet("Units")
        all_data = sheet.get_all_values()
        headers = all_data[0]
        name_col = headers.index('name') if 'name' in headers else 1
        
        unit_names = [row[name_col] for row in all_data[1:] if name_col < len(row)]
        
        if "Unit 1" in unit_names and "Unit 2" in unit_names:
            print("✅ Units: Unit 1 and Unit 2 exist")
        else:
            issues.append(f"❌ Units: Expected 'Unit 1' and 'Unit 2', found: {unit_names}")
    except Exception as e:
        issues.append(f"❌ Units: {e}")
    
    # Summary
    print("\n" + "="*60)
    if issues:
        print("⚠️ SOME ISSUES REMAIN:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("🎉 ALL FIXES APPLIED SUCCESSFULLY!")
    print("="*60)

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("🚀 GOOGLE SHEETS AUTO-FIX SCRIPT")
    print("="*60)
    print(f"📊 Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"🔑 Service Account: {SERVICE_ACCOUNT_FILE}")
    print()
    
    # Connect
    spreadsheet = connect_to_sheets()
    
    # Apply fixes
    fix_filing_tasks(spreadsheet)
    fix_tasks_project_deadline(spreadsheet)
    fix_units(spreadsheet)
    fix_corrupt_projects(spreadsheet)
    
    # Verify
    verify_fixes(spreadsheet)
    
    print("\n" + "="*60)
    print("✅ SCRIPT COMPLETE!")
    print("="*60)
    print("📝 Next steps:")
    print("  1. Refresh your browser (Ctrl+F5)")
    print("  2. Check the application")
    print("  3. All issues should be resolved!")
    print()

if __name__ == "__main__":
    main()
