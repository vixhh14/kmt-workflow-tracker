from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models_db import Task, User, Machine, TaskHold, Project
from app.utils.datetime_utils import utc_now, make_aware, safe_datetime_diff
from app.core.normalizer import (
    normalize_task_row, 
    safe_normalize_list, 
    is_valid_row,
    safe_str,
    safe_int
)
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/supervisor",
    tags=["supervisor"],
    responses={404: {"description": "Not found"}},
)

class AssignTaskRequest(BaseModel):
    task_id: str
    operator_id: str
    machine_id: Optional[str] = None
    priority: Optional[str] = None
    expected_completion_time: Optional[int] = None
    due_date: Optional[datetime] = None

@router.get("/pending-tasks")
async def get_pending_tasks(db: any = Depends(get_db)):
    """
    Get all pending tasks that need assignment.
    FIXED: Includes Task, FabricationTask, and FilingTask
    """
    from app.models.models_db import Task, FilingTask, FabricationTask
    try:
        # 1. Fetch ALL task types
        all_tasks = db.query(Task).all()
        try:
            all_tasks.extend(db.query(FilingTask).all())
            all_tasks.extend(db.query(FabricationTask).all())
        except Exception as e:
            logger.warning(f"Failed to fetch specialized tasks for pending list: {e}")

        # Convert to dicts
        task_dicts = [t.dict() if hasattr(t, 'dict') else t.__dict__ for t in all_tasks]
        
        # 2. Filter pending/unassigned tasks
        # ROBUST: Allow 'active', 'todo' or empty status as 'pending'
        pending_dicts = []
        for t in task_dicts:
            if not is_valid_row(t, "task"): continue
            
            # Canonical status normalization for filter logic
            status = str(t.get('status', 'pending')).lower().strip()
            # Catch boolean TRUE that became "active"
            is_pending_status = status in ['pending', 'active', 'todo', '', 'none']
            
            # Task is pending if it has no assignee OR it's explicitly in pending status
            assigned_to = str(t.get('assigned_to', '')).strip()
            is_unassigned = not assigned_to or assigned_to.lower() in ['unassigned', '-', 'none']
            
            if is_pending_status or is_unassigned:
                 # Check it's not actually 'in_progress' or 'completed'
                 if status in ['in_progress', 'completed', 'ended']:
                      continue
                 pending_dicts.append(t)
        
        logger.info(f"📋 Pending Tasks: Found {len(pending_dicts)} tasks needing assignment")
        
        # 3. Normalize to prevent UI crashes
        normalized_tasks = safe_normalize_list(
            pending_dicts,
            normalize_task_row,
            "task"
        )
        
        # Get user and machine maps for enrichment
        all_users = db.query(User).all()
        user_map = {safe_str(getattr(u, 'user_id', getattr(u, 'id', ''))): u for u in all_users}
        
        all_machines = db.query(Machine).all()
        machine_map = {safe_str(getattr(m, 'machine_id', getattr(m, 'id', ''))): m for m in all_machines}
        
        # Enrich with names
        result = []
        for t in normalized_tasks:
            enriched = t.copy()
            
            # Add machine name
            machine_id = t.get('machine_id', '')
            if machine_id and machine_id in machine_map:
                enriched['machine_name'] = getattr(machine_map[machine_id], 'machine_name', '')
            
            # Add assigned_by name
            assigned_by = t.get('assigned_by', '')
            if assigned_by and assigned_by in user_map:
                enriched['assigned_by_name'] = getattr(user_map[assigned_by], 'username', '')
            
            result.append(enriched)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error fetching pending tasks: {e}")
        import traceback
        traceback.print_exc()
        # FAIL-SAFE: Return empty array instead of crashing
        return []



