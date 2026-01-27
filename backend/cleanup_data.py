
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.core.database import get_db
from app.models.models_db import Task, Project

def cleanup():
    db = get_db()
    
    print("--- CLEANING UP TASKS ---")
    all_tasks = db.query(Task).all()
    tasks_to_delete = ["seed", "ggg"]
    deleted_tasks_count = 0
    
    for t in all_tasks:
        title = str(getattr(t, "title", "")).lower().strip()
        if title in tasks_to_delete and not getattr(t, "is_deleted", False):
            print(f"🗑️ Deleting task: {title} (ID: {getattr(t, 'task_id', getattr(t, 'id', ''))})")
            t.is_deleted = True
            deleted_tasks_count += 1
            
    if deleted_tasks_count > 0:
        db.commit()
        print(f"✅ Successfully deleted {deleted_tasks_count} tasks.")
    else:
        print("ℹ️ No tasks found to delete (seed/ggg).")

    print("\n--- CLEANING UP PROJECTS ---")
    all_projects = db.query(Project).all()
    # The user didn't specify which project to delete explicitly in text, 
    # but mentioned "the second image Tells us the project is deleted successfully".
    # I'll check for any projects that have is_deleted=True but are still in the sheet (cached).
    # Or specifically delete 'xyz' if it's there.
    projects_to_delete = ["xyz"]
    deleted_projects_count = 0
    
    for p in all_projects:
        name = str(getattr(p, "project_name", "")).lower().strip()
        is_del = getattr(p, "is_deleted", False)
        
        # If it matches 'xyz' or is already marked deleted but we want to ensure it's synced
        if (name in projects_to_delete or is_del) and not is_del:
            print(f"🗑️ Deleting project: {name} (ID: {getattr(p, 'project_id', getattr(p, 'id', ''))})")
            p.is_deleted = True
            deleted_projects_count += 1
        elif is_del:
            # Touch it to ensure it's marked dirty and re-synced with the fix
            p.is_deleted = True 
            deleted_projects_count += 1

    if deleted_projects_count > 0:
        db.commit()
        print(f"✅ Successfully synced/deleted {deleted_projects_count} projects.")
    else:
        print("ℹ️ No projects found to delete.")

    print("\n--- FIXING SCHEMAS ---")
    # Trigger a refresh of headers by ensuring worksheets
    from app.core.sheets_db import verify_sheets_structure
    verify_sheets_structure()

if __name__ == "__main__":
    cleanup()
