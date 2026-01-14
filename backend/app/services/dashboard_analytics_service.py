
"""
PRODUCTION STABILIZATION: Unified Dashboard Analytics Service (Google Sheets Edition)
Purpose: Provide accurate, consistent dashboard metrics across all roles using Google Sheets.
Strategy: Load relevant sheets and perform in-memory aggregation.
"""

from typing import Dict, Any, List
from app.models.models_db import User, Machine, Project, Task
from app.core.sheets_db import SheetsDB

def get_operations_overview(db: SheetsDB) -> Dict[str, Any]:
    """
    SINGLE SOURCE OF TRUTH for Admin, Supervisor, and Planning dashboards.
    """
    
    # 1. Projects and Tasks Aggregation
    try:
        all_projects = db.query(Project).filter(is_deleted=False).all()
        project_ids = [str(p.project_id) for p in all_projects]
        
        all_tasks = db.query(Task).filter(is_deleted=False).all()
        # Only count tasks belonging to active projects
        valid_tasks = [t for t in all_tasks if str(t.project_id) in project_ids]
        
        total_projects = len(all_projects)
        total_tasks = len(valid_tasks)
        
        pending = len([t for t in valid_tasks if t.status == 'pending'])
        in_progress = len([t for t in valid_tasks if t.status == 'in_progress'])
        completed = len([t for t in valid_tasks if t.status == 'completed'])
        on_hold = len([t for t in valid_tasks if t.status == 'on_hold'])
        ended = len([t for t in valid_tasks if t.status == 'ended'])
        
    except Exception as e:
        print(f"❌ Error aggregating projects/tasks from sheets: {e}")
        total_projects = total_tasks = pending = in_progress = completed = on_hold = ended = 0

    # 2. MACHINES OVERVIEW
    try:
        active_machines_list = db.query(Machine).filter(is_deleted=False).all()
        total_machines = len(active_machines_list)
        active_machines = len([m for m in active_machines_list if m.status == 'active'])
    except Exception as e:
        print(f"❌ Error counting machines from sheets: {e}")
        total_machines = active_machines = 0

    # 3. OPERATORS OVERVIEW
    try:
        all_users = db.query(User).filter(is_deleted=False, role='operator', approval_status='approved').all()
        total_operators = len(all_users)
    except Exception as e:
        print(f"❌ Error counting operators from sheets: {e}")
        total_operators = 0

    return {
        "tasks": {
            "total": total_tasks,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "on_hold": on_hold,
            "ended": ended
        },
        "machines": {
            "total": total_machines,
            "active": active_machines
        },
        "projects": {
            "total": total_projects
        },
        "operators": {
            "total": total_operators
        }
    }

def get_dashboard_overview(db: SheetsDB) -> Dict[str, Any]:
    return get_operations_overview(db)
