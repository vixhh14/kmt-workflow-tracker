import sys
import os
sys.path.append(os.getcwd())
import create_demo_users

try:
    print("Starting fix...")
    create_demo_users.create_demo_users()
    with open("fix_status.txt", "w") as f:
        f.write("Fix completed successfully")
    print("Fix completed")
except Exception as e:
    with open("fix_status.txt", "w") as f:
        f.write(f"Fix failed: {e}")
    print(f"Fix failed: {e}")