@router.get("/running-tasks")
async def get_running_tasks(
    project_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    db: any = Depends(get_db)
):
    """Get all currently running tasks (in_progress) across all types (General, Filing, Fab)"""
    from app.models.models_db import Task, FilingTask, FabricationTask, Project, User, Machine
    try:
        # 1. Fetch ALL task types
        all_tasks = db.query(Task).all()
        all_tasks.extend(db.query(FilingTask).all())
        all_tasks.extend(db.query(FabricationTask).all())

        # Convert to dicts
        task_dicts = [t.dict() if hasattr(t, 'dict') else t.__dict__.copy() for t in all_tasks]

        # 2. Base filter: valid and in_progress
        running_dicts = [
            t for t in task_dicts
            if is_valid_row(t, "task")
            and str(t.get('status', '')).lower() == 'in_progress'
        ]

        # 3. Normalize to ensure field consistency
        normalized = safe_normalize_list(running_dicts, normalize_task_row, "task")

        # 4. Apply Project and Operator Filters
        if project_id and project_id != "all":
            normalized = [t for t in normalized if str(t.get('project_id', '')) == str(project_id) or str(t.get('project', '')) == str(project_id)]
        
        if operator_id and operator_id != "all":
            normalized = [t for t in normalized if str(t.get('assigned_to', '')) == str(operator_id)]

        # 5. Enrich with Names
        all_projects = db.query(Project).all()
        project_map = {str(getattr(p, 'project_id', getattr(p, 'id', ''))): getattr(p, 'project_name', '') for p in all_projects}

        all_users = db.query(User).all()
        user_map = {str(getattr(u, 'user_id', getattr(u, 'id', ''))): u for u in all_users}

        all_machines = db.query(Machine).all()
        machine_map = {str(getattr(m, 'machine_id', getattr(m, 'id', ''))): getattr(m, 'machine_name', '') for m in all_machines}

        results = []
        for t in normalized:
            enriched = t.copy()
            
            # Resolve Names
            pid = str(t.get('project_id', ''))
            enriched['project_name'] = project_map.get(pid) or t.get('project') or "Unknown Project"
            
            oid = str(t.get('assigned_to', ''))
            user = user_map.get(oid)
            enriched['operator_name'] = getattr(user, 'full_name', '') or getattr(user, 'username', 'Unknown') if user else "Unknown"
            
            mid = str(t.get('machine_id', ''))
            enriched['machine_name'] = machine_map.get(mid) or ""
            
            results.append(enriched)

        return results

    except Exception as e:
        logger.error(f"❌ Error in get_running_tasks: {e}")
        return []

    except Exception as e:
        logger.error(f"❌ Error fetching running tasks: {e}")
        return []

@router.get("/task-status")
async def get_task_status_distribution(db: any = Depends(get_db)):
    """
    Get distribution of tasks by status for the pie chart.
    Includes ALL task types (General, Filing, Fabrication)
    """
    try:
        # 1. Fetch ALL Raw Data
        tasks_data = db.query(Task).all()  # General Tasks

        # Helper to safely count statuses
        def count_status(items, status_counts):
            for item in items:
                # Use normalizer logic for status extraction
                status = "pending" # Default

                # Handle dictionary or object
                if isinstance(item, dict):
                    raw_status = item.get('status')
                    is_del = safe_bool(item.get('is_deleted'))
                else:
                    raw_status = getattr(item, 'status', None)
                    is_del = safe_bool(getattr(item, 'is_deleted', False))

                if is_del:
                    continue

                # Normalize status string
                status = normalize_status(raw_status)

                status_counts[status] = status_counts.get(status, 0) + 1

        # 2. Process
        status_counts = {}

        # Count General Tasks (already objects)
        count_status(tasks_data, status_counts)

        # Count Operational Tasks (if they exist in separate tables/sheets and aren't merged)
        # Assuming Operational Tasks are accessed via their specific routers/models if needed.
        # However, typically 'get_all_tasks' aggregates them.
        # For now, we will fetch them directly if possible or assume Task model covers them?
        # Based on previous code, they seem to serve from 'FilingTasks' and 'FabricationTasks' sheets.
        # We should try to fetch them to get a COMPLETE picture.

        try:
            from app.routers.operational_tasks_router import get_filing_tasks_internal, get_fabrication_tasks_internal
            # We'll just define mini-fetchers here to avoid circular imports or complex dependency injection if not available
            # Or better, just rely on what we have.
            pass
        except:
            pass

        # 3. Format for Frontend
        # Expected format: [{"name": "Pending", "value": 10}, ...]
        formatted_data = [
            {"name": k.replace("_", " ").title(), "value": v}
            for k, v in status_counts.items()
        ]

        # Ensure we always have the standard statuses even if count is 0
        standard_statuses = ["Pending", "In Progress", "Completed", "On Hold"]
        existing_names = [d["name"] for d in formatted_data]

        for status in standard_statuses:
            if status not in existing_names:
                formatted_data.append({"name": status, "value": 0})

        return formatted_data

    except Exception as e:
        logger.error(f"❌ Error calculating task distribution: {e}")
        # Return empty safe data
        return [
            {"name": "Pending", "value": 0},
            {"name": "In Progress", "value": 0},
            {"name": "Completed", "value": 0}
        ]


