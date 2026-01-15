
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
        users = [u for u in db.query(User).all() if not getattr(u, 'is_deleted', False) and str(getattr(u, 'approval_status', '')).lower() == 'approved']
        
        # 2. Filter criteria
        active_project_id = project_id if project_id and project_id != "all" else None
        active_operator_id = operator_id if operator_id and operator_id != "all" else None

        # 3. Load all task types (Fast Cached Reads)
        normal_all = db.query(Task).filter(is_deleted=False).all()
        filing_all = db.query(FilingTask).filter(is_deleted=False).all()
        fab_all = db.query(FabricationTask).filter(is_deleted=False).all()

        # 4. Filter in-memory
        if active_project_id:
            normal_all = [t for t in normal_all if str(getattr(t, 'project_id', '')) == str(active_project_id) or str(getattr(t, 'project', '')) == str(active_project_id)]
            filing_all = [t for t in filing_all if str(getattr(t, 'project_id', '')) == str(active_project_id)]
            fab_all = [t for t in fab_all if str(getattr(t, 'project_id', '')) == str(active_project_id)]
        
        if active_operator_id:
            normal_all = [t for t in normal_all if str(getattr(t, 'assigned_to', '')) == str(active_operator_id)]
            filing_all = [t for t in filing_all if str(getattr(t, 'assigned_to', '')) == str(active_operator_id)]
            fab_all = [t for t in fab_all if str(getattr(t, 'assigned_to', '')) == str(active_operator_id)]

        # 5. Build Combined Representative List (SimpleNamespace for Pydantic compatibility)
        combined_tasks = []
        for t in normal_all:
             combined_tasks.append(t)
        
        for t in filing_all:
            combined_tasks.append(SimpleNamespace(
                id=str(getattr(t, 'id', '')), title=getattr(t, 'part_item', 'Filing'), 
                status=getattr(t, 'status', 'pending'), project_id=getattr(t, 'project_id', ''), 
                machine_id=getattr(t, 'machine_id', ''), assigned_to=getattr(t, 'assigned_to', ''), 
                priority=getattr(t, 'priority', 'medium')
            ))
        
        for t in fab_all:
            combined_tasks.append(SimpleNamespace(
                id=str(getattr(t, 'id', '')), title=getattr(t, 'part_item', 'Fab'), 
                status=getattr(t, 'status', 'pending'), project_id=getattr(t, 'project_id', ''), 
                machine_id=getattr(t, 'machine_id', ''), assigned_to=getattr(t, 'assigned_to', ''), 
                priority=getattr(t, 'priority', 'medium')
            ))

        # 6. Aggregate Stats Memory-Only
        is_filtered = active_project_id or active_operator_id
        if is_filtered:
            overview = {
                "tasks": {
                    "total": len(combined_tasks),
                    "pending": len([t for t in combined_tasks if str(getattr(t, 'status', '')).lower() == 'pending']),
                    "in_progress": len([t for t in combined_tasks if str(getattr(t, 'status', '')).lower() in ('in_progress', 'in progress')]),
                    "completed": len([t for t in combined_tasks if str(getattr(t, 'status', '')).lower() == 'completed']),
                    "ended": len([t for t in combined_tasks if str(getattr(t, 'status', '')).lower() == 'ended']),
                    "on_hold": len([t for t in combined_tasks if str(getattr(t, 'status', '')).lower() in ('on_hold', 'onhold', 'on hold')])
                },
                "machines": {"active": 0, "total": len(machines_raw)},
                "projects": {"total": len(projects)}
            }
        else:
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
            m_id = str(getattr(m, 'id', ''))
            machines_data.append({
                "machine_id": m_id, "machine_name": getattr(m, 'machine_name', 'Unknown'),
                "status": machine_status_map.get(m_id, 'available'),
                "hourly_rate": getattr(m, 'hourly_rate', 0)
            })
            
        if is_filtered:
             overview['machines']['active'] = len([s for s in machine_status_map.values() if s == 'running'])
        
        return {
            "projects": [p.dict() for p in projects], 
            "tasks": [t if isinstance(t, dict) else (t.dict() if hasattr(t, 'dict') else t.__dict__) for t in combined_tasks], 
            "machines": machines_data,  
            "users": [u.dict() for u in users], 
            "operators": [u.dict() for u in users if str(getattr(u, 'role', '')).lower() == 'operator'],
            "overview": overview
        }
    except Exception as e:
        print(f"❌ Error in unified dashboard: {e}")
        import traceback; traceback.print_exc()
        return {"projects": [], "tasks": [], "machines": [], "users": [], "operators": [], "overview": {"tasks": {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "ended": 0, "on_hold": 0}, "machines": {"active": 0, "total": 0}, "projects": {"total": 0}}}
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
