from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SupervisorProjectSummaryResponse(BaseModel):
    total_projects: int
    completed_projects: int
    pending_projects: int
    active_projects: int

class PendingTaskItem(BaseModel):
    id: str
    title: Optional[str] = None
    project: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    machine_id: Optional[str] = None
    machine_name: Optional[str] = None
    assigned_by: Optional[str] = None
    assigned_by_name: Optional[str] = None
    due_date: Optional[str] = None
    created_at: Optional[str] = None

class PendingTaskResponse(BaseModel):
    __root__: List[PendingTaskItem]

class OperatorTaskStatusItem(BaseModel):
    operator: str
    completed: int
    in_progress: int
    pending: int

class OperatorTaskStatusResponse(BaseModel):
    __root__: List[OperatorTaskStatusItem]

class PriorityStatusResponse(BaseModel):
    high: int
    medium: int
    low: int
