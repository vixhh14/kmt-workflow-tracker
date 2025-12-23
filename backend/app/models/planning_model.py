from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PlanningTaskBase(BaseModel):
    task_id: int
    project_name: str
    task_sequence: int
    assigned_supervisor: Optional[str] = None
    status: str = "planning"  # planning, approved, in_progress, completed

class PlanningTaskCreate(PlanningTaskBase):
    pass

class PlanningTaskUpdate(BaseModel):
    project_name: Optional[str] = None
    task_sequence: Optional[int] = None
    assigned_supervisor: Optional[str] = None
    status: Optional[str] = None

class PlanningTask(PlanningTaskBase):
    id: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
