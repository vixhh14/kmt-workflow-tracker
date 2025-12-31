from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from app.core.database import get_db
from app.models.models_db import Task, User, Machine, Project
from app.services.dashboard_analytics_service import get_dashboard_overview
from app.services.project_overview_service import get_project_overview_stats

router = APIRouter(
    prefix="/dashboard",
    tags=["unified-dashboard"]
)

@router.get("/admin")
async def get_admin_dashboard(db: Session = Depends(get_db)):
    """
    Unified dashboard for Admin as per requirements.
    """
    try:
        # 1. Projects
        projects = db.query(Project).filter(or_(Project.is_deleted == False, Project.is_deleted == None)).all()
        project_list = [{"id": p.project_id, "name": p.project_name, "code": p.project_code, "work_order": p.work_order_number} for p in projects]
        
        # 2. Tasks
        tasks = db.query(Task).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).all()
        task_list = [{"id": t.id, "title": t.title, "status": t.status} for t in tasks]
        
        # 3. Machines
        machines = db.query(Machine).filter(or_(Machine.is_deleted == False, Machine.is_deleted == None)).all()
        machine_list = [{"id": m.id, "machine_name": m.machine_name} for m in machines]
        
        # 4. Users (all)
        users = db.query(User).filter(User.is_deleted == False).all()
        user_list = [{"id": u.user_id, "username": u.username, "role": u.role, "full_name": u.full_name} for u in users]
        
        # 5. Operators only
        operators = db.query(User).filter(User.role == 'operator', User.is_deleted == False).all()
        operator_list = [{"id": u.user_id, "username": u.username, "name": u.full_name} for u in operators]
        
        # 6. Global Overview (Unified logic)
        overview = get_dashboard_overview(db)
        project_stats = get_project_overview_stats(db)
        
        return {
            "projects": project_list,
            "tasks": task_list,
            "machines": machine_list,
            "users": user_list,
            "operators": operator_list,
            "overview": {
                "tasks": overview.get("tasks", {}),
                "machines": overview.get("machines", {}),
                "projects": project_stats
            }
        }
    except Exception as e:
        print(f"Error in /dashboard/admin: {e}")
        return {
            "projects": [],
            "tasks": [],
            "machines": [],
            "users": [],
            "operators": [],
            "overview": {}
        }

@router.get("/supervisor")
async def get_supervisor_dashboard(db: Session = Depends(get_db)):
    """
    Unified dashboard for Supervisor as per requirements.
    """
    try:
        # 1. Projects
        projects = db.query(Project).filter(or_(Project.is_deleted == False, Project.is_deleted == None)).all()
        project_list = [{"id": p.project_id, "name": p.project_name, "code": p.project_code} for p in projects]
        
        # 2. Tasks
        tasks = db.query(Task).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).all()
        task_list = [{"id": t.id, "title": t.title, "status": t.status} for t in tasks]
        
        # 3. Machines
        machines = db.query(Machine).filter(or_(Machine.is_deleted == False, Machine.is_deleted == None)).all()
        machine_list = [{"id": m.id, "machine_name": m.machine_name} for m in machines]
        
        # 4. Operators
        operators = db.query(User).filter(User.role == 'operator', User.is_deleted == False).all()
        operator_list = [{"id": u.user_id, "username": u.username, "name": u.full_name} for u in operators]
        
        # 5. Global Overview
        overview = get_dashboard_overview(db)
        project_stats = get_project_overview_stats(db)
        
        return {
            "projects": project_list,
            "tasks": task_list,
            "machines": machine_list,
            "operators": operator_list,
            "overview": {
                "tasks": overview.get("tasks", {}),
                "machines": overview.get("machines", {}),
                "projects": project_stats
            }
        }
    except Exception as e:
        print(f"Error in /dashboard/supervisor: {e}")
        return {
            "projects": [],
            "tasks": [],
            "machines": [],
            "operators": [],
            "overview": {}
        }
