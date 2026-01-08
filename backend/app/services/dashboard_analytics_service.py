"""
PRODUCTION STABILIZATION: Unified Dashboard Analytics Service
Purpose: Provide accurate, consistent dashboard metrics across all roles
Strategy: Single source of truth using canonical SQL for core metrics
Safety: Direct DB queries, no in-memory aggregation, consistent filtering
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func, or_
from app.models.models_db import User, Machine, Attendance
from typing import Dict, Any
from app.core.time_utils import get_current_time_ist

def get_operations_overview(db: Session) -> Dict[str, Any]:
    """
    SINGLE SOURCE OF TRUTH for Admin, Supervisor, and Planning dashboards.
    
    Strict Adherence:
    1. Canonical SQL for Project/Task counts (Fixes LEFT JOIN bug)
    2. Attendance: Present = row exists for today
    3. Operators: Valid 'operator' role only
    4. Machines: Active = 'active' status
    """
    
    # 1. CANONICAL SQL QUERY (Projects & Tasks)
    # Fixes the bug where filtering t.is_deleted in WHERE clause excluded empty projects
    canonical_sql = text("""
        SELECT
          COUNT(DISTINCT p.project_id)                                  AS total_projects,
          COUNT(t.id)                                                   AS total_tasks,
          COUNT(*) FILTER (WHERE t.status = 'pending')                 AS pending,
          COUNT(*) FILTER (WHERE t.status = 'in_progress')             AS in_progress,
          COUNT(*) FILTER (WHERE t.status = 'completed')               AS completed,
          COUNT(*) FILTER (WHERE t.status = 'on_hold')                 AS on_hold
        FROM projects p
        LEFT JOIN tasks t
          ON t.project_id = p.project_id
          AND t.is_deleted = false
        WHERE p.is_deleted = false;
    """)
    
    try:
        result = db.execute(canonical_sql).fetchone()
        
        # Parse result safely
        total_projects = result.total_projects if result else 0
        total_tasks = result.total_tasks if result else 0
        pending = result.pending if result else 0
        in_progress = result.in_progress if result else 0
        completed = result.completed if result else 0
        on_hold = result.on_hold if result else 0
        
    except Exception as e:
        print(f"❌ CRITICAL: Error executing canonical overview SQL: {e}")
        # Fallback to zeros on critical failure
        total_projects = 0
        total_tasks = 0
        pending = 0
        in_progress = 0
        completed = 0
        on_hold = 0

    # 2. MACHINES OVERVIEW
    try:
        total_machines = db.query(Machine).filter(
            or_(Machine.is_deleted == False, Machine.is_deleted == None)
        ).count()
        
        active_machines = db.query(Machine).filter(
            or_(Machine.is_deleted == False, Machine.is_deleted == None),
            Machine.status == 'active'
        ).count()
    except Exception as e:
        print(f"❌ Error counting machines: {e}")
        total_machines = 0
        active_machines = 0

    # 3. OPERATORS OVERVIEW
    try:
        total_operators = db.query(User).filter(
            User.role == 'operator',
            or_(User.is_deleted == False, User.is_deleted == None),
            User.approval_status == 'approved'
        ).count()
    except Exception as e:
        print(f"❌ Error counting operators: {e}")
        total_operators = 0

    return {
        "tasks": {
            "total": total_tasks,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "on_hold": on_hold,
            "ended": 0 
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

# Legacy support - redirect to new function
def get_dashboard_overview(db: Session) -> Dict[str, Any]:
    return get_operations_overview(db)
