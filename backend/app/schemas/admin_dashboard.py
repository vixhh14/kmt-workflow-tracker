from pydantic import BaseModel
from typing import List, Optional

class ProjectSummaryResponse(BaseModel):
    total_projects: int
    completed: int
    in_progress: int
    yet_to_start: int
    held: int

class ProjectStatusChartItem(BaseModel):
    label: str
    value: int

class ProjectStatusChartResponse(BaseModel):
    __root__: List[ProjectStatusChartItem]

class UserInfo(BaseModel):
    id: str
    name: str
    role: Optional[str] = None

class AttendanceSummaryResponse(BaseModel):
    present_users: List[UserInfo]
    absent_users: List[UserInfo]
    total_users: int
    present_count: int
    absent_count: int

class TaskStatisticsResponse(BaseModel):
    total_tasks: int
    completed: int
    in_progress: int
    pending: int
    on_hold: int