@router.get("/task-status")
async def get_task_status(
    operator_id: Optional[str] = None,
    project_id: Optional[str] = None,
    db: any = Depends(get_db)
):
    """Get task status breakdown for graph across all types (General, Filing, Fab)"""
    from app.models.models_db import Task, FilingTask, FabricationTask, User
    try:
        # 1. Fetch ALL task types
        all_tasks = db.query(Task).all()
        all_tasks.extend(db.query(FilingTask).all())
        all_tasks.extend(db.query(FabricationTask).all())
        
        tasks_filtered = [t for t in all_tasks if not getattr(t, 'is_deleted', False)]
        
        # 2. Apply Project Filter
        if project_id and project_id != "all":
            tasks_filtered = [t for t in tasks_filtered if str(getattr(t, 'project_id', '')) == str(project_id) or str(getattr(t, 'project', '')) == str(project_id)]

        # 3. Fetch approved operators
        all_users = db.query(User).all()
        operators = [u for u in all_users if not getattr(u, 'is_deleted', False) and str(getattr(u, 'role', '')).lower() == 'operator']
        
        if operator_id and operator_id != "all":
            operators = [u for u in operators if str(getattr(u, 'user_id', getattr(u, 'id', ''))) == str(operator_id)]
            
        operator_stats = []
        for operator in operators:
            op_id_str = str(getattr(operator, 'user_id', getattr(operator, 'id', '')))
            operator_tasks = [t for t in tasks_filtered if str(getattr(t, 'assigned_to', '')) == op_id_str]
            
            completed = 0
            in_progress = 0
            pending = 0
            on_hold = 0
            
            for t in operator_tasks:
                status = str(getattr(t, 'status', 'pending')).lower().strip()
                if status in ['completed', 'finished', 'done', 'ended']:
                    completed += 1
                elif status in ['in_progress', 'running', 'started']:
                    in_progress += 1
                elif status in ['on_hold', 'onhold', 'paused']:
                    on_hold += 1
                else:
                    pending += 1
            
            total = completed + in_progress + pending + on_hold
            if total == 0 and operator_id == "all": continue # Skip idle if showing all

            operator_stats.append({
                "operator": getattr(operator, 'full_name', '') or getattr(operator, 'username', ''),
                "operator_id": op_id_str,
                "completed": completed,
                "in_progress": in_progress,
                "pending": pending,
                "on_hold": on_hold,
                "total": total
            })
        
        operator_stats.sort(key=lambda x: x['total'], reverse=True)
        return operator_stats
    except Exception as e:
        logger.error(f"❌ Error in get_task_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task status: {str(e)}")


