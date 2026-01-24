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
    """Get all projects from cache."""
    # Query returns all non-deleted projects if we use the right filter
    projects = db.query(Project).filter(is_deleted=False).all()
    
    # Map attributes for frontend compatibility if needed
    results = []
    for p in projects:
        data = p.dict()
        data['name'] = data.get('project_name', '')
        results.append(data)
    return results

@router.post("", response_model=ProjectOut)
async def create_project(project: ProjectCreate, db: Any = Depends(get_db)):
    """Create a new project."""
    if not project.project_name or not project.project_name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    if not project.project_code or not project.project_code.strip():
        raise HTTPException(status_code=400, detail="Project code is required")
    
    # Check if project code already exists
    all_projects = db.query(Project).all()
    existing = next((p for p in all_projects if str(getattr(p, 'project_code', '')).strip() == project.project_code.strip()), None)
    
    if existing:
        status_msg = "active" if not getattr(existing, 'is_deleted', False) else "deleted"
        raise HTTPException(status_code=409, detail=f"Project code '{project.project_code}' already exists (Status: {status_msg}).")
    
    try:
        new_project = Project(
            project_name=project.project_name.strip(),
            work_order_number=project.work_order_number.strip() if project.work_order_number else None,
            client_name=project.client_name.strip() if project.client_name else None,
            project_code=project.project_code.strip(),
            created_at=get_current_time_ist().isoformat(),
            is_deleted=False
        )
        
        db.add(new_project)
        db.commit()
        
        # Set convenience attributes
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
    
    project.name = getattr(project, 'project_name', '')
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
        # Use simple keyword filter for uniqueness
        existing = db.query(Project).filter(project_code=new_code, is_deleted=False).all()
        if any(str(getattr(p, 'project_id', getattr(p, 'id', ''))) != str(project_id) for p in existing):
             raise HTTPException(status_code=409, detail=f"Project code '{new_code}' is already in use.")
        update_data["project_code"] = new_code

    if "project_name" in update_data:
        update_data["project_name"] = update_data["project_name"].strip()

    # Apply updates
    for key, value in update_data.items():
        setattr(db_project, key, value)
    
    db_project.updated_at = get_current_time_ist().isoformat()
    db.commit() # Repository will update the project cache
    
    # Sync project name in Tasks table (All cached)
    # Optimization: Only sync if name changed
    new_name = getattr(db_project, 'project_name', '')
    all_tasks = db.query(Task).filter(project_id=project_id).all()
    for t in all_tasks:
        t.project = new_name
    
    db.commit() # Repository will update the tasks cache
    
    res = db_project.dict()
    res['name'] = res.get('project_name', '')
    return res

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Any = Depends(get_db)):
    """Delete a project."""
    # Robust ID lookup
    all_projects = db.query(Project).all()
    project = None
    pid_to_delete = None
    
    for p in all_projects:
        pid = str(getattr(p, 'project_id', getattr(p, 'id', '')))
        if pid == str(project_id):
            project = p
            pid_to_delete = pid
            break
            
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # REMOVED RESTRICTION: Allow deletion regardless of associated tasks
    # User requirement: Projects should be deletable without any criteria
    print(f"🗑️ Deleting project: {getattr(project, 'project_name', 'Unknown')} (ID: {pid_to_delete})")
        
    project.is_deleted = True
    project.updated_at = get_current_time_ist().isoformat()
    db.commit()
    
    print(f"✅ Project deleted successfully: {pid_to_delete}")
    return {"message": "Project deleted successfully"}
