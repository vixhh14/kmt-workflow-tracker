from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from app.core.database import get_db
from app.models.models_db import Task, User, Machine, Project
from app.services.dashboard_analytics_service import get_dashboard_overview
from app.services.project_overview_service import get_project_overview_stats
from app.schemas.dashboard_schema import AdminDashboardOut, SupervisorDashboardOut

router = APIRouter(
    prefix="/dashboard",
    tags=["unified-dashboard"]
)

@router.get("/admin", response_model=AdminDashboardOut)
async def get_admin_dashboard(db: Session = Depends(get_db)):
    """
    Admin Dashboard: All projects, tasks, machines, users, and operators.
    FAIL-SAFE: Skips corrupted rows, returns partial data.
    """
    try:
        # Fetch data with LEFT JOINs to handle missing relationships
        projects = db.query(Project).filter(or_(Project.is_deleted == False, Project.is_deleted == None)).all()
        tasks = db.query(Task).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).all()
        machines = db.query(Machine).filter(or_(Machine.is_deleted == False, Machine.is_deleted == None)).all()
        users = db.query(User).filter(
            or_(User.is_deleted == False, User.is_deleted == None),
            User.approval_status == 'approved'
        ).all()
        
        # Get overview stats
        overview = get_dashboard_overview(db)
        
        # FAIL-SAFE: Process each row individually, skip corrupted ones
        project_list = []
        for p in projects:
            try:
                project_list.append({
                    "project_id": str(p.project_id),
                    "project_name": p.project_name or "Unnamed Project",
                    "work_order_number": p.work_order_number or "",
                    "client_name": p.client_name or "",
                    "created_at": p.created_at.isoformat() if p.created_at else None
                })
            except Exception as e:
                print(f"⚠️ Skipping corrupted project {getattr(p, 'project_id', 'unknown')}: {e}")
                continue
        
        task_list = []
        for t in tasks:
            try:
                task_list.append({
                    "id": str(t.id),
                    "title": t.title or "Untitled Task",
                    "status": t.status or "pending",
                    "priority": t.priority or "medium",
                    "project_id": str(t.project_id) if t.project_id else None,
                    "assigned_to": t.assigned_to or "",
                    "due_date": t.due_date or "",
                    "created_at": t.created_at.isoformat() if t.created_at else None
                })
            except Exception as e:
                print(f"⚠️ Skipping corrupted task {getattr(t, 'id', 'unknown')}: {e}")
                continue
        
        machine_list = []
        for m in machines:
            try:
                machine_list.append({
                    "id": str(m.id),
                    "machine_name": m.machine_name or "Unknown Machine",
                    "status": m.status or "unknown",
                    "unit_id": m.unit_id or 0
                })
            except Exception as e:
                print(f"⚠️ Skipping corrupted machine {getattr(m, 'id', 'unknown')}: {e}")
                continue
        
        user_list = []
        for u in users:
            try:
                user_list.append({
                    "user_id": str(u.user_id),
                    "username": u.username or "Unknown",
                    "full_name": u.full_name or u.username or "Unknown",
                    "role": u.role or "operator"
                })
            except Exception as e:
                print(f"⚠️ Skipping corrupted user {getattr(u, 'user_id', 'unknown')}: {e}")
                continue
        
        # Operators are users with role 'operator'
        operator_list = [u for u in user_list if u.get("role") == "operator"]
        
        return {
            "projects": project_list,
            "tasks": task_list,
            "machines": machine_list,
            "users": user_list,
            "operators": operator_list,
            "overview": overview
        }
        
    except Exception as e:
        print(f"❌ Admin dashboard error: {e}")
        import traceback
        traceback.print_exc()
        # Return empty but valid structure
        return {
            "projects": [],
            "tasks": [],
            "machines": [],
            "users": [],
            "operators": [],
            "overview": {
                "tasks": {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "ended": 0, "on_hold": 0},
                "machines": {"active": 0, "total": 0},
                "projects": {"total": 0}
            }
        }

@router.get("/supervisor", response_model=SupervisorDashboardOut)
async def get_supervisor_dashboard(db: Session = Depends(get_db)):
    """
    Supervisor Dashboard: Projects, tasks, machines, operators (no user management).
    FAIL-SAFE: Skips corrupted rows, returns partial data.
    """
    try:
        # Reuse admin logic but exclude full user list
        admin_data = await get_admin_dashboard(db)
        
        return {
            "projects": admin_data["projects"],
            "tasks": admin_data["tasks"],
            "machines": admin_data["machines"],
            "operators": admin_data["operators"],
            "overview": admin_data["overview"]
        }
        
    except Exception as e:
        print(f"❌ Supervisor dashboard error: {e}")
        import traceback
        traceback.print_exc()
        # Return empty but valid structure
        return {
            "projects": [],
            "tasks": [],
            "machines": [],
            "operators": [],
            "overview": {
                "tasks": {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "ended": 0, "on_hold": 0},
                "machines": {"active": 0, "total": 0},
                "projects": {"total": 0}
            }
        }
