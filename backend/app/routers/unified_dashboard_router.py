from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from app.core.database import get_db
from app.models.models_db import Task, User, Machine, Project
from app.services.dashboard_analytics_service import get_dashboard_overview
from app.services.project_overview_service import get_project_overview_stats
from app.schemas.dashboard_schema import AdminDashboardOut, SupervisorDashboardOut
import uuid

router = APIRouter(
    prefix="/dashboard",
    tags=["unified-dashboard"]
)

@router.get("/admin", response_model=AdminDashboardOut)
async def get_admin_dashboard(
    project_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Admin Dashboard: All projects, tasks, machines, users, and operators.
    Returns ORM objects - Pydantic handles aliasing via Field(alias=...)
     Supports validation filtering for Project and Operator.
    """
    try:
        # Fetch ORM objects
        projects = db.query(Project).filter(
            or_(Project.is_deleted == False, Project.is_deleted == None)
        ).all()
        
        # Filter Tasks
        tasks_query = db.query(Task).filter(
            or_(Task.is_deleted == False, Task.is_deleted == None)
        )
        if project_id and project_id != "all":
            try:
                uuid.UUID(str(project_id))
                tasks_query = tasks_query.filter(Task.project_id == project_id)
            except ValueError:
                tasks_query = tasks_query.filter(Task.project == project_id)
        if operator_id and operator_id != "all":
            tasks_query = tasks_query.filter(Task.assigned_to == operator_id)
            
        tasks = tasks_query.all()
        
        # Machines - List all machines, but update status based on active tasks
        machines = db.query(Machine).filter(
            or_(Machine.is_deleted == False, Machine.is_deleted == None)
        ).all()
        
        users = db.query(User).filter(
            or_(User.is_deleted == False, User.is_deleted == None),
            User.approval_status == 'approved'
        ).all()
        
        # Get overview stats - Use our filtered tasks list to calculate stats on the fly
        # instead of the unfiltered service call
        
        total_tasks = len(tasks)
        pending = len([t for t in tasks if t.status == 'pending'])
        in_progress = len([t for t in tasks if t.status == 'in_progress'])
        completed = len([t for t in tasks if t.status == 'completed'])
        on_hold = len([t for t in tasks if t.status == 'on_hold' or t.status == 'onhold'])
        ended = len([t for t in tasks if t.status == 'ended']) # Assuming 'ended' is a valid status
        
        # Machine Status Logic
        # 1. Get all active tasks (in_progress, on_hold)
        # 2. Filter by project/operator if provided (already done in 'tasks' list)
        active_machine_tasks = [t for t in tasks if t.status in ('in_progress', 'on_hold', 'onhold') and t.machine_id]
        
        # Map machine_id -> status
        machine_status_map = {}
        for t in active_machine_tasks:
            current = machine_status_map.get(t.machine_id)
            if t.status == 'in_progress':
                machine_status_map[t.machine_id] = 'active' # Highest priority
            elif t.status in ('on_hold', 'onhold') and current != 'active':
                machine_status_map[t.machine_id] = 'on_hold'
        
        # Update machine objects
        machines_data = []
        for m in machines:
            # We need to return objects compatible with Pydantic model. 
            # ORM objects can be modified if not committed, or correct way involves separate dicts.
            # safe way -> dict
            m_status = machine_status_map.get(m.id, 'idle')
            machines_data.append({
                "id": m.id,
                "machine_name": m.machine_name,
                "category_id": m.category_id,
                "category_name": m.category_name,
                "status": m_status,
                "hourly_rate": m.hourly_rate,
                "unit": m.unit,
                "is_deleted": m.is_deleted,
                "created_at": m.created_at,
                "updated_at": m.updated_at
            })
            
        active_machines_count = len([m for m in machines_data if m['status'] == 'active'])
        
        # Calculate Logic for Overview if filtering is applied
        overview = {
            "tasks": {
                "total": total_tasks,
                "pending": pending,
                "in_progress": in_progress,
                "completed": completed,
                "ended": ended,
                "on_hold": on_hold
            },
            "machines": {
                "active": active_machines_count,
                "total": len(machines)
            },
            "projects": {
                "total": len(projects) # Projects list is total available
            }
        }
        
        # Filter operators
        operators = [u for u in users if u.role == 'operator']
        
        return {
            "projects": projects,  
            "tasks": tasks,        
            "machines": machines_data,  
            "users": users,        
            "operators": operators, 
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
async def get_supervisor_dashboard(
    project_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Supervisor Dashboard: Projects, tasks, machines, operators (no user management).
    FAIL-SAFE: Skips corrupted rows, returns partial data.
    Supports filtering by project_id and operator_id.
    """
    try:
        # Reuse admin logic but exclude full user list
        admin_data = await get_admin_dashboard(project_id, operator_id, db)
        
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
