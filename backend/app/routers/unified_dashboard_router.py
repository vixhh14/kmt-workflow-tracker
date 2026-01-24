
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
        # 1. Load all core data (Fast Cached Read)
        projects = db.query(Project).filter(is_deleted=False).all()
        machines_raw = db.query(Machine).filter(is_deleted=False).all()
        users = [u for u in db.query(User).all() if not getattr(u, 'is_deleted', False)]
        
        # 2. Filter criteria
        active_project_id = project_id if project_id and project_id != "all" else None
        active_operator_id = operator_id if operator_id and operator_id != "all" else None

        # 3. Load all task types (Fast Cached Reads)
        normal_all = db.query(Task).filter(is_deleted=False).all()
        filing_all = db.query(FilingTask).filter(is_deleted=False).all()
        fab_all = db.query(FabricationTask).filter(is_deleted=False).all()

        # 4. Filter in-memory
        if active_project_id:
            normal_all = [t for t in normal_all if str(getattr(t, 'project_id', '')) == str(active_project_id)]
            filing_all = [t for t in filing_all if str(getattr(t, 'project_id', '')) == str(active_project_id)]
            fab_all = [t for t in fab_all if str(getattr(t, 'project_id', '')) == str(active_project_id)]
        
        if active_operator_id:
            normal_all = [t for t in normal_all if str(getattr(t, 'assigned_to', '')) == str(active_operator_id)]
            filing_all = [t for t in filing_all if str(getattr(t, 'assigned_to', '')) == str(active_operator_id)]
            fab_all = [t for t in fab_all if str(getattr(t, 'assigned_to', '')) == str(active_operator_id)]

        # 5. Build Combined Representative List
        combined_tasks = []
        for t in normal_all: combined_tasks.append(t)
        for t in filing_all: combined_tasks.append(t)
        for t in fab_all: combined_tasks.append(t)

        # 6. Aggregate Stats Memory-Only
        overview = get_operations_overview(db)

        # 7. Machine Status Calculation
        machine_status_map = {}
        active_machine_tasks = [t for t in combined_tasks if str(getattr(t, 'status', '')).lower() in ('in_progress', 'in progress', 'on_hold', 'onhold', 'on hold') and getattr(t, 'machine_id', None)]
        
        for t in active_machine_tasks:
            mid = str(getattr(t, 'machine_id', ''))
            status = str(getattr(t, 'status', '')).lower()
            if status in ('in_progress', 'in progress'): machine_status_map[mid] = 'running'
            elif status in ('on_hold', 'onhold', 'on hold') and machine_status_map.get(mid) != 'running': machine_status_map[mid] = 'on_hold'
        
        machines_data = []
        for m in machines_raw:
            m_id = str(getattr(m, 'machine_id', getattr(m, 'id', '')))
            machines_data.append({
                "machine_id": m_id, "machine_name": getattr(m, 'machine_name', 'Unknown'),
                "status": machine_status_map.get(m_id, 'available'),
                "hourly_rate": getattr(m, 'hourly_rate', 0)
            })
        
        return {
            "projects": [
                {
                    **p.dict(),
                    "id": str(getattr(p, 'project_id', getattr(p, 'id', ''))),
                    "project_id": str(getattr(p, 'project_id', getattr(p, 'id', ''))),
                    "name": str(getattr(p, 'project_name', '')),
                    "project_name": str(getattr(p, 'project_name', ''))
                } for p in projects
            ], 
            "tasks": [t.dict() if hasattr(t, 'dict') else t for t in combined_tasks], 
            "machines": machines_data,  
            "users": [u.dict() for u in users], 
            "operators": [u.dict() for u in users if str(getattr(u, 'role', '')).lower() == 'operator'],
            "overview": overview
        }
    except Exception as e:
        print(f"❌ Error in unified dashboard: {e}")
        return {"projects": [], "tasks": [], "machines": [], "users": [], "operators": [], "overview": {"tasks": {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "ended": 0, "on_hold": 0}, "machines": {"active": 0, "total": 0}, "projects": {"total": 0}}}

@router.get("/supervisor", response_model=SupervisorDashboardOut)
async def get_supervisor_dashboard(project_id: Optional[str] = None, operator_id: Optional[str] = None, db: any = Depends(get_db)):
    return await get_admin_dashboard(project_id, operator_id, db)

@router.get("/operator")
async def get_operator_dashboard(user_id: str, db: any = Depends(get_db)):
    from app.services.operator_service import get_operator_tasks
    return get_operator_tasks(db, user_id)

@router.get("/planning")
async def get_planning_dashboard(db: any = Depends(get_db)):
    from app.services.planning_service import get_planning_overview
    return get_planning_overview(db)

@router.get("/file-master")
async def get_file_master_dashboard(db: any = Depends(get_db)):
    from app.services.task_service import get_tasks_by_type
    return {"tasks": get_tasks_by_type(db, "filing")}

@router.get("/fab-master")
async def get_fab_master_dashboard(db: any = Depends(get_db)):
    from app.services.task_service import get_tasks_by_type
    return {"tasks": get_tasks_by_type(db, "fabrication")}
