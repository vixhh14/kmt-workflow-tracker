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
    user_id: str
    username: str
    full_name: str
    role: str

@router.get("/projects", response_model=List[DropdownItem])
async def get_projects_dropdown(
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects = [p for p in db.query(Project).all() if not p.is_deleted]
    return [{"id": str(p.project_id), "name": str(p.project_name)} for p in projects]

@router.get("/machines", response_model=List[DropdownItem])
async def get_machines_dropdown(
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    machines = [m for m in db.query(Machine).all() if not m.is_deleted]
    return [{"id": str(m.id), "name": str(m.machine_name)} for m in machines]

@router.get("/users/assignable", response_model=List[UserDropdownItem])
async def get_assignable_users(
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignable_roles = ['admin', 'supervisor', 'planning', 'operator', 'fab_master', 'file_master']
    all_users = db.query(User).all()
    users = [u for u in all_users if not u.is_deleted and str(u.role).lower() in assignable_roles]
    
    return [
        {
            "user_id": str(u.user_id),
            "username": str(u.username),
            "full_name": str(u.full_name or u.username),
            "role": str(u.role)
        } for u in users
    ]
