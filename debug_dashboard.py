import sys
import os
from dotenv import load_dotenv

# Path adjustments
BASE_DIR = os.getcwd()
sys.path.append(os.path.join(BASE_DIR, 'backend'))

# Load environment
dotenv_path = os.path.join(BASE_DIR, 'backend', '.env')
load_dotenv(dotenv_path)

from app.core.database import SessionLocal
from app.models.models_db import Project, Task, User, Machine
from sqlalchemy import or_

def run():
    db = SessionLocal()
    try:
        print("Starting manual dashboard fetch...")
        # 1. Projects
        projects = db.query(Project).filter(or_(Project.is_deleted == False, Project.is_deleted == None)).all()
        print(f"Projects count: {len(projects)}")
        for p in projects:
            print(f"  P: {p.project_id} | {p.project_name} | {p.is_deleted}")
            
        # 2. Tasks
        tasks = db.query(Task).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).all()
        print(f"Tasks count: {len(tasks)}")
        
        # 3. Machines
        machines = db.query(Machine).filter(or_(Machine.is_deleted == False, Machine.is_deleted == None)).all()
        print(f"Machines count: {len(machines)}")
        
        # 4. Users
        users = db.query(User).filter(User.is_deleted == False).all()
        print(f"Users count: {len(users)}")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run()