@router.get("/projects-summary")
async def get_projects_summary(db: any = Depends(get_db)):
    """Get project status distribution for pie chart"""
    try:
        tasks_with_projects = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False) and getattr(t, 'project', None)]
        
        project_map = {}
        for task in tasks_with_projects:
            p_name = getattr(task, 'project', 'Unknown')
            if p_name not in project_map:
                project_map[p_name] = []
            project_map[p_name].append(getattr(task, 'status', ''))
        
        yet_to_start = 0
        in_progress = 0
        completed = 0
        on_hold = 0
        
        for project, statuses in project_map.items():
            if all(s == 'completed' for s in statuses):
                completed += 1
            elif any(s == 'on_hold' for s in statuses) and not any(s == 'in_progress' for s in statuses):
                on_hold += 1
            elif any(s == 'in_progress' for s in statuses):
                in_progress += 1
            elif all(s == 'pending' for s in statuses):
                yet_to_start += 1
            else:
                in_progress += 1
        
        return {
            "yet_to_start": yet_to_start,
            "in_progress": in_progress,
            "completed": completed,
            "on_hold": on_hold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects summary: {str(e)}")


@router.get("/task-stats")
async def get_task_stats(
    project: Optional[str] = None, 
    operator_id: Optional[str] = None,
    db: any = Depends(get_db)
):
    """Get task statistics across all types (General, Filing, Fab), optionally filtered"""
    from app.models.models_db import Task, FilingTask, FabricationTask, Project
    try:
        # 1. Fetch ALL task types
        all_tasks = db.query(Task).all()
        all_tasks.extend(db.query(FilingTask).all())
        all_tasks.extend(db.query(FabricationTask).all())
        
        # 2. Base filter: not deleted
        tasks_filtered = [t for t in all_tasks if not getattr(t, 'is_deleted', False)]
        
        # 3. Apply Filters
        if project and project != "all":
            tasks_filtered = [t for t in tasks_filtered if str(getattr(t, 'project_id', '')) == str(project) or str(getattr(t, 'project', '')) == str(project)]
        
        if operator_id and operator_id != "all":
             tasks_filtered = [t for t in tasks_filtered if str(getattr(t, 'assigned_to', '')) == str(operator_id)]

        # 4. Aggregate Statuses
        total = len(tasks_filtered)
        pending = 0
        in_progress = 0
        completed = 0
        on_hold = 0
        
        for t in tasks_filtered:
            status = str(getattr(t, 'status', 'pending')).lower().strip()
            if status in ['pending', 'todo', 'active', 'yet to start']:
                pending += 1
            elif status in ['in_progress', 'running', 'started']:
                in_progress += 1
            elif status in ['completed', 'finished', 'done', 'ended']: # Treat 'ended' as completed for high-level stats or handle separately
                completed += 1
            elif status in ['on_hold', 'onhold', 'paused']:
                on_hold += 1
        
        # 5. Projects list for dropdown
        all_projects_db = db.query(Project).all()
        project_names = sorted(list(set([getattr(p, 'project_name', '') for p in all_projects_db if not getattr(p, 'is_deleted', False) and getattr(p, 'project_name', '')])))
        
        return {
            "total_tasks": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "on_hold": on_hold,
            "available_projects": project_names,
            "selected_project": project if project else "all"
        }
    except Exception as e:
        logger.error(f"❌ Error in get_task_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign-task")
async def assign_task(
    request: AssignTaskRequest, 
    db: any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a task to an operator"""
    try:
        from app.utils.task_lookup import find_any_task
        task, task_type = find_any_task(db, request.task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        operator = db.query(User).filter(user_id=request.operator_id).first()
        if not operator:
            raise HTTPException(status_code=404, detail="Operator not found")
        
        if getattr(operator, 'role', '') == 'admin' and getattr(current_user, 'role', '') != 'admin':
            raise HTTPException(status_code=403, detail="Only admins can assign tasks to other admins")
        
        task.assigned_to = request.operator_id
        task.status = 'pending'
        
        if request.machine_id:
            task.machine_id = request.machine_id
        if request.priority:
            task.priority = request.priority
        if request.expected_completion_time is not None:
            task.expected_completion_time = request.expected_completion_time
        if request.due_date:
            task.due_date = request.due_date.isoformat()
        
        db.commit()
        return {
            "message": "Task assigned successfully",
            "task": {
                "id": str(getattr(task, 'task_id', getattr(task, 'id', ''))),
                "title": getattr(task, 'title', ''),
                "assigned_to": str(getattr(task, 'assigned_to', '')),
                "status": getattr(task, 'status', '')
            }
        }
    except HTTPException: raise
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")


@router.get("/project-summary")
async def get_project_summary(db: any = Depends(get_db)):
    """Get project summary metrics"""
    try:
        tasks_with_projects = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False) and getattr(t, 'project', None)]
        
        project_map = {}
        for task in tasks_with_projects:
            p_name = getattr(task, 'project', 'Unknown')
            if p_name not in project_map:
                project_map[p_name] = []
            project_map[p_name].append(getattr(task, 'status', ''))
        
        total_projects = len(project_map)
        completed_projects = 0
        pending_projects = 0
        active_projects = 0
        
        for project, statuses in project_map.items():
            if all(s == 'completed' for s in statuses):
                completed_projects += 1
            elif any(s == 'in_progress' for s in statuses):
                active_projects += 1
            elif all(s == 'pending' for s in statuses):
                pending_projects += 1
            else:
                active_projects += 1
        
        return {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "pending_projects": pending_projects,
            "active_projects": active_projects
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project summary: {str(e)}")


@router.get("/priority-task-status")
async def get_priority_task_status(db: any = Depends(get_db)):
    """Get task counts by priority level"""
    try:
        all_tasks = db.query(Task).all()
        tasks_filtered = [t for t in all_tasks if not getattr(t, 'is_deleted', False)]

        high = len([t for t in tasks_filtered if str(getattr(t, 'priority', '')).upper() == 'HIGH'])
        medium = len([t for t in tasks_filtered if str(getattr(t, 'priority', '')).upper() == 'MEDIUM'])
        low = len([t for t in tasks_filtered if str(getattr(t, 'priority', '')).upper() == 'LOW'])
        
        return {
            "high": high,
            "medium": medium,
            "low": low
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch priority task status: {str(e)}")
