
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_
from app.models.models_db import Task, Machine, Project

def get_dashboard_overview(db: Session):
    """
    Unified dashboard analytics for Admin, Planning, and Supervisor.
    Returns counts for tasks, projects, and machines.
    """
    
    # 1. Task Counts (filtered by is_deleted)
    task_counts = db.query(
        func.count(Task.id).label('total'),
        func.count(case((Task.status == 'pending', 1))).label('pending'),
        func.count(case((Task.status == 'in_progress', 1))).label('in_progress'),
        func.count(case((Task.status == 'completed', 1))).label('completed'),
        func.count(case((Task.status == 'on_hold', 1))).label('on_hold')
    ).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).first()

    # 2. Machine Counts (active vs total)
    # Assuming 'active' status means available/working.
    machines_active = db.query(Machine).filter(
        or_(Machine.is_deleted == False, Machine.is_deleted == None),
        Machine.status == 'active'
    ).count()
    
    machines_total = db.query(Machine).filter(
         or_(Machine.is_deleted == False, Machine.is_deleted == None)
    ).count()

    # 3. Project Counts
    total_projects = db.query(Project).filter(
        or_(Project.is_deleted == False, Project.is_deleted == None)
    ).count()

    return {
        "tasks": {
            "total": task_counts.total,
            "pending": task_counts.pending,
            "in_progress": task_counts.in_progress,
            "completed": task_counts.completed,
            "on_hold": task_counts.on_hold
        },
        "machines": {
            "active": machines_active,
            "total": machines_total
        },
        "projects": {
            "total": total_projects
        }
    }
