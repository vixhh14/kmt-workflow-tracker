
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.core.database import get_db
from app.models.models_db import Task, User, Machine, Project, FilingTask, FabricationTask
from types import SimpleNamespace
from app.services.dashboard_analytics_service import get_operations_overview
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
    db: any = Depends(get_db)
):
    try:
        # All data in memory
        projects = [p for p in db.query(Project).all() if not p.is_deleted]
        machines_raw = [m for m in db.query(Machine).all() if not m.is_deleted]
        users = [u for u in db.query(User).all() if not u.is_deleted and str(u.approval_status).lower() == 'approved']
        
        active_project_id = project_id if project_id and project_id != "all" else None
        active_operator_id = operator_id if operator_id and operator_id != "all" else None

        # 1. Normal Tasks
        normal_all = [t for t in db.query(Task).all() if not t.is_deleted]
        if active_project_id:
            normal_all = [t for t in normal_all if str(t.project_id) == str(active_project_id) or str(t.project) == str(active_project_id)]
        if active_operator_id:
            normal_all = [t for t in normal_all if str(t.assigned_to) == str(active_operator_id)]

        # 2. Filing Tasks
        filing_all = [t for t in db.query(FilingTask).all() if not t.is_deleted]
        if active_project_id:
            filing_all = [t for t in filing_all if str(t.project_id) == str(active_project_id)]
        if active_operator_id:
            filing_all = [t for t in filing_all if str(t.assigned_to) == str(active_operator_id)]

        # 3. Fabrication Tasks
        fab_all = [t for t in db.query(FabricationTask).all() if not t.is_deleted]
        if active_project_id:
            fab_all = [t for t in fab_all if str(t.project_id) == str(active_project_id)]
        if active_operator_id:
            fab_all = [t for t in fab_all if str(t.assigned_to) == str(active_operator_id)]

        combined_tasks = []
        for t in normal_all: combined_tasks.append(t)
        for t in filing_all:
            combined_tasks.append(SimpleNamespace(
                task_id=str(t.id), title=t.part_item, status=t.status, 
                project_id=t.project_id, machine_id=t.machine_id, 
                assigned_to=t.assigned_to, priority=getattr(t, 'priority', 'medium')
            ))
        for t in fab_all:
            combined_tasks.append(SimpleNamespace(
                task_id=str(t.id), title=t.part_item, status=t.status, 
                project_id=t.project_id, machine_id=t.machine_id, 
                assigned_to=t.assigned_to, priority=getattr(t, 'priority', 'medium')
            ))

        overview = get_operations_overview(db)
        is_filtered = active_project_id or active_operator_id
        if is_filtered:
            overview = {
                "tasks": {
                    "total": len(combined_tasks),
                    "pending": len([t for t in combined_tasks if str(t.status).lower() == 'pending']),
                    "in_progress": len([t for t in combined_tasks if str(t.status).lower() in ('in_progress', 'in progress')]),
                    "completed": len([t for t in combined_tasks if str(t.status).lower() == 'completed']),
                    "ended": len([t for t in combined_tasks if str(t.status).lower() == 'ended']),
                    "on_hold": len([t for t in combined_tasks if str(t.status).lower() in ('on_hold', 'onhold', 'on hold')])
                },
                "machines": {"active": 0, "total": len(machines_raw)},
                "projects": {"total": len(projects)}
            }

        machine_status_map = {}
        active_machine_tasks = [t for t in combined_tasks if str(t.status).lower() in ('in_progress', 'in progress', 'on_hold', 'onhold', 'on hold') and getattr(t, 'machine_id', None)]
        
        for t in active_machine_tasks:
            mid = str(t.machine_id); status = str(t.status).lower()
            if status in ('in_progress', 'in progress'): machine_status_map[mid] = 'running'
            elif status in ('on_hold', 'onhold', 'on hold') and machine_status_map.get(mid) != 'running': machine_status_map[mid] = 'on_hold'
        
        machines_data = []
        for m in machines_raw:
            machines_data.append({
                "machine_id": str(m.machine_id), "machine_name": m.machine_name,
                "status": machine_status_map.get(str(m.machine_id), 'available'),
                "hourly_rate": getattr(m, 'hourly_rate', 0)
            })
            
        if is_filtered and 'machines' in overview:
             overview['machines']['active'] = len([s for s in machine_status_map.values() if s == 'running'])
        
        return {
            "projects": projects, "tasks": combined_tasks, "machines": machines_data,  
            "users": users, "operators": [u for u in users if str(u.role).lower() == 'operator'],
            "overview": overview
        }
    except Exception as e:
        print(f"Error in unified dashboard: {e}")
        return {"projects": [], "tasks": [], "machines": [], "users": [], "operators": [], "overview": {"tasks": {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "ended": 0, "on_hold": 0}, "machines": {"active": 0, "total": 0}, "projects": {"total": 0}}}

@router.get("/supervisor", response_model=SupervisorDashboardOut)
async def get_supervisor_dashboard(project_id: Optional[str] = None, operator_id: Optional[str] = None, db: any = Depends(get_db)):
    try:
        admin_data = await get_admin_dashboard(project_id, operator_id, db)
        return {
            "projects": admin_data["projects"], "tasks": admin_data["tasks"],
            "machines": admin_data["machines"], "operators": admin_data["operators"],
            "overview": admin_data["overview"]
        }
    except Exception as e:
        print(f"Error in supervisor dashboard: {e}")
        return {"projects": [], "tasks": [], "machines": [], "operators": [], "overview": {"tasks": {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "ended": 0, "on_hold": 0}, "machines": {"active": 0, "total": 0}, "projects": {"total": 0}}}
