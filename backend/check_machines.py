import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect('workflow.db')
    
    print("--- Machine Categories ---")
    try:
        categories = pd.read_sql_query("SELECT * FROM machine_categories", conn)
        print(categories)
    except Exception as e:
        print(f"Error reading machine_categories: {e}")

    print("\n--- Machines ---")
    try:
        machines = pd.read_sql_query("SELECT * FROM machines", conn)
        print(machines)
    except Exception as e:
        print(f"Error reading machines: {e}")

    conn.close()
except Exception as e:
    print(f"Database connection error: {e}")
