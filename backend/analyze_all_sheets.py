#!/usr/bin/env python3
"""
Google Sheets Complete Analysis
Discovers all sheets and their structure to align with application
"""

import gspread
from google.oauth2.service_account import Credentials
import sys
from collections import defaultdict

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
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        print("✅ Connected successfully!")
        return spreadsheet
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

def analyze_all_sheets(spreadsheet):
    """Analyze all sheets in the spreadsheet"""
    print("\n" + "="*80)
    print("📊 COMPLETE GOOGLE SHEETS ANALYSIS")
    print("="*80)
    
    worksheets = spreadsheet.worksheets()
    print(f"\n📄 Total Sheets Found: {len(worksheets)}")
    
    sheet_analysis = {}
    
    for idx, ws in enumerate(worksheets, 1):
        print(f"\n{'='*80}")
        print(f"📄 SHEET #{idx}: '{ws.title}'")
        print(f"{'='*80}")
        
        try:
            # Get all data
            all_data = ws.get_all_values()
            
            if not all_data:
                print("  ⚠️ Sheet is empty")
                continue
            
            headers = all_data[0]
            data_rows = all_data[1:]
            
            print(f"\n📋 Headers ({len(headers)} columns):")
            for i, header in enumerate(headers, 1):
                print(f"  {i:2d}. {header}")
            
            print(f"\n📊 Data Statistics:")
            print(f"  Total rows (excluding header): {len(data_rows)}")
            
            # Count non-empty rows
            non_empty = sum(1 for row in data_rows if any(cell.strip() for cell in row if cell))
            print(f"  Non-empty rows: {non_empty}")
            
            # Sample data (first 3 rows)
            if data_rows:
                print(f"\n📝 Sample Data (first 3 rows):")
                for row_idx, row in enumerate(data_rows[:3], 1):
                    print(f"\n  Row {row_idx}:")
                    for col_idx, (header, value) in enumerate(zip(headers, row), 1):
                        if value and value.strip():
                            display_value = value[:50] + "..." if len(value) > 50 else value
                            print(f"    {header}: {display_value}")
            
            # Identify sheet type based on headers
            sheet_type = identify_sheet_type(headers)
            print(f"\n🔍 Identified as: {sheet_type}")
            
            # Store analysis
            sheet_analysis[ws.title] = {
                'worksheet': ws,
                'headers': headers,
                'row_count': len(data_rows),
                'non_empty_count': non_empty,
                'type': sheet_type
            }
            
        except Exception as e:
            print(f"  ❌ Error analyzing sheet: {e}")
    
    return sheet_analysis

def identify_sheet_type(headers):
    """Identify what type of data this sheet contains"""
    headers_lower = [h.lower() for h in headers]
    
    if 'task_id' in headers_lower:
        return "TASKS (General Tasks)"
    elif 'filing_task_id' in headers_lower:
        return "FILING TASKS"
    elif 'fabrication_task_id' in headers_lower:
        return "FABRICATION TASKS"
    elif 'project_id' in headers_lower and 'project_name' in headers_lower:
        return "PROJECTS"
    elif 'user_id' in headers_lower and 'username' in headers_lower:
        return "USERS"
    elif 'machine_id' in headers_lower and 'machine_name' in headers_lower:
        return "MACHINES"
    elif 'unit_id' in headers_lower:
        return "UNITS"
    elif 'attendance_id' in headers_lower:
        return "ATTENDANCE"
    elif 'category_id' in headers_lower and 'category_name' in headers_lower:
        return "MACHINE CATEGORIES"
    else:
        return "UNKNOWN / OTHER"

