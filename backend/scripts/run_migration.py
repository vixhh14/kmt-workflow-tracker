import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from app.core.database import SessionLocal, engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        
        # 1. Create table `projects`
        if not inspector.has_table("projects"):
            logger.info("Creating table 'projects'...")
            db.execute(text("""
                CREATE TABLE projects (
                    project_id VARCHAR PRIMARY KEY,
                    project_name VARCHAR NOT NULL,
                    work_order_number VARCHAR,
                    client_name VARCHAR,
                    project_code VARCHAR UNIQUE,
                    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'Asia/Kolkata')
                )
            """))
            db.commit()
            
            # Indexes
            logger.info("Creating indexes for 'projects'...")
            db.execute(text("CREATE INDEX ix_projects_project_id ON projects (project_id)"))
            db.execute(text("CREATE INDEX ix_projects_project_name ON projects (project_name)"))
            db.execute(text("CREATE INDEX ix_projects_project_code ON projects (project_code)"))
            db.commit()
        else:
            logger.info("Table 'projects' already exists.")

        # 2. Add `project_id` to `tasks`
        columns = [c['name'] for c in inspector.get_columns("tasks")]
        if "project_id" not in columns:
            logger.info("Adding column 'project_id' to 'tasks'...")
            db.execute(text("ALTER TABLE tasks ADD COLUMN project_id VARCHAR"))
            db.commit()
        else:
            logger.info("Column 'project_id' already exists in 'tasks'.")

        # 3. Add FK Constraint safely
        # We try to add if not exists. Postgres doesn't have "ADD CONSTRAINT IF NOT EXISTS" easily.
        # We can Query information_schema.
        
        # Check constraint existence
        result = db.execute(text("""
            SELECT 1 
            FROM information_schema.table_constraints 
            WHERE constraint_name = 'fk_tasks_project_id'
        """)).fetchone()
        
        if not result:
            logger.info("Adding foreign key constraint 'fk_tasks_project_id'...")
            # Note: This might fail if bad data exists. We rely on ON DELETE SET NULL
            db.execute(text("""
                ALTER TABLE tasks 
                ADD CONSTRAINT fk_tasks_project_id 
                FOREIGN KEY (project_id) 
                REFERENCES projects (project_id) 
                ON DELETE SET NULL
            """))
            db.commit()
        else:
            logger.info("Foreign key constraint 'fk_tasks_project_id' already exists.")
            
        logger.info("Migration completed successfully.")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
