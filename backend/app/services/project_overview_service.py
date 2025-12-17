from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.models_db import Project, Task

def get_project_overview_stats(db: Session):
    """
    Calculates unified project overview statistics.
    Single source of truth for Admin, Planning, and Supervisor dashboards.
    """
    # 1. Fetch all active projects
    projects = db.query(Project).filter(
        or_(Project.is_deleted == False, Project.is_deleted == None)
    ).all()
    
    total_projects = len(projects)
    
    stats = {
        "total": total_projects,
        "completed": 0,
        "in_progress": 0,
        "yet_to_start": 0,
        "held": 0
    }
    
    # 2. Iterate and determine status for each project
    for project in projects:
        # Fetch tasks for this project
        tasks = db.query(Task).filter(
            Task.project_id == project.project_id,
            or_(Task.is_deleted == False, Task.is_deleted == None)
        ).all()
        
        if not tasks:
            stats["yet_to_start"] += 1
            continue
            
        task_statuses = [t.status for t in tasks]
        
        # Logic Priority:
        # 1. In Progress: If ANY task is running
        if "in_progress" in task_statuses:
            stats["in_progress"] += 1
        # 2. Held: If ANY task is held (and none running)
        elif "on_hold" in task_statuses:
            stats["held"] += 1
        # 3. Completed: If ALL tasks are completed
        elif all(s == "completed" for s in task_statuses):
            stats["completed"] += 1
        # 4. Yet to Start: If ALL tasks are pending
        elif all(s == "pending" for s in task_statuses):
            stats["yet_to_start"] += 1
        else:
            # Mixed state (e.g., some completed, some pending) -> Treat as In Progress
            stats["in_progress"] += 1
            
    return stats
