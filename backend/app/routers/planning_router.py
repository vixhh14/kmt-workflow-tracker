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
    NON-CRASHING GUARANTEE: Returns safe defaults if DB queries fail.
    """
    try:
        from sqlalchemy import or_
        from app.models.models_db import Project as DBProject
        
        # Get all tasks (filtered by is_deleted)
        all_tasks = db.query(Task).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).all()
        
        # Project-wise summary
        project_map = {}
        for task in all_tasks:
            # Safe logic to determine Project Name
            p_name = "Unassigned"
            
            try:
                # 1. Try relationship object
                if task.project_obj:
                    p_name = task.project_obj.project_name
                # 2. Fallback to legacy string field
                elif task.project and task.project != '-' and task.project.strip():
                     p_name = task.project
                # 3. Fallback to manual lookup via ID (Handling corrupt IDs safely)
                elif task.project_id:
                    # Defensive ID check: ensure it's a string, passing int to UUID query crashes Postgres
                    pid_str = str(task.project_id).strip()
                    # Only query if it LOOKS like a UUID (len 36 or 32) or at least a string, 
                    # but if it IS an int-like string (e.g. "123") Postgres might still complain comparing to UUID.
                    # Best safety: Try/Except the query itself.
                    try:
                        p_obj = db.query(DBProject).filter(DBProject.project_id == pid_str).first()
                        if p_obj:
                            p_name = p_obj.project_name
                    except Exception:
                        # If query fails (e.g. data type mismatch), ignore and keep "Unassigned"
                         pass
            except Exception:
                 p_name = "Unassigned"

            if not p_name:
                p_name = "Unassigned"
            
            if p_name not in project_map:
                project_map[p_name] = {
                    'total': 0,
                    'completed': 0,
                    'ended': 0,
                    'in_progress': 0,
                    'pending': 0,
                    'on_hold': 0
                }
            
            project_map[p_name]['total'] += 1
            
            status_key = (task.status or "").lower().replace(" ", "_")
            if status_key in ['completed', 'ended', 'in_progress', 'pending', 'on_hold']:
                project_map[p_name][status_key] += 1
            elif status_key == 'in_progress': # handle underscore variation
                 project_map[p_name]['in_progress'] += 1
        
        project_summary = []
        for project_name, stats in project_map.items():
            progress = 0
            if stats['total'] > 0:
                # Progress counts both normally completed and admin-ended tasks
                progress = ((stats['completed'] + stats['ended']) / stats['total']) * 100
            
            # Determine project status
            status = "Pending"
            if (stats['completed'] + stats['ended']) == stats['total']:
                status = "Completed"
            elif stats['in_progress'] > 0:
                status = "In Progress"
            elif stats['on_hold'] > 0:
                status = "On Hold"
            
            project_summary.append({
                "project": project_name,
                "progress": round(progress, 1),
                "total_tasks": stats['total'],
                "completed_tasks": stats['completed'] + stats['ended'],
                "status": status
            })
        
        # Sort by progress descending
        project_summary.sort(key=lambda x: x['progress'], reverse=True)
        
        # Global Counts
        total_projects = len(project_summary)
        active_machine_ids = set()
        
        # Robust counting using list comprehensions with safe checks
        total_tasks_running = 0
        pending_tasks = 0
        completed_tasks = 0
        on_hold_tasks = 0
        
        for t in all_tasks:
            s = (t.status or "").lower().replace(" ", "_")
            if s == 'in_progress':
                total_tasks_running += 1
                if t.machine_id:
                     active_machine_ids.add(t.machine_id)
            elif s == 'pending':
                pending_tasks += 1
            elif s in ['completed', 'ended']:
                completed_tasks += 1
            elif s == 'on_hold':
                on_hold_tasks += 1
        
        machines_active = len(active_machine_ids)
        total_tasks = len(all_tasks)
        
        # Operator status
        operator_status = []
        try:
            operators = db.query(User).filter(User.role == 'operator').all()
            for operator in operators:
                # Safely query current task
                current_task = db.query(Task).filter(
                    Task.assigned_to == operator.user_id,
                    or_(func.lower(Task.status) == 'in_progress', Task.status == 'In Progress'),
                    or_(Task.is_deleted == False, Task.is_deleted == None)
                ).first()
                
                operator_status.append({
                    "name": operator.full_name if operator.full_name else operator.username,
                    "current_task": current_task.title if current_task else None,
                    "status": "Active" if current_task else "Idle"
                })
        except Exception:
             # If operator query fails, return empty list rather than 500
             operator_status = []
        
        return {
            "total_projects": total_projects,
            "total_tasks": total_tasks,
            "total_tasks_running": total_tasks_running,
            "machines_active": machines_active,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "on_hold_tasks": on_hold_tasks,
            "project_summary": project_summary,
            "operator_status": operator_status
        }
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in Planning Dashboard: {traceback.format_exc()}")
        # Fail-safe return
        return {
            "total_projects": 0,
            "total_tasks": 0,
            "total_tasks_running": 0,
            "machines_active": 0,
            "pending_tasks": 0,
            "completed_tasks": 0,
            "on_hold_tasks": 0,
            "project_summary": [],
            "operator_status": []
        }
