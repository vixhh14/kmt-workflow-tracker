from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.models.models_db import Task, User, Machine, FilingTask, FabricationTask, Project as DBProject
from sqlalchemy import or_

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
        # Get all tasks from all tables (Normal, Filing, Fabrication)
        general_tasks = db.query(Task).filter(or_(Task.is_deleted == False, Task.is_deleted == None)).all()
        filing_tasks = db.query(FilingTask).filter(or_(FilingTask.is_deleted == False, FilingTask.is_deleted == None)).all()
        fabrication_tasks = db.query(FabricationTask).filter(or_(FabricationTask.is_deleted == False, FabricationTask.is_deleted == None)).all()
        
        # Combine and normalize for stats processing
        all_tasks = []
        for t in general_tasks:
            all_tasks.append({
                'title': t.title,
                'status': t.status,
                'project_id': t.project_id,
                'project_obj': t.project_obj,
                'project': t.project,
                'machine_id': t.machine_id,
                'assigned_to': t.assigned_to
            })
        for t in filing_tasks:
            all_tasks.append({
                'title': t.part_item, # Normalizing part_item to title
                'status': t.status,
                'project_id': t.project_id,
                'project_obj': t.project_obj,
                'project': None, # Filing tasks don't have legacy project string
                'machine_id': t.machine_id,
                'assigned_to': t.assigned_to
            })
        for t in fabrication_tasks:
            all_tasks.append({
                'title': t.part_item, # Normalizing part_item to title
                'status': t.status,
                'project_id': t.project_id,
                'project_obj': t.project_obj,
                'project': None,
                'machine_id': t.machine_id,
                'assigned_to': t.assigned_to
            })
        
        # Get all projects initially to ensure non-empty dashboard
        projects = db.query(DBProject).filter(or_(DBProject.is_deleted == False, DBProject.is_deleted == None)).all()
        
        project_map = {p.project_name: {
            'total': 0, 'completed': 0, 'ended': 0, 'in_progress': 0, 'pending': 0, 'on_hold': 0
        } for p in projects}
        project_map["Unassigned"] = {'total': 0, 'completed': 0, 'ended': 0, 'in_progress': 0, 'pending': 0, 'on_hold': 0}

        for task in all_tasks:
            # Safe logic to determine Project Name
            p_name = "Unassigned"
            
            try:
                # 1. Try relationship object
                if 'project_obj' in task and task['project_obj']:
                    p_name = task['project_obj'].project_name
                # 2. Try relationship via project_id lookup if not normalized
                elif 'project_id' in task and task['project_id']:
                    # Since we have projects list, we can look it up
                    for p in projects:
                        if p.project_id == task['project_id']:
                            p_name = p.project_name
                            break
                # 3. Fallback to legacy string field
                elif 'project' in task and task['project'] and task['project'] != '-' and task['project'].strip():
                     p_name = task['project']
            except Exception:
                 p_name = "Unassigned"

            if not p_name: p_name = "Unassigned"
            
            if p_name not in project_map:
                project_map[p_name] = {'total': 0, 'completed': 0, 'ended': 0, 'in_progress': 0, 'pending': 0, 'on_hold': 0}
            
            project_map[p_name]['total'] += 1
            
            status_key = (task['status'] or "").lower().replace(" ", "_")
            if status_key in ['completed', 'ended', 'in_progress', 'pending', 'on_hold']:
                project_map[p_name][status_key] += 1
        
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
        total_projects = len(projects)
        active_machine_ids = set()
        
        # Robust counting using list comprehensions with safe checks
        total_tasks_running = 0
        pending_tasks = 0
        completed_tasks = 0
        on_hold_tasks = 0
        
        for t in all_tasks:
            s = (t['status'] or "").lower().replace(" ", "_")
            if s == 'in_progress':
                total_tasks_running += 1
                if t['machine_id']:
                     active_machine_ids.add(t['machine_id'])
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
                # Safely query current task across all types
                current_task = db.query(Task).filter(
                    Task.assigned_to == operator.user_id,
                    or_(func.lower(Task.status) == 'in_progress', Task.status == 'In Progress'),
                    or_(Task.is_deleted == False, Task.is_deleted == None)
                ).first()
                if not current_task:
                    current_task = db.query(FilingTask).filter(
                        FilingTask.assigned_to == operator.user_id,
                        or_(func.lower(FilingTask.status) == 'in progress', FilingTask.status == 'In Progress'),
                        or_(FilingTask.is_deleted == False, FilingTask.is_deleted == None)
                    ).first()
                if not current_task:
                    current_task = db.query(FabricationTask).filter(
                        FabricationTask.assigned_to == operator.user_id,
                        or_(func.lower(FabricationTask.status) == 'in progress', FabricationTask.status == 'In Progress'),
                        or_(FabricationTask.is_deleted == False, FabricationTask.is_deleted == None)
                    ).first()
                
                # Normalize title for display
                title = getattr(current_task, 'title', None) or getattr(current_task, 'part_item', None)
                
                operator_status.append({
                    "name": operator.full_name if operator.full_name else operator.username,
                    "current_task": title,
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
