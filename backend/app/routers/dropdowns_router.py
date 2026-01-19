from fastapi import APIRouter, Depends
from typing import List
from app.core.database import get_db
from app.models.models_db import Project, Machine, User
from app.core.dependencies import get_current_user
from pydantic import BaseModel
from app.core.time_utils import get_current_time_ist

router = APIRouter(prefix="/dropdowns", tags=["Dropdowns"])

class DropdownItem(BaseModel):
    id: str
    name: str

class UserDropdownItem(BaseModel):
    id: str
    username: str
    full_name: str
    role: str

@router.get("/projects", response_model=List[DropdownItem])
async def get_projects_dropdown(
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        from app.models.models_db import Project
        all_p = db.query(Project).all()
        return [{"id": str(getattr(p, 'id', '')), "name": str(getattr(p, 'project_name', ''))} 
                for p in all_p if not getattr(p, 'is_deleted', False)]
    except Exception as e:
        print(f"❌ Error in projects dropdown: {e}")
        return []

@router.get("/machines", response_model=List[DropdownItem])
async def get_machines_dropdown(
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        from app.models.models_db import Machine
        all_m = db.query(Machine).all()
        return [{"id": str(getattr(m, 'id', '')), "name": str(getattr(m, 'machine_name', ''))} 
                for m in all_m if not getattr(m, 'is_deleted', False)]
    except Exception as e:
        print(f"❌ Error in machines dropdown: {e}")
        return []

@router.get("/users/assignable", response_model=List[UserDropdownItem])
async def get_assignable_users(
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        assignable_roles = ['admin', 'supervisor', 'planning', 'operator', 'fab_master', 'file_master']
        all_u = db.query(User).all()
        
        results = []
        for u in all_u:
            if getattr(u, 'is_deleted', False) or not bool(getattr(u, 'active', True)):
                continue
            
            u_role = str(getattr(u, 'role', '')).lower()
            if u_role in assignable_roles:
                results.append({
                    "id": str(getattr(u, 'user_id', getattr(u, 'id', ''))),
                    "username": str(getattr(u, 'username', '')),
                    "full_name": str(getattr(u, 'username', '')),
                    "role": u_role
                })
        return results
    except Exception as e:
        print(f"❌ Error in users dropdown: {e}")
        return []

@router.get("/bootstrap")
async def bootstrap_data(
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consolidated endpoint to fetch all common dropdown data."""
    try:
        from app.models.models_db import Unit, MachineCategory, Project, Machine
        
        p = [{"id": str(getattr(p, 'id', '')), "name": str(getattr(p, 'project_name', ''))} 
             for p in db.query(Project).all() if not getattr(p, 'is_deleted', False)]
                   
        m = [{"id": str(getattr(m, 'id', '')), "name": str(getattr(m, 'machine_name', ''))} 
             for m in db.query(Machine).all() if not getattr(m, 'is_deleted', False)]
                   
        u = [{"id": str(getattr(u, 'id', '')), "name": str(getattr(u, 'name', ''))} 
             for u in db.query(Unit).all() if not getattr(u, 'is_deleted', False)]
                
        c = [{"id": str(getattr(c, 'id', '')), "name": str(getattr(c, 'name', ''))} 
             for c in db.query(MachineCategory).all() if not getattr(c, 'is_deleted', False)]
        
        return {
            "projects": p,
            "machines": m,
            "units": u,
            "categories": c,
            "server_time": get_current_time_ist().isoformat()
        }
    except Exception as e:
        print(f"❌ Error in bootstrap: {e}")
        return {"error": str(e), "projects": [], "machines": [], "units": [], "categories": []}
