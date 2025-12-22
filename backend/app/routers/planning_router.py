from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.models.models_db import Task, User, Machine

router = APIRouter(
    prefix="/planning",
    tags=["planning"],
    responses={404: {"description": "Not found"}},
)

@router.get("/dashboard-summary")
async def get_planning_dashboard_summary(db: Session = Depends(get_db)):
    """
    Get comprehensive dashboard summary for planning dashboard.
    Includes project metrics, task counts, active machines, and operator status.
    """
    try:
        from sqlalchemy import or_
        # Get all tasks (filtered by is_deleted)
        all_tasks = db.query(Task).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).all()
        
        # Project-wise summary
        project_map = {}
        for task in all_tasks:
            # Use project_obj name if available, fallback to legacy project string
            p_name = task.project
            if task.project_id and task.project_obj:
                p_name = task.project_obj.project_name
                
            if not p_name:
                continue
            
            if p_name not in project_map:
                project_map[p_name] = {
                    'total': 0,
                    'completed': 0,
                    'in_progress': 0,
                    'pending': 0,
                    'on_hold': 0
                }
            
            project_map[p_name]['total'] += 1
            if task.status == 'completed':
                project_map[p_name]['completed'] += 1
            elif task.status == 'in_progress':
                project_map[p_name]['in_progress'] += 1
            elif task.status == 'pending':
                project_map[p_name]['pending'] += 1
            elif task.status == 'on_hold':
                project_map[p_name]['on_hold'] += 1
        
        project_summary = []
        for project_name, stats in project_map.items():
            progress = 0
            if stats['total'] > 0:
                progress = (stats['completed'] / stats['total']) * 100
            
            # Determine project status
            status = "Pending"
            if stats['completed'] == stats['total']:
                status = "Completed"
            elif stats['in_progress'] > 0:
                status = "In Progress"
            elif stats['on_hold'] > 0:
                status = "On Hold"
            
            project_summary.append({
                "project": project_name,
                "progress": round(progress, 1),
                "total_tasks": stats['total'],
                "completed_tasks": stats['completed'],
                "status": status
            })
        
        # Sort by progress descending
        project_summary.sort(key=lambda x: x['progress'], reverse=True)
        
        # Global Counts
        total_projects = len(project_summary)
        total_tasks_running = len([t for t in all_tasks if t.status == 'in_progress'])
        pending_tasks = len([t for t in all_tasks if t.status == 'pending'])
        completed_tasks = len([t for t in all_tasks if t.status == 'completed'])
        
        # Count active machines
        active_machine_ids = set()
        for task in all_tasks:
            if task.status == 'in_progress' and task.machine_id:
                active_machine_ids.add(task.machine_id)
        machines_active = len(active_machine_ids)
        
        # Operator status
        operators = db.query(User).filter(User.role == 'operator').all()
        operator_status = []
        
        for operator in operators:
            current_task = db.query(Task).filter(
                Task.assigned_to == operator.user_id,
                Task.status == 'in_progress',
                or_(Task.is_deleted == False, Task.is_deleted == None)
            ).first()
            
            operator_status.append({
                "name": operator.full_name if operator.full_name else operator.username,
                "current_task": current_task.title if current_task else None,
                "status": "Active" if current_task else "Idle"
            })
        
        return {
            "total_projects": total_projects,
            "total_tasks_running": total_tasks_running,
            "machines_active": machines_active,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "project_summary": project_summary,
            "operator_status": operator_status
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch planning dashboard summary: {str(e)}")
