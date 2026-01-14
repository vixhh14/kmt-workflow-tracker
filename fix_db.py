
import os
import sys

# Add venv site-packages to path just in case, though python executable should handle it
# Assuming running with venv python

try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("CRITICAL: sqlalchemy not found. Ensure you are running with venv python.")
    sys.exit(1)

def get_database_url():
    env_path = os.path.join("backend", ".env")
    if not os.path.exists(env_path):
        print(f"Error: .env not found at {env_path}")
        return None
    
    url = None
    with open(env_path, "r") as f:
        for line in f:
            if line.strip().startswith("DATABASE_URL="):
                url = line.strip().split("=", 1)[1]
                # Remove quotes if present
                if url.startswith('"') and url.endswith('"'):
                    url = url[1:-1]
                if url.startswith("'") and url.endswith("'"):
                    url = url[1:-1]
                break
    return url

def fix_columns():
    url = get_database_url()
    if not url:
        print("Could not find DATABASE_URL")
        return

    print(f"Connecting to DB...")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")
            
            # 1. ended_by
            try:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN ended_by VARCHAR"))
                print("✅ Added 'ended_by' column.")
            except Exception as e:
                print(f"ℹ️ 'ended_by' could not be added (exists?): {e}")

            # 2. end_reason
            try:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN end_reason VARCHAR"))
                print("✅ Added 'end_reason' column.")
            except Exception as e:
                print(f"ℹ️ 'end_reason' could not be added (exists?): {e}")

            # 3. expected_completion_time
            try:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN expected_completion_time INTEGER DEFAULT 0"))
                print("✅ Added 'expected_completion_time' column.")
            except Exception as e:
                print(f"ℹ️ 'expected_completion_time' could not be added (exists?): {e}")
                
    except Exception as e:
        print(f"❌ DB Connection failed: {e}")
        with open("fix_result.txt", "w") as f:
            f.write(f"FAILED: {e}")
        return

    with open("fix_result.txt", "w") as f:
        f.write("DONE")

if __name__ == "__main__":
    fix_columns()
