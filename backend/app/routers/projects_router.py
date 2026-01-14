from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Any
from datetime import datetime
import uuid
from app.models.models_db import Project, Task, User
from app.core.database import get_db
from app.core.time_utils import get_current_time_ist
from app.schemas.project_schema import ProjectCreate, ProjectOut, ProjectUpdate
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=List[ProjectOut])
async def read_projects(
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all projects."""
    all_projects = db.query(Project).all()
    projects = [p for p in all_projects if not getattr(p, 'is_deleted', False)]
    
    # Map attributes for frontend compatibility if needed by the schema
    for p in projects:
        p.id = str(p.project_id)
        p.name = p.project_name
    return projects

@router.post("", response_model=ProjectOut)
async def create_project(project: ProjectCreate, db: Any = Depends(get_db)):
    """Create a new project."""
    if not project.project_name or not project.project_name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    if not project.project_code or not project.project_code.strip():
        raise HTTPException(status_code=400, detail="Project code is required")
    
    # Check if project code already exists
    all_projects = db.query(Project).all()
    existing = next((p for p in all_projects if str(p.project_code).strip() == project.project_code.strip()), None)
    
    if existing:
        status_msg = "active" if not getattr(existing, 'is_deleted', False) else "deleted"
        raise HTTPException(status_code=409, detail=f"Project code '{project.project_code}' already exists (Status: {status_msg}).")
    
    try:
        new_project = Project(
            project_id=str(uuid.uuid4()),
            project_name=project.project_name.strip(),
            work_order_number=project.work_order_number.strip() if project.work_order_number else None,
            client_name=project.client_name.strip() if project.client_name else None,
            project_code=project.project_code.strip(),
            created_at=datetime.now().isoformat(),
            is_deleted=False
        )
        
        db.add(new_project)
        db.commit()
        
        # Set convenience attributes
        new_project.id = str(new_project.project_id)
        new_project.name = str(new_project.project_name)
        
        return new_project
    except Exception as e:
        print(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}", response_model=ProjectOut)
async def read_project(project_id: str, db: Any = Depends(get_db)):
    """Get a specific project by ID."""
    project = db.query(Project).filter(project_id=project_id).first()
    if not project or getattr(project, 'is_deleted', False):
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.id = str(project.project_id)
    project.name = project.project_name
    return project

@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str, 
    project_update: ProjectUpdate, 
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing project."""
    db_project = db.query(Project).filter(project_id=project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.dict(exclude_unset=True)
    
    if "project_code" in update_data and update_data["project_code"]:
        new_code = update_data["project_code"].strip()
        all_projects = db.query(Project).all()
        existing = next((p for p in all_projects if str(p.project_code) == new_code and str(p.project_id) != str(project_id) and not getattr(p, 'is_deleted', False)), None)
        if existing:
             raise HTTPException(status_code=409, detail=f"Project code '{new_code}' is already in use.")
        update_data["project_code"] = new_code

    if "project_name" in update_data:
        update_data["project_name"] = update_data["project_name"].strip()

    # Apply updates
    for key, value in update_data.items():
        setattr(db_project, key, value)
    
    db_project.updated_at = datetime.now().isoformat()
    db.commit()
    
    # Sync project name in Tasks table
    all_tasks = db.query(Task).all()
    for t in all_tasks:
        if str(getattr(t, 'project_id', '')) == str(project_id):
            t.project = db_project.project_name
    
    db.commit()
    
    db_project.id = str(db_project.project_id)
    db_project.name = str(db_project.project_name)
    return db_project

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Any = Depends(get_db)):
    """Delete a project."""
    project = db.query(Project).filter(project_id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project.is_deleted = True
    project.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Project deleted successfully"}
