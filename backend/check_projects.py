from app.core.database import SessionLocal
from app.models.models_db import Project
from sqlalchemy import or_

def check_projects():
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        print(f"Total projects found: {len(projects)}")
        for p in projects:
            print(f"ID: {p.project_id}, Name: {p.project_name}, Deleted: {p.is_deleted}")
            
        active_projects = db.query(Project).filter(or_(Project.is_deleted == False, Project.is_deleted == None)).all()
        print(f"Active projects found: {len(active_projects)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_projects()
