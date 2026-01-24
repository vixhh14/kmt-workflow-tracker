#!/usr/bin/env python3
"""
Fix Tasks Sheet - Add project and due_date columns
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

def connect_to_sheets():
    """Connect to Google Sheets"""
    print("🔐 Authenticating...")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)

def fix_tasks_sheet(spreadsheet):
    """Fix Tasks sheet to add project and due_date columns"""
    print("\n" + "="*60)
    print("🔧 FIXING TASKS SHEET")
    print("="*60)
    
    try:
        sheet = spreadsheet.worksheet("Tasks")
        headers = sheet.row_values(1)
        
        print(f"\n📋 Current headers:")
        for i, h in enumerate(headers, 1):
            print(f"  {i}. {h}")
        
        # Check what we have
        has_project = 'project' in headers
        has_project_id = 'project_id' in headers
        has_due_date = 'due_date' in headers
        has_due_datetime = 'due_datetime' in headers
        
        print(f"\n📊 Column Status:")
        print(f"  'project' column: {'✅ EXISTS' if has_project else '❌ MISSING'}")
        print(f"  'project_id' column: {'✅ EXISTS' if has_project_id else '❌ MISSING'}")
        print(f"  'due_date' column: {'✅ EXISTS' if has_due_date else '❌ MISSING'}")
        print(f"  'due_datetime' column: {'✅ EXISTS' if has_due_datetime else '❌ MISSING'}")
        
        changes_made = False
        
        # Add 'project' column if missing
        if not has_project:
            print(f"\n➕ Adding 'project' column...")
            # Insert after project_id if it exists, otherwise at position 3
            if has_project_id:
                insert_pos = headers.index('project_id') + 2
            else:
                insert_pos = 3
            
            sheet.insert_cols([[]], col=insert_pos)
            sheet.update_cell(1, insert_pos, 'project')
            print(f"✅ Added 'project' column at position {insert_pos}")
            changes_made = True
            
            # Refresh headers
            headers = sheet.row_values(1)
        
        # Add 'due_date' column if missing
        if not has_due_date:
            print(f"\n➕ Adding 'due_date' column...")
            # Insert after due_datetime if it exists, otherwise at a reasonable position
            if has_due_datetime:
                insert_pos = headers.index('due_datetime') + 2
            else:
                insert_pos = len(headers) + 1
            
            sheet.insert_cols([[]], col=insert_pos)
            sheet.update_cell(1, insert_pos, 'due_date')
            print(f"✅ Added 'due_date' column at position {insert_pos}")
            changes_made = True
            
            # Refresh headers
            headers = sheet.row_values(1)
        
        # Now populate the columns if they were just added
        if changes_made:
            print(f"\n📝 Populating new columns...")
            all_data = sheet.get_all_values()
            
            project_col = headers.index('project') if 'project' in headers else -1
            project_id_col = headers.index('project_id') if 'project_id' in headers else -1
            due_date_col = headers.index('due_date') if 'due_date' in headers else -1
            due_datetime_col = headers.index('due_datetime') if 'due_datetime' in headers else -1
            
            # Get projects for lookup
            try:
                projects_sheet = spreadsheet.worksheet("Projects")
                projects_data = projects_sheet.get_all_values()
                projects_headers = projects_data[0]
                
                project_id_idx = projects_headers.index('project_id') if 'project_id' in projects_headers else 0
                project_name_idx = projects_headers.index('project_name') if 'project_name' in projects_headers else 1
                
                project_map = {}
                for row in projects_data[1:]:
                    if project_id_idx < len(row) and project_name_idx < len(row):
                        pid = row[project_id_idx]
                        pname = row[project_name_idx]
                        if pid and pname:
                            project_map[pid] = pname
                
                print(f"  📊 Loaded {len(project_map)} projects for lookup")
            except Exception as e:
                print(f"  ⚠️ Could not load projects: {e}")
                project_map = {}
            
            # Update rows
            updates = []
            for row_idx, row in enumerate(all_data[1:], start=2):
                # Populate 'project' from 'project_id'
                if project_col >= 0 and project_id_col >= 0:
                    current_project = row[project_col] if project_col < len(row) else ""
                    if not current_project or current_project == "-":
                        project_id = row[project_id_col] if project_id_col < len(row) else ""
                        if project_id and project_id in project_map:
                            project_name = project_map[project_id]
                            updates.append({
                                'range': f'{gspread.utils.rowcol_to_a1(row_idx, project_col + 1)}',
                                'values': [[project_name]]
                            })
                            print(f"  Row {row_idx}: project = '{project_name}'")
                
                # Copy 'due_datetime' to 'due_date' if needed
                if due_date_col >= 0 and due_datetime_col >= 0:
                    current_due_date = row[due_date_col] if due_date_col < len(row) else ""
                    if not current_due_date:
                        due_datetime = row[due_datetime_col] if due_datetime_col < len(row) else ""
                        if due_datetime:
                            updates.append({
                                'range': f'{gspread.utils.rowcol_to_a1(row_idx, due_date_col + 1)}',
                                'values': [[due_datetime]]
                            })
                            print(f"  Row {row_idx}: due_date = '{due_datetime}'")
            
            # Apply updates
            if updates:
                print(f"\n📤 Applying {len(updates)} updates...")
                for update in updates:
                    sheet.update(update['range'], update['values'])
                print(f"✅ Updated {len(updates)} cells")
            else:
                print(f"✅ No updates needed")
        
        print(f"\n✅ Tasks sheet is now properly configured!")
        print(f"\n📋 Final headers:")
        final_headers = sheet.row_values(1)
        for i, h in enumerate(final_headers, 1):
            if h in ['project', 'due_date']:
                print(f"  {i}. {h} ✅")
            else:
                print(f"  {i}. {h}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("\n" + "="*60)
    print("🚀 TASKS SHEET FIX SCRIPT")
    print("="*60)
    
    spreadsheet = connect_to_sheets()
    fix_tasks_sheet(spreadsheet)
    
    print("\n" + "="*60)
    print("✅ COMPLETE!")
    print("="*60)
    print("📝 Next steps:")
    print("  1. Refresh your browser")
    print("  2. Tasks should now show project and deadline")
    print()

if __name__ == "__main__":
    main()
