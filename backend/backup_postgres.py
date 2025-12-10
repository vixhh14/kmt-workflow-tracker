import os
import datetime
import subprocess

def backup_postgres():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set. Cannot backup.")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.sql"
    
    # Extract connection details (simplified parsing)
    # Assumes format: postgresql://user:password@host:port/dbname
    try:
        # Use pg_dump if available
        # Note: This requires pg_dump to be installed and in PATH
        cmd = f"pg_dump {database_url} > {backup_file}"
        subprocess.run(cmd, shell=True, check=True)
        print(f"Backup created: {backup_file}")
    except Exception as e:
        print(f"Backup failed: {e}")
        print("Ensure pg_dump is installed and accessible.")

if __name__ == "__main__":
    backup_postgres()
