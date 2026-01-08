"""
PRODUCTION STABILIZATION: Unified Dashboard Analytics Service
Purpose: Provide accurate, consistent dashboard metrics across all roles
Strategy: Use database views for normalization, aggregate all task types
Safety: Defensive null handling, fallback to zeros, no crashes
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_, text
from app.models.models_db import Task, Machine, Project, FilingTask, FabricationTask, User
from typing import Dict, Any, Optional

def get_dashboard_overview_optimized(db: Session) -> Dict[str, Any]:
    """
    OPTIMIZED: Use materialized view for instant dashboard metrics
    Falls back to live aggregation if view doesn't exist
    """
    try:
        # Try to use materialized view first (much faster)
        result = db.execute(text("SELECT * FROM dashboard_overview_mv LIMIT 1")).fetchone()
        
        if result:
            return {
                "tasks": {
                    "total": result.total_tasks or 0,
                    "pending": result.pending_tasks or 0,
                    "in_progress": result.in_progress_tasks or 0,
                    "completed": result.completed_tasks or 0,
                    "ended": result.ended_tasks or 0,
                    "on_hold": result.on_hold_tasks or 0,
                    "by_type": {
                        "general": result.general_tasks_total or 0,
                        "filing": result.filing_tasks_total or 0,
                        "fabrication": result.fabrication_tasks_total or 0
                    }
                },
                "projects": {
                    "total": db.query(Project).filter(
                        or_(Project.is_deleted == False, Project.is_deleted == None)
                    ).count(),
                    "with_tasks": result.total_projects_with_tasks or 0
                },
                "machines": {
                    "total": db.query(Machine).filter(
                        or_(Machine.is_deleted == False, Machine.is_deleted == None)
                    ).count(),
                    "with_tasks": result.total_machines_with_tasks or 0,
                    "active": db.query(Machine).filter(
                        or_(Machine.is_deleted == False, Machine.is_deleted == None),
                        Machine.status == 'active'
                    ).count()
                },
                "operators": {
                    "total": db.query(User).filter(
                        User.role == 'operator',
                        or_(User.is_deleted == False, User.is_deleted == None),
                        User.approval_status == 'approved'
                    ).count(),
                    "with_tasks": result.total_operators_with_tasks or 0
                },
                "last_refreshed": result.last_refreshed.isoformat() if result.last_refreshed else None
            }
    except Exception as e:
        print(f"⚠️ Materialized view not available, using live aggregation: {e}")
    
    # Fallback to live aggregation
    return get_dashboard_overview(db)


def get_dashboard_overview(db: Session) -> Dict[str, Any]:
    """
    COMPREHENSIVE: Aggregate from ALL task tables with defensive null handling
    Returns accurate counts even if some tables are empty
    """
    
    # Helper class for zero defaults
    class Zeros:
        total=0; pending=0; in_progress=0; completed=0; ended=0; on_hold=0
    
    # 1. GENERAL TASKS (tasks table)
    try:
        general_task_counts = db.query(
            func.count(Task.id).label('total'),
            func.count(case((func.lower(Task.status) == 'pending', 1))).label('pending'),
            func.count(case((func.lower(Task.status) == 'in_progress', 1))).label('in_progress'),
            func.count(case((func.lower(Task.status) == 'completed', 1))).label('completed'),
            func.count(case((func.lower(Task.status) == 'ended', 1))).label('ended'),
            func.count(case((or_(
                func.lower(Task.status) == 'on_hold',
                func.lower(Task.status) == 'onhold',
                func.lower(Task.status) == 'on hold'
            ), 1))).label('on_hold')
        ).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).first()
    except Exception as e:
        print(f"❌ Error querying general tasks: {e}")
        general_task_counts = Zeros()
    
    general_task_counts = general_task_counts or Zeros()
    
    # 2. FILING TASKS (filing_tasks table)
    try:
        filing_task_counts = db.query(
            func.count(FilingTask.id).label('total'),
            func.count(case((func.lower(FilingTask.status) == 'pending', 1))).label('pending'),
            func.count(case((or_(
                func.lower(FilingTask.status) == 'in progress',
                func.lower(FilingTask.status) == 'in_progress'
            ), 1))).label('in_progress'),
            func.count(case((func.lower(FilingTask.status) == 'completed', 1))).label('completed'),
            func.count(case((or_(
                func.lower(FilingTask.status) == 'on hold',
                func.lower(FilingTask.status) == 'onhold',
                func.lower(FilingTask.status) == 'on_hold'
            ), 1))).label('on_hold')
        ).filter(or_(FilingTask.is_deleted == False, FilingTask.is_deleted == None)).first()
    except Exception as e:
        print(f"❌ Error querying filing tasks: {e}")
        filing_task_counts = Zeros()
    
    filing_task_counts = filing_task_counts or Zeros()
    
    # 3. FABRICATION TASKS (fabrication_tasks table)
    try:
        fabrication_task_counts = db.query(
            func.count(FabricationTask.id).label('total'),
            func.count(case((func.lower(FabricationTask.status) == 'pending', 1))).label('pending'),
            func.count(case((or_(
                func.lower(FabricationTask.status) == 'in progress',
                func.lower(FabricationTask.status) == 'in_progress'
            ), 1))).label('in_progress'),
            func.count(case((func.lower(FabricationTask.status) == 'completed', 1))).label('completed'),
            func.count(case((or_(
                func.lower(FabricationTask.status) == 'on hold',
                func.lower(FabricationTask.status) == 'onhold',
                func.lower(FabricationTask.status) == 'on_hold'
            ), 1))).label('on_hold')
        ).filter(or_(FabricationTask.is_deleted == False, FabricationTask.is_deleted == None)).first()
    except Exception as e:
        print(f"❌ Error querying fabrication tasks: {e}")
        fabrication_task_counts = Zeros()
    
    fabrication_task_counts = fabrication_task_counts or Zeros()
    
    # AGGREGATE ALL TASK TYPES
    total_tasks = (general_task_counts.total or 0) + (filing_task_counts.total or 0) + (fabrication_task_counts.total or 0)
    total_pending = (general_task_counts.pending or 0) + (filing_task_counts.pending or 0) + (fabrication_task_counts.pending or 0)
    total_in_progress = (general_task_counts.in_progress or 0) + (filing_task_counts.in_progress or 0) + (fabrication_task_counts.in_progress or 0)
    total_completed = (general_task_counts.completed or 0) + (filing_task_counts.completed or 0) + (fabrication_task_counts.completed or 0)
    total_ended = (general_task_counts.ended or 0)  # Only general tasks have 'ended' status
    total_on_hold = (general_task_counts.on_hold or 0) + (filing_task_counts.on_hold or 0) + (fabrication_task_counts.on_hold or 0)

    # 4. Machine Counts
    try:
        machines_total = db.query(Machine).filter(
            or_(Machine.is_deleted == False, Machine.is_deleted == None)
        ).count()
        
        machines_active = db.query(Machine).filter(
            or_(Machine.is_deleted == False, Machine.is_deleted == None),
            Machine.status == 'active'
        ).count()
    except Exception as e:
        print(f"❌ Error querying machines: {e}")
        machines_total = 0
        machines_active = 0

    # 5. Project Counts
    try:
        total_projects = db.query(Project).filter(
            or_(Project.is_deleted == False, Project.is_deleted == None)
        ).count()
    except Exception as e:
        print(f"❌ Error querying projects: {e}")
        total_projects = 0

    # 6. Operator Counts
    try:
        total_operators = db.query(User).filter(
            User.role == 'operator',
            or_(User.is_deleted == False, User.is_deleted == None),
            User.approval_status == 'approved'
        ).count()
    except Exception as e:
        print(f"❌ Error querying operators: {e}")
        total_operators = 0

    return {
        "tasks": {
            "total": total_tasks,
            "pending": total_pending,
            "in_progress": total_in_progress,
            "completed": total_completed,
            "ended": total_ended,
            "on_hold": total_on_hold,
            "by_type": {
                "general": general_task_counts.total or 0,
                "filing": filing_task_counts.total or 0,
                "fabrication": fabrication_task_counts.total or 0
            }
        },
        "machines": {
            "active": machines_active,
            "total": machines_total
        },
        "projects": {
            "total": total_projects
        },
        "operators": {
            "total": total_operators
        }
    }


def refresh_dashboard_cache(db: Session) -> bool:
    """
    Refresh the materialized view for dashboard metrics
    Call this after bulk task operations
    """
    try:
        db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_overview_mv"))
        db.commit()
        print("✅ Dashboard cache refreshed successfully")
        return True
    except Exception as e:
        print(f"⚠️ Failed to refresh dashboard cache: {e}")
        return False