def check_required_columns(sheet_analysis):
    """Check if required columns exist for each sheet type"""
    print("\n" + "="*80)
    print("🔍 REQUIRED COLUMNS CHECK")
    print("="*80)
    
    required_columns = {
        "TASKS (General Tasks)": {
            'must_have': ['task_id', 'title', 'status', 'priority'],
            'should_have': ['project', 'project_id', 'due_date', 'assigned_to'],
            'optional': ['description', 'part_item', 'machine_id']
        },
        "FILING TASKS": {
            'must_have': ['filing_task_id', 'title'],
            'should_have': ['project_id', 'part_item', 'status'],
            'optional': ['work_order_number', 'quantity']
        },
        "FABRICATION TASKS": {
            'must_have': ['fabrication_task_id', 'title'],
            'should_have': ['project_id', 'part_item', 'status'],
            'optional': ['work_order_number', 'quantity']
        },
        "PROJECTS": {
            'must_have': ['project_id', 'project_name', 'project_code'],
            'should_have': ['is_deleted', 'created_at'],
            'optional': ['client_name', 'description']
        },
        "USERS": {
            'must_have': ['user_id', 'username', 'role'],
            'should_have': ['email', 'approval_status', 'is_deleted'],
            'optional': ['unit_id', 'contact_number']
        },
        "UNITS": {
            'must_have': ['unit_id', 'name'],
            'should_have': ['description', 'status'],
            'optional': ['is_deleted']
        }
    }
    
    for sheet_name, info in sheet_analysis.items():
        sheet_type = info['type']
        
        if sheet_type in required_columns:
            print(f"\n📄 {sheet_name} ({sheet_type}):")
            headers_lower = [h.lower() for h in info['headers']]
            
            reqs = required_columns[sheet_type]
            
            # Check must-have columns
            print(f"\n  ✅ MUST HAVE:")
            for col in reqs['must_have']:
                if col.lower() in headers_lower:
                    print(f"    ✅ {col}")
                else:
                    print(f"    ❌ {col} - MISSING!")
            
            # Check should-have columns
            print(f"\n  ⚠️ SHOULD HAVE:")
            for col in reqs['should_have']:
                if col.lower() in headers_lower:
                    print(f"    ✅ {col}")
                else:
                    print(f"    ⚠️ {col} - Missing (recommended)")

def generate_recommendations(sheet_analysis):
    """Generate recommendations for fixing issues"""
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80)
    
    recommendations = []
    
    for sheet_name, info in sheet_analysis.items():
        sheet_type = info['type']
        headers_lower = [h.lower() for h in info['headers']]
        
        # Check Tasks sheet
        if sheet_type == "TASKS (General Tasks)":
            if 'project' not in headers_lower:
                recommendations.append(f"❌ {sheet_name}: Add 'project' column for project names")
            if 'due_date' not in headers_lower and 'due_datetime' not in headers_lower:
                recommendations.append(f"❌ {sheet_name}: Add 'due_date' column for deadlines")
        
        # Check Filing Tasks
        if sheet_type == "FILING TASKS":
            if 'title' not in headers_lower:
                recommendations.append(f"❌ {sheet_name}: Add 'title' column for task titles")
        
        # Check Fabrication Tasks
        if sheet_type == "FABRICATION TASKS":
            if 'title' not in headers_lower:
                recommendations.append(f"❌ {sheet_name}: Add 'title' column for task titles")
        
        # Check Units
        if sheet_type == "UNITS":
            # Check if units are still A/B/C
            if info['row_count'] > 0:
                recommendations.append(f"⚠️ {sheet_name}: Verify units are 'Unit 1' and 'Unit 2' (not A/B/C)")
    
    if recommendations:
        print("\n🔧 Actions Needed:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print("\n✅ All sheets appear to be correctly configured!")
    
    return recommendations

def main():
    """Main execution"""
    print("\n" + "="*80)
    print("🚀 GOOGLE SHEETS COMPLETE ANALYSIS")
    print("="*80)
    print(f"📊 Spreadsheet ID: {SPREADSHEET_ID}")
    print()
    
    # Connect
    spreadsheet = connect_to_sheets()
    
    # Analyze all sheets
    sheet_analysis = analyze_all_sheets(spreadsheet)
    
    # Check required columns
    check_required_columns(sheet_analysis)
    
    # Generate recommendations
    recommendations = generate_recommendations(sheet_analysis)
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"\nTotal Sheets: {len(sheet_analysis)}")
    print(f"\nSheet Types Found:")
    
    type_counts = defaultdict(int)
    for info in sheet_analysis.values():
        type_counts[info['type']] += 1
    
    for sheet_type, count in sorted(type_counts.items()):
        print(f"  - {sheet_type}: {count}")
    
    print(f"\nIssues Found: {len(recommendations)}")
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE!")
    print("="*80)
    print()

if __name__ == "__main__":
    main()
