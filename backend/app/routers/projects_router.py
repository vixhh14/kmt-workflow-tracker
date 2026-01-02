from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
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

from app.schemas.project_schema import ProjectCreate, ProjectOut, ProjectUpdate

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
    except IntegrityError as e:
        db.rollback()
        print(f"Integrity Error creating project: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Project with this code or name already exists.")
    except Exception as e:
        db.rollback()
        print(f"Error creating project: {str(e)}")
        # Return the actual error message for debugging purposes
        raise HTTPException(status_code=500, detail=f"Internal Database Error: {str(e)}")

@router.get("/{project_id}", response_model=ProjectOut)
async def read_project(project_id: str, db: Session = Depends(get_db)):
    """
    Get a specific project by ID.
    """
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str, 
    project_update: ProjectUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing project.
    """
    db_project = db.query(Project).filter(Project.project_id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.dict(exclude_unset=True)
    
    # Validation for project_code if provided
    if "project_code" in update_data and update_data["project_code"]:
        new_code = update_data["project_code"].strip()
        existing = db.query(Project).filter(
            Project.project_code == new_code,
            Project.project_id != project_id,
            or_(Project.is_deleted == False, Project.is_deleted == None)
        ).first()
        if existing:
             raise HTTPException(status_code=409, detail=f"Project code '{new_code}' is already in use.")
        update_data["project_code"] = new_code

    if "project_name" in update_data:
        update_data["project_name"] = update_data["project_name"].strip()

    # Apply updates
    for key, value in update_data.items():
        setattr(db_project, key, value)
    
    try:
        db.commit()
        db.refresh(db_project)
        
        # Also sync project name in Tasks table for many tasks referencing this project
        from app.models.models_db import Task
        db.query(Task).filter(Task.project_id == project_id).update({"project": db_project.project_name})
        db.commit()
        
        db_project.id = db_project.project_id
        db_project.name = db_project.project_name
        return db_project
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error while updating project: {str(e)}")

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """
    Delete a project.
    """
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project.is_deleted = True
    db.commit()
    return {"message": "Project deleted successfully"}
