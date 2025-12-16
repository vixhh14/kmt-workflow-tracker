from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from datetime import datetime
import uuid
from app.models.models_db import Project
from app.core.database import get_db
from app.core.time_utils import get_current_time_ist

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

# ----------------------------------------------------------------------
# Pydantic Schemas
# ----------------------------------------------------------------------
class ProjectCreate(BaseModel):
    project_name: str
    work_order_number: Optional[str] = None
    client_name: Optional[str] = None
    project_code: str

class ProjectOut(BaseModel):
    project_id: int
    project_name: str
    work_order_number: Optional[str] = None
    client_name: Optional[str] = None
    project_code: str
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------

@router.get("/", response_model=List[ProjectOut])
async def read_projects(db: Session = Depends(get_db)):
    """
    Get all projects.
    """
    return db.query(Project).filter(or_(Project.is_deleted == False, Project.is_deleted == None)).all()

@router.post("/", response_model=ProjectOut)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project.
    """
    # Check if project code already exists
    existing = db.query(Project).filter(Project.project_code == project.project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project code already exists")
    
    new_project = Project(
        # project_id is auto-increment
        project_name=project.project_name,
        work_order_number=project.work_order_number,
        client_name=project.client_name,
        project_code=project.project_code,
        created_at=get_current_time_ist(),
        is_deleted=False
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return new_project

@router.get("/{project_id}", response_model=ProjectOut)
async def read_project(project_id: int, db: Session = Depends(get_db)):
    """
    Get a specific project by ID.
    """
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    Delete a project.
    """
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project.is_deleted = True
    db.commit()
    return {"message": "Project deleted successfully"}
