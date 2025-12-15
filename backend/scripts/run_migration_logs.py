import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    db = SessionLocal()
    try:
        with open("scripts/add_runtime_logs.sql", "r") as f:
            sql_commands = f.read()
        
        # Split logic in case multiple statements need separate execution, 
        # but db.execute(text(full_script)) often works for Postgres if block structured.
        # Safer to just execute the whole block if it's PG compatible (which it is)
        logger.info("Executing migration script...")
        db.execute(text(sql_commands))
        db.commit()
        logger.info("Migration completed successfully.")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
