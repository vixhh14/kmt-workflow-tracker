from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return projects where is_deleted = false"""
    projects = db.query(Project).filter(or_(Project.is_deleted == False, Project.is_deleted == None)).all()
    return [{"id": str(p.project_id), "name": p.project_name} for p in projects]

@router.get("/machines", response_model=List[DropdownItem])
async def get_machines_dropdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return machines where is_deleted = false"""
    machines = db.query(Machine).filter(or_(Machine.is_deleted == False, Machine.is_deleted == None)).all()
    return [{"id": str(m.id), "name": m.machine_name} for m in machines]

@router.get("/users/assignable", response_model=List[UserDropdownItem])
async def get_assignable_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return users with assignable roles and is_deleted = false"""
    assignable_roles = [
        'admin',
        'supervisor',
        'planning',
        'operator',
        'fab_master',
        'file_master'
    ]
    users = db.query(User).filter(
        User.role.in_(assignable_roles),
        or_(User.is_deleted == False, User.is_deleted == None)
    ).all()
    
    return [
        {
            "user_id": u.user_id,
            "username": u.username,
            "full_name": u.full_name or u.username,
            "role": u.role
        } for u in users
    ]
