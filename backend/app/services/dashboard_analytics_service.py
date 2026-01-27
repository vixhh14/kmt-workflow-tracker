
"""
PRODUCTION STABILIZATION: Unified Dashboard Analytics Service (Google Sheets Edition)
Purpose: Provide accurate, consistent dashboard metrics across all roles using Google Sheets.
Strategy: Load relevant sheets and perform in-memory aggregation.
"""

from typing import Dict, Any, List, Optional
from app.models.models_db import User, Machine, Project, Task, FilingTask, FabricationTask
from app.core.sheets_db import SheetsDB

def get_operations_overview(
    db: SheetsDB, 
    project_id: Optional[str] = None, 
    operator_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    SINGLE SOURCE OF TRUTH for Admin, Supervisor, and Planning dashboards.
    Aggregates metrics from Projects, Tasks, Machines, and Users, with optional filtering.
    """
    stats = {
        "tasks": {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "on_hold": 0, "ended": 0},
        "machines": {"total": 0, "active": 0},
        "projects": {"total": 0},
        "operators": {"total": 0}
    }
    
    try:
        # 1. Projects
        all_projects = [p for p in db.query(Project).all() if not getattr(p, 'is_deleted', False)]
        if project_id and project_id != "all":
            all_projects = [p for p in all_projects if str(getattr(p, 'project_id', getattr(p, 'id', ''))) == str(project_id)]
        stats["projects"]["total"] = len(all_projects)
        
        # 2. Tasks Aggregation (Main Tasks Sheet)
        all_tasks = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False)]
        
        # Include Filing and Fabrication
        try:
            filing_tasks = [t for t in db.query(FilingTask).all() if not getattr(t, 'is_deleted', False)]
            all_tasks.extend(filing_tasks)
        except Exception as e:
            print(f"⚠️ Filing tasks fetch failed for analytics: {e}")
        
        try:
            fab_tasks = [t for t in db.query(FabricationTask).all() if not getattr(t, 'is_deleted', False)]
            all_tasks.extend(fab_tasks)
        except Exception as e:
            print(f"⚠️ Fabrication tasks fetch failed for analytics: {e}")

        # Applying Filters
        if project_id and project_id != "all":
            all_tasks = [t for t in all_tasks if str(getattr(t, 'project_id', '')) == str(project_id)]
        if operator_id and operator_id != "all":
            all_tasks = [t for t in all_tasks if str(getattr(t, 'assigned_to', '')) == str(operator_id)]

        for t in all_tasks:
            stats["tasks"]["total"] += 1
            status = str(getattr(t, 'status', 'pending')).lower().strip()
            
            # Robust status mapping to prevent empty charts
            if status in ['pending', 'active', 'todo']:
                stats["tasks"]["pending"] += 1
            elif status in ['in_progress', 'in progress', 'running', 'started']:
                stats["tasks"]["in_progress"] += 1
            elif status in ['completed', 'finished', 'done']:
                stats["tasks"]["completed"] += 1
            elif status in ['on_hold', 'onhold', 'on hold', 'paused']:
                stats["tasks"]["on_hold"] += 1
            elif status in ['ended', 'inactive', 'cancelled']:
                stats["tasks"]["ended"] += 1
            else:
                # Fallback: Count unmapped but non-deleted tasks as pending
                stats["tasks"]["pending"] += 1

    except Exception as e:
        print(f"❌ Error aggregating dashboard tasks: {e}")

    # 3. Machines
    try:
        all_machines = [m for m in db.query(Machine).all() if not getattr(m, 'is_deleted', False)]
        stats["machines"]["total"] = len(all_machines)
        # Check both 'status' field and in-memory busy status from tasks if needed
        stats["machines"]["active"] = len([m for m in all_machines if str(getattr(m, 'status', '')).lower() in ('active', 'running')])
    except Exception as e:
        print(f"❌ Error aggregating dashboard machines: {e}")

    # 4. Operators
    try:
        # Only count approved operators
        all_operators = [u for u in db.query(User).all() 
                        if not getattr(u, 'is_deleted', False) 
                        and str(getattr(u, 'role', '')).lower() == 'operator']
        stats["operators"]["total"] = len(all_operators)
    except Exception as e:
        print(f"❌ Error aggregating dashboard operators: {e}")

    return stats

def get_dashboard_overview(db: SheetsDB) -> Dict[str, Any]:
    return get_operations_overview(db)
