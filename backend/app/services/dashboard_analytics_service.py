
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_
from app.models.models_db import Task, Machine, Project, FilingTask, FabricationTask

def get_dashboard_overview(db: Session):
    """
    Unified dashboard analytics for Admin, Planning, and Supervisor.
    Returns counts for tasks, projects, and machines.
    
    CRITICAL FIX: Aggregates from ALL task tables (tasks, filing_tasks, fabrication_tasks)
    to provide accurate counts for Operations Overview.
    """
    
    # 1. GENERAL TASKS (tasks table)
    general_task_counts = db.query(
        func.count(Task.id).label('total'),
        func.count(case((func.lower(Task.status) == 'pending', 1))).label('pending'),
        func.count(case((func.lower(Task.status) == 'in_progress', 1))).label('in_progress'),
        func.count(case((func.lower(Task.status) == 'completed', 1))).label('completed'),
        func.count(case((func.lower(Task.status) == 'ended', 1))).label('ended'),
        func.count(case((or_(func.lower(Task.status) == 'on_hold', func.lower(Task.status) == 'onhold'), 1))).label('on_hold')
    ).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).first()
    
    # 2. FILING TASKS (filing_tasks table)
    filing_task_counts = db.query(
        func.count(FilingTask.id).label('total'),
        func.count(case((func.lower(FilingTask.status) == 'pending', 1))).label('pending'),
        func.count(case((func.lower(FilingTask.status) == 'in progress', 1))).label('in_progress'),
        func.count(case((func.lower(FilingTask.status) == 'completed', 1))).label('completed'),
        func.count(case((or_(func.lower(FilingTask.status) == 'on hold', func.lower(FilingTask.status) == 'onhold'), 1))).label('on_hold')
    ).filter(or_(FilingTask.is_deleted == False, FilingTask.is_deleted == None)).first()
    
    # 3. FABRICATION TASKS (fabrication_tasks table)
    fabrication_task_counts = db.query(
        func.count(FabricationTask.id).label('total'),
        func.count(case((func.lower(FabricationTask.status) == 'pending', 1))).label('pending'),
        func.count(case((func.lower(FabricationTask.status) == 'in progress', 1))).label('in_progress'),
        func.count(case((func.lower(FabricationTask.status) == 'completed', 1))).label('completed'),
        func.count(case((or_(func.lower(FabricationTask.status) == 'on hold', func.lower(FabricationTask.status) == 'onhold'), 1))).label('on_hold')
    ).filter(or_(FabricationTask.is_deleted == False, FabricationTask.is_deleted == None)).first()
    
    # 🛡️ DEFENSIVE: Ensure we have valid objects with 0s if query returns None
    class Zeros:
        total=0; pending=0; in_progress=0; completed=0; ended=0; on_hold=0
    
    general_task_counts = general_task_counts or Zeros()
    filing_task_counts = filing_task_counts or Zeros()
    fabrication_task_counts = fabrication_task_counts or Zeros()
    
    # AGGREGATE ALL TASK TYPES
    total_tasks = (general_task_counts.total or 0) + (filing_task_counts.total or 0) + (fabrication_task_counts.total or 0)
    total_pending = (general_task_counts.pending or 0) + (filing_task_counts.pending or 0) + (fabrication_task_counts.pending or 0)
    total_in_progress = (general_task_counts.in_progress or 0) + (filing_task_counts.in_progress or 0) + (fabrication_task_counts.in_progress or 0)
    total_completed = (general_task_counts.completed or 0) + (filing_task_counts.completed or 0) + (fabrication_task_counts.completed or 0)
    total_ended = (general_task_counts.ended or 0)  # Only general tasks have 'ended' status
    total_on_hold = (general_task_counts.on_hold or 0) + (filing_task_counts.on_hold or 0) + (fabrication_task_counts.on_hold or 0)

    # 4. Machine Counts (active vs total)
    # NOTE: Machine status should be dynamically calculated from active tasks, not static DB field
    # For now, keeping existing logic but this should be refactored
    machines_active = db.query(Machine).filter(
        or_(Machine.is_deleted == False, Machine.is_deleted == None),
        Machine.status == 'active'
    ).count()
    
    machines_total = db.query(Machine).filter(
         or_(Machine.is_deleted == False, Machine.is_deleted == None)
    ).count()

    # 5. Project Counts
    total_projects = db.query(Project).filter(
        or_(Project.is_deleted == False, Project.is_deleted == None)
    ).count()

    return {
        "tasks": {
            "total": total_tasks,
            "pending": total_pending,
            "in_progress": total_in_progress,
            "completed": total_completed,
            "ended": total_ended,
            "on_hold": total_on_hold
        },
        "machines": {
            "active": machines_active,
            "total": machines_total
        },
        "projects": {
            "total": total_projects
        }
    }
