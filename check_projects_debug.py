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
from app.models.models_db import Project

def run():
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        print(f"DEBUG:PROJECT_COUNT={len(projects)}")
        for p in projects:
            print(f"DEBUG:PROJECT:{p.project_id}:{p.project_name}:deleted={p.is_deleted}")
    except Exception as e:
        print(f"DEBUG:ERROR:{e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
