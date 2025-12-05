import sqlite3

try:
    conn = sqlite3.connect('workflow.db')
    cursor = conn.cursor()
    
    print("--- Machine Categories ---")
    try:
        cursor.execute("SELECT * FROM machine_categories")
        rows = cursor.fetchall()
        if not rows:
            print("No categories found.")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error reading machine_categories: {e}")

    print("\n--- Machines ---")
    try:
        cursor.execute("SELECT * FROM machines")
        rows = cursor.fetchall()
        if not rows:
            print("No machines found.")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error reading machines: {e}")

    conn.close()
except Exception as e:
    print(f"Database connection error: {e}")
