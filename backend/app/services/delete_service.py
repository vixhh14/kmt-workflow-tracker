from fastapi import HTTPException
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.models_db import (
    User, Project, Machine, Task, FilingTask, FabricationTask,
    Attendance, TaskHold, TaskTimeLog, MachineRuntimeLog, UserWorkLog,
    Subtask, OutsourceItem
)
import logging

logger = logging.getLogger(__name__)

class DeleteService:
    @staticmethod
    def soft_delete_user(db: Any, user_id: str, current_user_id: str) -> Dict[str, Any]:
        if str(user_id) == str(current_user_id):
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
        user = db.query(User).filter(user_id=user_id).first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        if getattr(user, 'is_deleted', False): return {"message": "Already deleted", "user_id": user_id}
        
        user.is_deleted = True
        user.updated_at = datetime.now().isoformat()
        
        # Cascades - Manual in-memory filter
        all_att = db.query(Attendance).all()
        for att in all_att:
            if str(getattr(att, 'user_id', '')) == str(user_id):
                att.status = "Deleted"
                
        all_logs = db.query(UserWorkLog).all()
        for wl in all_logs:
            if str(getattr(wl, 'user_id', '')) == str(user_id):
                db.delete(wl) # Or wl.is_deleted = True if applicable
                
        db.commit()
        return {"message": "User deleted successfully", "user_id": user_id}

    @staticmethod
    def soft_delete_project(db: Any, project_id: str) -> Dict[str, Any]:
        project = db.query(Project).filter(project_id=project_id).first()
        if not project: raise HTTPException(status_code=404, detail="Project not found")
        
        project.is_deleted = True
        project.updated_at = datetime.now().isoformat()
        
        all_tasks = db.query(Task).all()
        count = 0
        for t in all_tasks:
            if str(getattr(t, 'project_id', '')) == str(project_id):
                t.is_deleted = True
                count += 1
        
        db.commit()
        return {"message": "Project deleted successfully", "tasks_affected": count}

    @staticmethod
    def soft_delete_machine(db: Any, machine_id: str) -> Dict[str, Any]:
        machine = db.query(Machine).filter(id=machine_id).first()
        if not machine: raise HTTPException(status_code=404, detail="Machine not found")
        
        machine.is_deleted = True
        machine.updated_at = datetime.now().isoformat()
        db.commit()
        return {"message": "Success"}

    @staticmethod
    def soft_delete_task(db: Any, task_id: str) -> Dict[str, Any]:
        task = db.query(Task).filter(id=task_id).first()
        if not task: raise HTTPException(status_code=404, detail="Task not found")
        
        task.is_deleted = True
        task.updated_at = datetime.now().isoformat()
        
        # Cascade to logs/holds
        all_holds = db.query(TaskHold).all()
        for h in all_holds:
            if str(getattr(h, 'task_id', '')) == str(task_id):
                db.delete(h)
        
        db.commit()
        return {"message": "Success"}

delete_service = DeleteService()
