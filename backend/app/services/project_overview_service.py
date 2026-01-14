from app.models.models_db import Project, Task

def get_project_overview_stats(db: any):
    """
    Calculates unified project overview statistics matching SheetsDB backend.
    """
    projects = [p for p in db.query(Project).all() if not getattr(p, 'is_deleted', False)]
    all_tasks = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False)]
    
    stats = {"total": len(projects), "completed": 0, "in_progress": 0, "yet_to_start": 0, "held": 0}
    
    for project in projects:
        pid = str(getattr(project, 'project_id', ''))
        tasks = [t for t in all_tasks if str(getattr(t, 'project_id', '')) == pid]
        
        if not tasks:
            stats["yet_to_start"] += 1
            continue
            
        st = [str(getattr(t, 'status', '')).lower() for t in tasks]
        
        if any(s in ["in_progress", "in progress"] for s in st):
            stats["in_progress"] += 1
        elif any(s in ["on_hold", "on hold", "onhold"] for s in st):
            stats["held"] += 1
        elif all(s == "completed" for s in st):
            stats["completed"] += 1
        elif all(s == "pending" for s in st):
            stats["yet_to_start"] += 1
        else:
            stats["in_progress"] += 1
            
    return stats
