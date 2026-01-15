from fastapi import APIRouter, Depends
from typing import List
from app.core.database import get_db
from app.models.models_db import Project, Machine, User
from app.core.dependencies import get_current_user
from pydantic import BaseModel

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
        projects = [p for p in db.query(Project).all() if not getattr(p, 'is_deleted', False)]
        return [{"id": str(getattr(p, 'id', '')), "name": str(getattr(p, 'project_name', ''))} for p in projects]
    except Exception as e:
        print(f"❌ Error in projects dropdown: {e}")
        return []

@router.get("/machines", response_model=List[DropdownItem])
async def get_machines_dropdown(
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        machines = [m for m in db.query(Machine).all() if not getattr(m, 'is_deleted', False)]
        return [{"id": str(getattr(m, 'id', '')), "name": str(getattr(m, 'machine_name', ''))} for m in machines]
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
        all_users = db.query(User).all()
        users = [u for u in all_users if not getattr(u, 'is_deleted', False) and str(getattr(u, 'role', '')).lower() in assignable_roles]
        
        return [
            {
                "id": str(getattr(u, 'id', '')),
                "username": str(getattr(u, 'username', '')),
                "full_name": str(getattr(u, 'full_name', '') or getattr(u, 'username', '')),
                "role": str(getattr(u, 'role', ''))
            } for u in users
        ]
    except Exception as e:
        print(f"❌ Error in users dropdown: {e}")
        return []
