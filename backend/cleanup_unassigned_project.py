
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.core.database import get_db
from app.models.models_db import Project

def cleanup_projects():
    db = get_db()
    all_projects = db.query(Project).filter(is_deleted=False).all()
    
    print("Active projects:")
    for p in all_projects:
        pid = getattr(p, 'project_id', getattr(p, 'id', ''))
        name = getattr(p, 'project_name', '')
        code = getattr(p, 'project_code', '')
        print(f"  - Name: {name} | Code: {code} | ID: {pid}")
        
        # If it's the 'Unassigned' project or the second one has some weird name
        if name.lower() == 'unassigned' or not name.strip():
            print(f"🗑️ Deleting project: {name}")
            p.is_deleted = True
            
    db.commit()
    print("Done cleanup.")

if __name__ == "__main__":
    cleanup_projects()
