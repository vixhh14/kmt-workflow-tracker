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

from app.schemas.project_schema import ProjectCreate, ProjectOut

# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------

from app.core.dependencies import get_current_user
from app.models.models_db import User

@router.get("", response_model=List[ProjectOut])
async def read_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all projects.
    """
    projects = db.query(Project).filter(or_(Project.is_deleted == False, Project.is_deleted == None)).all()
    for p in projects:
        p.id = p.project_id
        p.name = p.project_name
    return projects

@router.post("", response_model=ProjectOut)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project.
    """
    # 1. Validation
    if not project.project_name or not project.project_name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    if not project.project_code or not project.project_code.strip():
        raise HTTPException(status_code=400, detail="Project code is required")
    
    # 2. Check if project code already exists (Ignoring soft-deleted ones)
    existing = db.query(Project).filter(
        Project.project_code == project.project_code.strip(),
        or_(Project.is_deleted == False, Project.is_deleted == None)
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail=f"Project code '{project.project_code}' is already in use by an active project.")
    
    try:
        new_project = Project(
            project_name=project.project_name.strip(),
            work_order_number=project.work_order_number.strip() if project.work_order_number else None,
            client_name=project.client_name.strip() if project.client_name else None,
            project_code=project.project_code.strip(),
            created_at=get_current_time_ist(),
            is_deleted=False
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        return new_project
    except Exception as e:
        db.rollback()
        print(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal database error while creating project: {str(e)}")

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
