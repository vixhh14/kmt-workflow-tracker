import os
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.models.models_db import Base, User, Unit, MachineCategory, UserApproval, UserMachine, Machine, Task, TaskTimeLog, PlanningTask, OutsourceItem
from app.core.database import SQLALCHEMY_DATABASE_URL as SQLITE_URL

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def migrate_data():
    # 1. Get Target Database URL
    print("--- Migration Tool: SQLite to PostgreSQL ---")
    target_url = os.getenv("TARGET_DATABASE_URL")
    
    if not target_url:
        print("❌ Error: TARGET_DATABASE_URL environment variable is not set.")
        print("Please set it to your PostgreSQL connection string.")
        print("Example: export TARGET_DATABASE_URL='postgresql://user:pass@host/dbname'")
        return

    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)

    print(f"Target Database: {target_url.split('@')[-1]}") # Hide credentials

    # 2. Connect to Source (SQLite)
    print("Connecting to Source (SQLite)...")
    source_engine = create_engine(SQLITE_URL)
    SourceSession = sessionmaker(bind=source_engine)
    source_session = SourceSession()

    # 3. Connect to Target (PostgreSQL)
    print("Connecting to Target (PostgreSQL)...")
    try:
        target_engine = create_engine(target_url)
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()
    except Exception as e:
        print(f"❌ Failed to connect to target database: {e}")
        return

    # 4. Create Tables in Target
    print("Creating tables in target database...")
    Base.metadata.create_all(bind=target_engine)

    # 5. Migrate Data
    # Define migration order to respect Foreign Keys
    # Models: User, Unit, MachineCategory -> Machine -> Task -> Others
    
    models_to_migrate = [
        (Unit, "units"),
        (MachineCategory, "machine_categories"),
        (User, "users"),
        (Machine, "machines"),
        (UserApproval, "user_approvals"),
        (UserMachine, "user_machines"),
        (Task, "tasks"),
        (TaskTimeLog, "task_time_logs"),
        (PlanningTask, "planning_tasks"),
        (OutsourceItem, "outsource_items")
    ]

    try:
        for model, table_name in models_to_migrate:
            print(f"Migrating table: {table_name}...", end=" ", flush=True)
            
            # Fetch all records from source
            records = source_session.query(model).all()
            count = len(records)
            
            if count == 0:
                print("Skipping (0 records)")
                continue

            # Check if target is already populated to avoid duplicates
            target_count = target_session.query(model).count()
            if target_count > 0:
                print(f"⚠️  Target table not empty ({target_count} records). Skipping to avoid duplicates.")
                continue

            # Insert into target
            # We need to expunge objects from source session to attach them to target session
            # However, simpler is to create new instances or use make_transient
            from sqlalchemy.orm import make_transient

            for record in records:
                source_session.expunge(record)
                make_transient(record)
                target_session.add(record)
            
            target_session.commit()
            print(f"✅ Migrated {count} records")

        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        target_session.rollback()
    finally:
        source_session.close()
        target_session.close()

if __name__ == "__main__":
    migrate_data()
