from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.database import get_db
from app.models.models_db import Task, User, Machine, FilingTask, FabricationTask, Project as DBProject

router = APIRouter(
    prefix="/planning",
    tags=["planning"],
    responses={404: {"description": "Not found"}},
)

@router.get("/dashboard-summary")
async def get_planning_dashboard_summary(db: any = Depends(get_db)):
    """Refactored for SheetsDB with comprehensive aggregation"""
    try:
        # Fetch all task types
        gen_tasks = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False)]
        filing_tasks = [t for t in db.query(FilingTask).all() if not getattr(t, 'is_deleted', False)]
        fab_tasks = [t for t in db.query(FabricationTask).all() if not getattr(t, 'is_deleted', False)]
        
        # Combine and normalize
        all_tasks_data = []
        for t in gen_tasks:
            all_tasks_data.append({
                'status': getattr(t, 'status', 'pending'), 
                'project_id': str(getattr(t, 'project_id', '')), 
                'project': getattr(t, 'project', ''), 
                'machine_id': str(getattr(t, 'machine_id', '')), 
                'assigned_to': str(getattr(t, 'assigned_to', '')), 
                'title': getattr(t, 'title', '')
            })
        for t in filing_tasks:
            all_tasks_data.append({
                'status': getattr(t, 'status', 'pending'), 
                'project_id': str(getattr(t, 'project_id', '')), 
                'project': None, 
                'machine_id': str(getattr(t, 'machine_id', '')), 
                'assigned_to': str(getattr(t, 'assigned_to', '')), 
                'title': getattr(t, 'part_item', '')
            })
        for t in fab_tasks:
            all_tasks_data.append({
                'status': getattr(t, 'status', 'pending'), 
                'project_id': str(getattr(t, 'project_id', '')), 
                'project': None, 
                'machine_id': str(getattr(t, 'machine_id', '')), 
                'assigned_to': str(getattr(t, 'assigned_to', '')), 
                'title': getattr(t, 'part_item', '')
            })
        
        projects = db.query(DBProject).all()
        p_map_info = {str(getattr(p, 'project_id', getattr(p, 'id', ''))): getattr(p, 'project_name', '') for p in projects if not getattr(p, 'is_deleted', False)}
        
        project_stats = {name: {'total': 0, 'completed': 0, 'ended': 0, 'in_progress': 0, 'pending': 0, 'on_hold': 0} for name in p_map_info.values()}
        project_stats["Unassigned"] = {'total': 0, 'completed': 0, 'ended': 0, 'in_progress': 0, 'pending': 0, 'on_hold': 0}
        
        active_machine_ids = set()
        total_running = 0
        total_pending = 0
        total_completed = 0
        total_on_hold = 0
        
        for t in all_tasks_data:
            p_name = p_map_info.get(t['project_id']) or t['project'] or "Unassigned"
            if p_name not in project_stats: 
                project_stats[p_name] = {'total': 0, 'completed': 0, 'ended': 0, 'in_progress': 0, 'pending': 0, 'on_hold': 0}
            
            project_stats[p_name]['total'] += 1
            status = str(t['status']).lower().replace(" ", "_")
            if status in project_stats[p_name]: 
                project_stats[p_name][status] += 1
            
            if status == 'in_progress':
                total_running += 1
                if t['machine_id'] and t['machine_id'] != 'None' and t['machine_id'] != '':
                    active_machine_ids.add(t['machine_id'])
            elif status == 'pending':
                total_pending += 1
            elif status in ['completed', 'ended']:
                total_completed += 1
            elif status == 'on_hold':
                total_on_hold += 1
                
        project_summary = []
        for name, s in project_stats.items():
            if s['total'] == 0 and name != "Unassigned": continue
            done = s['completed'] + s['ended']
            prog = (done / s['total'] * 100) if s['total'] > 0 else 0
            
            proj_status = "Pending"
            if done == s['total'] and s['total'] > 0: proj_status = "Completed"
            elif s['in_progress'] > 0: proj_status = "In Progress"
            elif s['on_hold'] > 0: proj_status = "On Hold"
            
            project_summary.append({
                "project": name, 
                "progress": round(prog, 1), 
                "total_tasks": s['total'],
                "completed_tasks": done, 
                "status": proj_status
            })
        project_summary.sort(key=lambda x: x['progress'], reverse=True)
        
        # Operators
        ops = [u for u in db.query(User).all() 
               if not getattr(u, 'is_deleted', False) 
               and str(getattr(u, 'role', '')).lower() == 'operator'
               and str(getattr(u, 'approval_status', '')).lower() == 'approved']
        
        op_status = []
        for op in ops:
            op_id_str = str(getattr(op, 'user_id', getattr(op, 'id', '')))
            curr = None
            for t in all_tasks_data:
                if t['assigned_to'] == op_id_str and str(t['status']).lower().replace(" ", "_") == 'in_progress':
                    curr = t['title']
                    break
            op_status.append({
                "id": op_id_str,
                "name": getattr(op, 'full_name', '') or getattr(op, 'username', ''), 
                "current_task": curr, 
                "status": "Active" if curr else "Idle"
            })
            
        return {
            "total_projects": len(p_map_info),
            "total_tasks": len(all_tasks_data),
            "total_tasks_running": total_running,
            "machines_active": len(active_machine_ids),
            "pending_tasks": total_pending,
            "completed_tasks": total_completed,
            "on_hold_tasks": total_on_hold,
            "project_summary": project_summary,
            "operator_status": op_status
        }
    except Exception as e:
        print(f"Error in planning dashboard: {e}")
        return {
            "total_projects": 0, "total_tasks": 0, "total_tasks_running": 0, 
            "machines_active": 0, "pending_tasks": 0, "completed_tasks": 0, 
            "on_hold_tasks": 0, "project_summary": [], "operator_status": []
        }
