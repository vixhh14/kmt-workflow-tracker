import os
import subprocess
import sys

def restore_postgres(backup_file):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set. Cannot restore.")
        return

    if not os.path.exists(backup_file):
        print(f"Backup file not found: {backup_file}")
        return

    try:
        # Use psql to restore
        # Note: This requires psql to be installed and in PATH
        cmd = f"psql {database_url} < {backup_file}"
        subprocess.run(cmd, shell=True, check=True)
        print(f"Restored from: {backup_file}")
    except Exception as e:
        print(f"Restore failed: {e}")
        print("Ensure psql is installed and accessible.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore_postgres.py <backup_file>")
    else:
        restore_postgres(sys.argv[1])
