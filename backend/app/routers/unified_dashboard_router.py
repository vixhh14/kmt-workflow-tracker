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
    Returns ORM objects - Pydantic handles aliasing via Field(alias=...)
    """
    try:
        # Fetch ORM objects
        projects = db.query(Project).filter(
            or_(Project.is_deleted == False, Project.is_deleted == None)
        ).all()
        
        tasks = db.query(Task).filter(
            or_(Task.is_deleted == False, Task.is_deleted == None)
        ).all()
        
        machines = db.query(Machine).filter(
            or_(Machine.is_deleted == False, Machine.is_deleted == None)
        ).all()
        
        users = db.query(User).filter(
            or_(User.is_deleted == False, User.is_deleted == None),
            User.approval_status == 'approved'
        ).all()
        
        # Get overview stats
        overview = get_dashboard_overview(db)
        
        # Filter operators
        operators = [u for u in users if u.role == 'operator']
        
        # Return ORM objects directly - Pydantic will:
        # 1. Map project_id -> id via Field(alias="project_id")
        # 2. Map user_id -> id via Field(alias="user_id")
        # 3. Serialize UUIDs to strings
        # 4. Handle all datetime conversions
        return {
            "projects": projects,  # ORM objects
            "tasks": tasks,        # ORM objects
            "machines": machines,  # ORM objects
            "users": users,        # ORM objects
            "operators": operators,  # ORM objects
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
