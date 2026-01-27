from typing import Optional, Any
from app.models.models_db import Task, FilingTask, FabricationTask
from fastapi import HTTPException

def find_any_task(db: Any, task_id: str):
    """
    Look for a task in all three sheets: tasks, filingtasks, fabricationtasks.
    Returns the task object and its type.
    """
    if not task_id:
        return None, None

    # 1. Search General Tasks
    task = db.query(Task).filter(id=task_id).first()
    if task:
        return task, "general"

    # 2. Search Filing Tasks
    task = db.query(FilingTask).filter(id=task_id).first()
    if task:
        return task, "filing"

    # 3. Search Fabrication Tasks
    task = db.query(FabricationTask).filter(id=task_id).first()
    if task:
        return task, "fabrication"

    return None, None
