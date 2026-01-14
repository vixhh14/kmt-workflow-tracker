import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import SessionLocal
from app.models.models_db import Project
from sqlalchemy import or_

def run():
    db = SessionLocal()
    try:
        count = db.query(Project).count()
        print(f"Total projects in DB: {count}")
        active = db.query(Project).filter(or_(Project.is_deleted == False, Project.is_deleted == None)).all()
        print(f"Active projects: {len(active)}")
        for p in active:
            print(f" - {p.project_id}: {p.project_name}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
