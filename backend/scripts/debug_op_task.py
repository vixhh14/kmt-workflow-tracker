
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.database import Base, get_db_url
from app.models.models_db import Project, FilingTask, User

DATABASE_URL = get_db_url()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_creation():
    db = SessionLocal()
    with open("debug_log.txt", "w") as f:
        try:
            # 1. Get a valid project
            project = db.query(Project).first()
            if not project:
                f.write("No projects found! Creating one...\n")
                project = Project(project_name="Test Project", project_code="TP-001")
                db.add(project)
                db.commit()
                db.refresh(project)
            
            f.write(f"Using Project ID: {project.project_id}\n")

            # 2. Get a valid user
            user = db.query(User).first()
            if not user:
                f.write("No users found!\n")
                return
            
            f.write(f"Using User ID: {user.user_id}\n")

            # 3. Create Filing Task Payload
            task_data = {
                "project_id": project.project_id,
                "work_order_number": "WO-DEBUG-1",
                "part_item": "Debug Part",
                "quantity": 10,
                "priority": "URGENT",
                "remarks": "Debugging",
                "assigned_by": user.user_id,
                "assigned_to": None,
                "status": "Pending"
            }
            
            from datetime import date
            task_data["due_date"] = date(2025, 12, 31)

            f.write("Attempting to create FilingTask...\n")
            new_task = FilingTask(**task_data)
            
            from app.core.time_utils import get_current_time_ist
            new_task.created_at = get_current_time_ist()
            new_task.updated_at = get_current_time_ist()

            db.add(new_task)
            db.commit()
            db.refresh(new_task)
            f.write(f"Success! Task ID: {new_task.id}\n")
            
        except Exception as e:
            f.write(f"FAILED: {e}\n")
            import traceback
            traceback.print_exc(file=f)
        finally:
            db.close()

if __name__ == "__main__":
    debug_creation()
