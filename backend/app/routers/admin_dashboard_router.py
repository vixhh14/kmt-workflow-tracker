
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import date
from app.core.database import get_db
from app.models.models_db import Task, User, Attendance, Project

router = APIRouter(
    prefix="/admin",
    tags=["admin-dashboard"],
    responses={404: {"description": "Not found"}},
)

@router.get("/projects")
async def get_projects(db: any = Depends(get_db)):
    """Get list of all unique project names from Google Sheets."""
    try:
        all_projects = [p for p in db.query(Project).all() if not p.is_deleted]
        project_names = [p.project_name for p in all_projects if p.project_name]
        
        # Get projects from tasks too (legacy sync)
        all_tasks = [t for t in db.query(Task).all() if not t.is_deleted]
        task_projects = [t.project for t in all_tasks if t.project]
        
        # Merge and sort
        unique_projects = sorted(list(set(project_names + task_projects)))
        return unique_projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

from app.schemas.dashboard_schema import ProjectAnalyticsOut

@router.get("/project-analytics", response_model=ProjectAnalyticsOut)
async def get_project_analytics(project: Optional[str] = None, db: any = Depends(get_db)):
    """Get comprehensive project analytics using Google Sheets data."""
    try:
        all_tasks = [t for t in db.query(Task).all() if not t.is_deleted]
        all_p_objs = [p for p in db.query(Project).all() if not p.is_deleted]
        p_map = {str(p.id): p.project_name for p in all_p_objs}

        # Filter tasks by project if specified
        if project and project != 'all':
            tasks = []
            for t in all_tasks:
                t_project_name = t.project
                if not t_project_name or t_project_name == "-":
                    t_project_name = p_map.get(str(t.project_id))
                
                if t_project_name == project:
                    tasks.append(t)
        else:
            tasks = all_tasks
            
        # Calculate statistics
        total = len(tasks)
        yet_to_start = len([t for t in tasks if str(t.status).lower() == 'pending'])
        in_progress = len([t for t in tasks if str(t.status).lower() == 'in_progress'])
        completed = len([t for t in tasks if str(t.status).lower() == 'completed'])
        on_hold = len([t for t in tasks if str(t.status).lower() == 'on_hold'])
        
        return {
            "project": project if project else "all",
            "stats": {
                "total": total,
                "yet_to_start": yet_to_start,
                "in_progress": in_progress,
                "completed": completed,
                "on_hold": on_hold
            },
            "chart": {
                "yet_to_start": yet_to_start,
                "in_progress": in_progress,
                "completed": completed,
                "on_hold": on_hold
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project analytics: {str(e)}")

@router.get("/attendance-summary")
async def get_attendance_summary(db: any = Depends(get_db)):
    """Get attendance summary from service."""
    try:
        from app.services import attendance_service
        from app.core.time_utils import get_today_date_ist
        today = get_today_date_ist().isoformat()
        return attendance_service.get_attendance_summary(db=db, target_date_str=today)
    except Exception as e:
        print(f"❌ Error in admin attendance summary: {e}")
        return {
            "success": False,
            "date": date.today().isoformat(),
            "present": 0,
            "absent": 0,
            "total_users": 0,
            "records": []
        }

# Legacy support
@router.get("/overall-stats")
async def get_overall_stats(db: any = Depends(get_db)):
    analytics = await get_project_analytics(project='all', db=db)
    all_tasks = [t for t in db.query(Task).all() if not t.is_deleted]
    project_counts = len(set([t.project for t in all_tasks if t.project]))
    
    return {
        "total_projects": project_counts,
        "completed": analytics['stats']['completed'],
        "in_progress": analytics['stats']['in_progress'],
        "yet_to_start": analytics['stats']['yet_to_start'],
        "held": analytics['stats']['on_hold']
    }

@router.get("/project-status")
async def get_project_status(project: Optional[str] = None, db: any = Depends(get_db)):
    analytics = await get_project_analytics(project=project, db=db)
    return analytics['chart']

@router.get("/task-stats")
async def get_task_stats(project: Optional[str] = None, db: any = Depends(get_db)):
    analytics = await get_project_analytics(project=project, db=db)
    return analytics['stats']
