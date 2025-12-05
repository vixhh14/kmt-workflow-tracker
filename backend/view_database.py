"""
SQLite Database Viewer
View all data in the workflow.db database
"""
import sqlite3

def view_database():
    try:
        conn = sqlite3.connect('workflow.db')
        cursor = conn.cursor()
        
        print("=" * 80)
        print("WORKFLOW TRACKER DATABASE VIEWER")
        print("=" * 80)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📊 Found {len(tables)} tables: {', '.join(tables)}\n")
        
        # View each table
        for table in tables:
            print("\n" + "=" * 80)
            print(f"TABLE: {table.upper()}")
            print("=" * 80)
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Get data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if rows:
                # Calculate column widths
                widths = [len(c) for c in columns]
                for row in rows:
                    for i, val in enumerate(row):
                        widths[i] = max(widths[i], len(str(val)))
                
                # Create format string
                fmt = " | ".join([f"{{:<{w}}}" for w in widths])
                
                # Print header
                print("-" * (sum(widths) + 3 * (len(columns) - 1)))
                print(fmt.format(*columns))
                print("-" * (sum(widths) + 3 * (len(columns) - 1)))
                
                # Print rows
                for row in rows:
                    # Convert all values to string for printing
                    row_str = [str(val) for val in row]
                    print(fmt.format(*row_str))
                
                print(f"\n✅ Total rows: {len(rows)}")
            else:
                print("❌ No data in this table")
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("✅ Database view complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    view_database()
