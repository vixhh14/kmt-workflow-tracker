from pydantic import BaseModel, Field, field_serializer, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class DashboardProject(BaseModel):
    # Map project_id to id for frontend
    id: str = Field(alias="id")
    name: Optional[str] = Field(default=None, alias="project_name")
    code: Optional[str] = Field(default=None, alias="project_code")
    work_order: Optional[str] = Field(default=None, alias="work_order_number")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class DashboardTask(BaseModel):
    id: str = Field(alias="task_id")
    title: Optional[str] = "Untitled"
    status: Optional[str] = "pending"
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class DashboardMachine(BaseModel):
    id: str = Field(alias="machine_id")
    machine_name: Optional[str] = "Unknown Machine"
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

# ... (DashboardUser/Operator skipped, they seem fine but check below) ...

class OperatorTask(BaseModel):
    id: str
    title: Optional[str] = "Untitled"
    project: Optional[str] = None
    description: Optional[str] = None
    part_item: Optional[str] = None
    nos_unit: Optional[str] = None
    status: Optional[str] = "pending"
    priority: Optional[str] = "MEDIUM"
    assigned_to: Optional[str] = None
    machine_id: Optional[str] = None
    machine_name: Optional[str] = None
    assigned_by: Optional[str] = None
    assigned_by_name: Optional[str] = None
    due_date: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_duration_seconds: int = 0
    total_held_seconds: int = 0
    holds: List[OperatorHold] = []

    @field_serializer('due_date', 'created_at', 'started_at', 'completed_at')
    def serialize_dates(self, v, _info):
        return v or None

class ProjectAnalyticsStats(BaseModel):
    total: int
    yet_to_start: int
    in_progress: int
    completed: int
    on_hold: int

class ProjectAnalyticsChart(BaseModel):
    yet_to_start: int
    in_progress: int
    completed: int
    on_hold: int

class ProjectAnalyticsOut(BaseModel):
    project: str
    stats: ProjectAnalyticsStats
    chart: ProjectAnalyticsChart

class DailyMachineReportItem(BaseModel):
    machine_id: str
    machine_name: str
    unit: str
    category: str
    date: str
    runtime_seconds: int
    tasks_run_count: int
    is_running_now: bool
    status: str

class DailyMachineReportOut(BaseModel):
    date: str
    report: List[DailyMachineReportItem]

class DailyUserReportItem(BaseModel):
    user_id: str
    username: str
    full_name: Optional[str] = None
    role: str
    date: str
    tasks_worked_count: int
    total_work_seconds: int
    machines_used: List[str]
    status: str

class DailyUserReportOut(BaseModel):
    date: str
    report: List[DailyUserReportItem]

class MonthlyPerformanceChartItem(BaseModel):
    month: str
    tasks_completed: int
    aht: float

class MonthlyPerformanceCSVRow(BaseModel):
    month: str
    tasks_completed: int
    total_runtime_hms: str
    total_runtime_seconds: int
    aht_hms: str
    aht_seconds: int

class MonthlyPerformanceOut(BaseModel):
    year: int
    chart_data: List[MonthlyPerformanceChartItem]
    csv_rows: List[MonthlyPerformanceCSVRow]

class DetailedMachineActivityItem(BaseModel):
    task_id: str
    task_title: str
    operator: str
    start_time: str
    end_time: Optional[str] = None
    runtime_seconds: int

    held_time_seconds: int
    status: str

class DetailedHold(BaseModel):
    start: str
    end: Optional[str] = None
    reason: Optional[str] = None
    duration_seconds: int

class DetailedUserActivityItem(BaseModel):
    task_id: str
    task_title: str
    machine_name: str
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: int

    holds: List[DetailedHold]
    status: str
