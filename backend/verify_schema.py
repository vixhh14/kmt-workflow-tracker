import sqlite3

conn = sqlite3.connect('workflow.db')
cursor = conn.cursor()

print("="*60)
print("WORKFLOW.DB - TABLE STRUCTURE VERIFICATION")
print("="*60)

tables = {
    'tasks': ['project', 'part_item', 'nos_unit', 'assigned_by'],
    'machines': ['current_operator', 'updated_at'],
    'users': ['updated_at'],
    'outsource_items': ['task_id', 'dc_generated', 'transport_status', 'follow_up_time', 'pickup_status', 'updated_at'],
    'planning_tasks': ['id', 'task_id', 'project_name', 'task_sequence', 'assigned_supervisor', 'status', 'updated_at']
}

for table_name, expected_columns in tables.items():
    print(f"\n{table_name.upper()} TABLE:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    if not columns:
        print(f"  ❌ Table does not exist!")
        continue
    
    column_names = [col[1] for col in columns]
    print(f"  Total columns: {len(column_names)}")
    
    for expected_col in expected_columns:
        if expected_col in column_names:
            print(f"  ✅ {expected_col}")
        else:
            print(f"  ❌ {expected_col} - MISSING!")
    
    print(f"\n  All columns: {', '.join(column_names)}")

conn.close()
print("\n" + "="*60)
