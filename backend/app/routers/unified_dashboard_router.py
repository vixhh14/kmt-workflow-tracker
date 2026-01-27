
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
        overview = get_operations_overview(db, active_project_id, active_operator_id)
        
        # 6.5 Sanitize Tasks (Fix Boolean Status Crash + JOIN Project Names)
        project_map = {str(getattr(p, 'project_id', getattr(p, 'id', ''))): str(getattr(p, 'project_name', '')) for p in projects}
        user_map = {str(getattr(u, 'user_id', getattr(u, 'id', ''))): str(getattr(u, 'full_name', '') or getattr(u, 'username', '')) for u in users}
        machine_map = {str(getattr(m, 'machine_id', getattr(m, 'id', ''))): str(getattr(m, 'machine_name', '')) for m in machines_raw}

        sanitized_tasks = []
        for idx, t in enumerate(combined_tasks):
            # Convert SQLAlchemy model to dict if needed
            t_data = t.dict() if hasattr(t, 'dict') else t.__dict__.copy() if hasattr(t, '__dict__') else t
            
            # Ensure status is always a string and lowercase
            from app.core.normalizer import normalize_status
            status = normalize_status(t_data.get('status', 'pending'))
            t_data['status'] = status
            
            # Fix Project Name (Join)
            pid = str(t_data.get('project_id', ''))
            if not t_data.get('project') and pid in project_map:
                t_data['project'] = project_map[pid]
            
            # Fix Operator Name
            uid = str(t_data.get('assigned_to', ''))
            t_data['operator_name'] = user_map.get(uid, uid or "Unassigned")

            # Fix Machine Name
            mid = str(t_data.get('machine_id', ''))
            t_data['machine_name'] = machine_map.get(mid, "Handwork" if not mid else mid)

            # CRITICAL: Ensure 'id' is present and NOT empty/undefined
            # Fallback chain: task_id -> fabrication_task_id -> filing_task_id -> row_index
            t_id = (
                str(t_data.get('task_id', '')).strip() or 
                str(t_data.get('fabrication_task_id', '')).strip() or 
                str(t_data.get('filing_task_id', '')).strip() or
                str(t_data.get('id', '')).strip()
            )
            
            if not t_id or t_id.lower() == 'undefined':
                # Use a combined ID with index for safety
                t_id = f"TEMP-{idx}-{uuid.uuid4().hex[:4]}"
            
            t_data['id'] = t_id
            t_data['task_id'] = t_id # Sync back
                 
            sanitized_tasks.append(t_data)

        # 7. Machine Status Calculation
        machine_status_map = {}
        active_machine_tasks = [t for t in sanitized_tasks if str(t.get('status', '')).lower() in ('in_progress', 'in progress', 'on_hold', 'onhold', 'on hold') and t.get('machine_id')]
        
        for t in active_machine_tasks:
            mid = str(t.get('machine_id', ''))
            status = str(t.get('status', '')).lower()
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
        
        # 8. Attendance Summary (Integrated)
        from app.services.attendance_service import get_attendance_summary
        from app.core.time_utils import get_today_date_ist
        attendance = get_attendance_summary(db, get_today_date_ist().isoformat())
        
        # 9. Running Tasks (Integrated)
        running_tasks_raw = [t for t in sanitized_tasks if str(t.get('status')).lower() == 'in_progress']
        running_tasks = []
        for t in running_tasks_raw:
            # Map into RunningTask schema
            running_tasks.append({
                "id": t.get('id'),
                "title": t.get('title', 'Unknown'),
                "project": t.get('project', 'Internal'),
                "operator_name": t.get('operator_name', 'Unknown'), 
                "machine_name": t.get('machine_name', 'Handwork'),
                "machine_id": str(t.get('machine_id', '')),
                "duration_seconds": int(t.get('total_duration_seconds', 0) or 0),
                "total_held_seconds": int(t.get('total_held_seconds', 0) or 0),
                "due_date": t.get('due_date'),
                "started_at": t.get('started_at'),
                "status": "in_progress",
                "holds": t.get('holds', [])
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
            "tasks": sanitized_tasks, 
            "running_tasks": running_tasks,
            "machines": machines_data,  
            "users": [u.dict() for u in users], 
            "operators": [u.dict() for u in users if str(getattr(u, 'role', '')).lower() == 'operator'],
            "overview": overview,
            "attendance": attendance
        }
    except Exception as e:
        print(f"❌ Error in unified dashboard: {e}")
        return {"projects": [], "tasks": [], "machines": [], "users": [], "operators": [], "overview": {"tasks": {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "ended": 0, "on_hold": 0}, "machines": {"active": 0, "total": 0}, "projects": {"total": 0}}}

@router.get("/supervisor", response_model=SupervisorDashboardOut)
async def get_supervisor_dashboard(project_id: Optional[str] = None, operator_id: Optional[str] = None, db: any = Depends(get_db)):
    return await get_admin_dashboard(project_id, operator_id, db)

@router.get("/operator")
async def get_operator_dashboard(user_id: str, db: any = Depends(get_db)):
    from app.routers.operator_router import get_operator_tasks
    return await get_operator_tasks(user_id, db)

@router.get("/planning")
async def get_planning_dashboard(db: any = Depends(get_db)):
    from app.routers.planning_router import get_planning_dashboard_summary
    return await get_planning_dashboard_summary(db=db)

@router.get("/file-master")
async def get_file_master_dashboard(db: any = Depends(get_db)):
    from app.models.models_db import FilingTask
    tasks = db.query(FilingTask).all()
    return {"tasks": [t.dict() if hasattr(t, "dict") else t.__dict__ for t in tasks if not getattr(t, "is_deleted", False)]}

@router.get("/fab-master")
async def get_fab_master_dashboard(db: any = Depends(get_db)):
    from app.models.models_db import FabricationTask
    tasks = db.query(FabricationTask).all()
    return {"tasks": [t.dict() if hasattr(t, "dict") else t.__dict__ for t in tasks if not getattr(t, "is_deleted", False)]}
