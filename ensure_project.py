import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import SessionLocal
from app.models.models_db import Project
from sqlalchemy import or_

def run():
    db = SessionLocal()
    try:
        active = db.query(Project).filter(or_(Project.is_deleted == False, Project.is_deleted == None)).all()
        if not active:
            print("No active projects found. Creating a sample project...")
            sample = Project(
                project_name="Sample Project 1",
                project_code="SP001",
                work_order_number="WO-001",
                client_name="Test Client",
                is_deleted=False
            )
            db.add(sample)
            db.commit()
            print("Sample project created.")
        else:
            print(f"Found {len(active)} active projects:")
            for p in active:
                print(f" - {p.project_id}: {p.project_name} ({p.project_code})")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
