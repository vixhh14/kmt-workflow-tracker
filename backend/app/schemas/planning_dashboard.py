from pydantic import BaseModel
from typing import List, Optional

class ProjectSummaryItem(BaseModel):
    project: str
    progress: float
    total_tasks: int
    completed_tasks: int
    status: str

class OperatorStatusItem(BaseModel):
    name: str
    current_task: Optional[str] = None
    status: str

class PlanningDashboardResponse(BaseModel):
    total_projects: int
    total_tasks_running: int
    machines_active: int
    pending_tasks: int
    completed_tasks: int
    project_summary: List[ProjectSummaryItem]
    operator_status: List[OperatorStatusItem]
