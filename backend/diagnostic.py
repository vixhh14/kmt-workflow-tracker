from app.core.database import SessionLocal
from app.models.models_db import Project, Machine, User
from sqlalchemy import func

def diagnostic():
    db = SessionLocal()
    try:
        project_count = db.query(func.count(Project.project_id)).filter(Project.is_deleted == False).scalar()
        machine_count = db.query(func.count(Machine.id)).filter(Machine.is_deleted == False).scalar()
        user_count = db.query(func.count(User.user_id)).filter(User.is_deleted == False).scalar()
        
        print(f"DIAGNOSTIC RESULTS:")
        print(f"Active Projects: {project_count}")
        print(f"Active Machines: {machine_count}")
        print(f"Active Users: {user_count}")
    finally:
        db.close()

if __name__ == "__main__":
    diagnostic()
