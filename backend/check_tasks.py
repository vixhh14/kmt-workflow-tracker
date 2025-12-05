import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import Base, get_db
from app.models.models_db import Task

def check_tasks():
    # Create a new session
    db = next(get_db())
    
    try:
        tasks = db.query(Task).all()
        print(f"Total tasks found: {len(tasks)}")
        
        if not tasks:
            print("No tasks found in the database.")
            return

        print("\nTask Details:")
        print("-" * 80)
        print(f"{'ID':<36} | {'Title':<20} | {'Created At':<20} | {'Status'}")
        print("-" * 80)
        
        for task in tasks:
            created_at = task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else "N/A"
            print(f"{task.id:<36} | {task.title[:20]:<20} | {created_at:<20} | {task.status}")
            
    except Exception as e:
        print(f"Error checking tasks: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_tasks()
