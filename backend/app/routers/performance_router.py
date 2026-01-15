from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_active_admin
from app.models.models_db import Task, Machine, User, TaskHold

router = APIRouter(prefix="/performance", tags=["Performance"])

@router.get("/machine/{machine_id}")
async def get_machine_performance(machine_id: str, db: any = Depends(get_db)):
    tasks = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False) and str(getattr(t, 'machine_id', '')) == str(machine_id) and str(getattr(t, 'status', '')).lower() == 'completed']
    total_duration = sum(int(getattr(t, 'total_duration_seconds', 0) or 0) for t in tasks)
    return {"machine_id": machine_id, "tasks_completed": len(tasks), "total_runtime_seconds": total_duration}

@router.get("/user/{user_id}")
async def get_user_performance(user_id: str, db: any = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    tasks = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False) and str(getattr(t, 'assigned_to', '')) == str(user_id) and str(getattr(t, 'status', '')).lower() == 'completed']
    total_duration = sum(int(getattr(t, 'total_duration_seconds', 0) or 0) for t in tasks)
    return {"id": user_id, "tasks_completed": len(tasks), "total_work_seconds": total_duration}

@router.get("/details")
async def get_detailed_performance(user_id: str, year: int, month: int, db: any = Depends(get_db)):
    pat = f"{year}-{month:02d}"
    tasks = [t for t in db.query(Task).all() if str(getattr(t, 'assigned_to', '')) == str(user_id) and not getattr(t, 'is_deleted', False) and str(getattr(t, 'created_at', '')).startswith(pat)]
    holds = db.query(TaskHold).all()
    
    res = []
    for t in tasks:
        t_id = str(getattr(t, 'id', ''))
        t_holds = [h for h in holds if str(getattr(h, 'task_id', '')) == t_id]
        res.append({
            "id": t_id, 
            "title": str(getattr(t, 'title', '')), 
            "status": str(getattr(t, 'status', '')),
            "duration": int(getattr(t, 'total_duration_seconds', 0) or 0),
            "held": int(getattr(t, 'total_held_seconds', 0) or 0),
            "holds": [{"start": str(getattr(h, 'hold_started_at', '')), "end": str(getattr(h, 'hold_ended_at', '')), "reason": str(getattr(h, 'hold_reason', ''))} for h in t_holds]
        })
    return res
