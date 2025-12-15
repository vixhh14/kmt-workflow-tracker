from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, text
from datetime import datetime, date, timezone
from typing import List, Optional
from app.core.database import get_db
from app.models.models_db import Task, User, Attendance
from app.utils.datetime_utils import utc_now, make_aware

router = APIRouter(
    prefix="/admin",
    tags=["admin-dashboard"],
    responses={404: {"description": "Not found"}},
)

@router.get("/projects")
async def get_projects(db: Session = Depends(get_db)):
    """Get list of all unique project names"""
    try:
        projects = db.query(Task.project).filter(
            Task.project != None,
            Task.project != ''
        ).distinct().all()
        
        project_names = [p[0] for p in projects]
        return project_names
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")


@router.get("/project-analytics")
async def get_project_analytics(project: Optional[str] = None, db: Session = Depends(get_db)):
    """Get comprehensive project analytics including stats and chart data"""
    try:
        query = db.query(Task)
        
        # Filter by project if specified and not "all"
        if project and project != 'all':
            query = query.filter(Task.project == project)
        
        tasks = query.all()
        
        # Calculate statistics
        total = len(tasks)
        yet_to_start = len([t for t in tasks if t.status == 'pending'])
        in_progress = len([t for t in tasks if t.status == 'in_progress'])
        completed = len([t for t in tasks if t.status == 'completed'])
        on_hold = len([t for t in tasks if t.status == 'on_hold'])
        
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
async def get_attendance_summary(db: Session = Depends(get_db)):
    """Get attendance summary using attendance service"""
    try:
        from app.services import attendance_service
        
        result = attendance_service.get_attendance_summary(db=db)
        
        if not result.get("success"):
            # Return safe fallback data
            all_users = db.query(User).filter(User.role.in_(['operator', 'supervisor', 'planning'])).all()
            user_list = [
                {
                    "id": u.user_id,
                    "name": u.full_name if u.full_name else u.username,
                    "role": u.role
                }
                for u in all_users
            ]
            
            return {
                "date": date.today().isoformat(),
                "present": 0,
                "absent": len(all_users),
                "late": 0,
                "present_users": [],
                "absent_users": user_list,
                "total_users": len(all_users),
                "records": []
            }
        
        # Map service result to expected frontend format
        return {
            "date": result.get("date"),
            "present": result.get("present", 0),
            "absent": result.get("absent", 0),
            "late": 0,
            "present_users": result.get("present_users", []),
            "absent_users": result.get("absent_users", []),
            "total_users": result.get("total_users", 0),
            "records": result.get("records", [])  # Explicit records list from service
        }
    except Exception as e:
        # Return safe fallback data on error
        try:
            all_users = db.query(User).filter(User.role.in_(['operator', 'supervisor', 'planning'])).all()
            user_list = [
                {
                    "id": u.user_id,
                    "name": u.full_name if u.full_name else u.username,
                    "role": u.role
                }
                for u in all_users
            ]
            
            return {
                "date": date.today().isoformat(),
                "present": 0,
                "absent": len(all_users),
                "late": 0,
                "present_users": [],
                "absent_users": user_list,
                "total_users": len(all_users),
                "records": []
            }
        except:
            return {
                "date": date.today().isoformat(),
                "present": 0,
                "absent": 0,
                "late": 0,
                "present_users": [],
                "absent_users": [],
                "total_users": 0,
                "records": []
            }


# Legacy endpoints for backward compatibility
@router.get("/overall-stats")
async def get_overall_stats(db: Session = Depends(get_db)):
    """Get overall project statistics (LEGACY)"""
    analytics = await get_project_analytics(project='all', db=db)
    return {
        "total_projects": len(db.query(Task.project).filter(Task.project != None, Task.project != '').distinct().all()),
        "completed": analytics['stats']['completed'],
        "in_progress": analytics['stats']['in_progress'],
        "yet_to_start": analytics['stats']['yet_to_start'],
        "held": analytics['stats']['on_hold']
    }


@router.get("/project-status")
async def get_project_status(project: Optional[str] = None, db: Session = Depends(get_db)):
    """Get project status distribution (LEGACY)"""
    analytics = await get_project_analytics(project=project, db=db)
    return analytics['chart']


@router.get("/task-stats")
async def get_task_stats(project: Optional[str] = None, db: Session = Depends(get_db)):
    """Get task statistics (LEGACY)"""
    analytics = await get_project_analytics(project=project, db=db)
    return analytics['stats']
