
import uuid
from datetime import datetime
from typing import Optional
from app.core.time_utils import get_current_time_ist

class SheetsModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # Ensure standard metadata
        now = get_current_time_ist().isoformat()
        if not hasattr(self, "created_at") or self.created_at is None:
            self.created_at = now
        if not hasattr(self, "updated_at") or self.updated_at is None:
            self.updated_at = now
        if not hasattr(self, "is_deleted") or self.is_deleted is None:
            self.is_deleted = False

    def dict(self):
        # Exclude internal attributes
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

class User(SheetsModel):
    __tablename__ = "users"
    def __init__(self, **kwargs):
        # Sync id, user_id and others
        u_id = kwargs.get("user_id") or kwargs.get("id")
        if not u_id: u_id = str(uuid.uuid4())
        kwargs["id"] = u_id
        kwargs["user_id"] = u_id
        # Ensure active is set
        if "active" not in kwargs and "is_active" in kwargs:
            kwargs["active"] = kwargs["is_active"]
        if "active" not in kwargs:
            kwargs["active"] = True
        super().__init__(**kwargs)

class Project(SheetsModel):
    __tablename__ = "projects"
    def __init__(self, **kwargs):
        # Sync project_id and legacy id
        p_id = kwargs.get("project_id") or kwargs.get("id")
        if not p_id: p_id = str(uuid.uuid4())
        kwargs["project_id"] = p_id
        kwargs["id"] = p_id
        super().__init__(**kwargs)

class Task(SheetsModel):
    __tablename__ = "tasks"
    def __init__(self, **kwargs):
        # Sync task_id and legacy id
        t_id = kwargs.get("task_id") or kwargs.get("id")
        if not t_id: t_id = str(uuid.uuid4())
        kwargs["task_id"] = t_id
        kwargs["id"] = t_id
        super().__init__(**kwargs)

class Attendance(SheetsModel):
    __tablename__ = "attendance"
    def __init__(self, **kwargs):
        # Sync attendance_id and legacy id
        a_id = kwargs.get("attendance_id") or kwargs.get("id")
        if not a_id: a_id = f"att_{int(datetime.now().timestamp())}"
        kwargs["attendance_id"] = a_id
        kwargs["id"] = a_id
        super().__init__(**kwargs)

class FabricationTask(SheetsModel):
    __tablename__ = "fabricationtasks"
    def __init__(self, **kwargs):
        # Sync fabrication_task_id and legacy id
        f_id = kwargs.get("fabrication_task_id") or kwargs.get("id")
        if not f_id: f_id = str(uuid.uuid4())
        kwargs["fabrication_task_id"] = f_id
        kwargs["id"] = f_id
        super().__init__(**kwargs)

class FilingTask(SheetsModel):
    __tablename__ = "filingtasks"
    def __init__(self, **kwargs):
        # Sync filing_task_id and legacy id
        f_id = kwargs.get("filing_task_id") or kwargs.get("id")
        if not f_id: f_id = str(uuid.uuid4())
        kwargs["filing_task_id"] = f_id
        kwargs["id"] = f_id
        super().__init__(**kwargs)

class TaskTimeLog(SheetsModel):
    __tablename__ = "tasktimelog"
    def __init__(self, **kwargs):
        l_id = kwargs.get("log_id") or kwargs.get("id")
        if not l_id: l_id = str(uuid.uuid4())
        kwargs["log_id"] = l_id
        kwargs["id"] = l_id
        super().__init__(**kwargs)

class TaskHold(SheetsModel):
    __tablename__ = "taskhold"
    def __init__(self, **kwargs):
        h_id = kwargs.get("hold_id") or kwargs.get("id")
        if not h_id: h_id = str(uuid.uuid4())
        kwargs["hold_id"] = h_id
        kwargs["id"] = h_id
        super().__init__(**kwargs)

class MachineRuntimeLog(SheetsModel):
    __tablename__ = "machineruntimelog"
    def __init__(self, **kwargs):
        l_id = kwargs.get("log_id") or kwargs.get("id")
        if not l_id: l_id = str(uuid.uuid4())
        kwargs["log_id"] = l_id
        kwargs["id"] = l_id
        super().__init__(**kwargs)

class UserWorkLog(SheetsModel):
    __tablename__ = "userworklog"
    def __init__(self, **kwargs):
        l_id = kwargs.get("log_id") or kwargs.get("id")
        if not l_id: l_id = str(uuid.uuid4())
        kwargs["log_id"] = l_id
        kwargs["id"] = l_id
        super().__init__(**kwargs)

class Machine(SheetsModel):
    __tablename__ = "machines"
    def __init__(self, **kwargs):
        # Sync id and machine_id
        m_id = kwargs.get("machine_id") or kwargs.get("id")
        if not m_id: m_id = str(uuid.uuid4())
        kwargs["id"] = m_id
        kwargs["machine_id"] = m_id
        # Canonical status
        if "status" not in kwargs:
            kwargs["status"] = "active"
        super().__init__(**kwargs)

class Unit(SheetsModel):
    __tablename__ = "units"
    def __init__(self, **kwargs):
        u_id = kwargs.get("unit_id") or kwargs.get("id")
        if not u_id: u_id = str(uuid.uuid4())
        kwargs["unit_id"] = u_id
        kwargs["id"] = u_id
        super().__init__(**kwargs)

class MachineCategory(SheetsModel):
    __tablename__ = "machinecategories"
    def __init__(self, **kwargs):
        c_id = kwargs.get("category_id") or kwargs.get("id")
        if not c_id: c_id = str(uuid.uuid4())
        kwargs["category_id"] = c_id
        kwargs["id"] = c_id
        super().__init__(**kwargs)

class UserMachine(SheetsModel):
    __tablename__ = "usermachine"

class Subtask(SheetsModel):
    __tablename__ = "subtasks"

class OutsourceItem(SheetsModel):
    __tablename__ = "outsourceitems"

class RescheduleRequest(SheetsModel):
    __tablename__ = "reschedulerequests"
    def __init__(self, **kwargs):
        r_id = kwargs.get("reschedule_id") or kwargs.get("id")
        if not r_id: r_id = str(uuid.uuid4())
        kwargs["reschedule_id"] = r_id
        kwargs["id"] = r_id
        super().__init__(**kwargs)

class PlanningTask(SheetsModel):
    __tablename__ = "planningtasks"
    def __init__(self, **kwargs):
        p_id = kwargs.get("planning_task_id") or kwargs.get("id")
        if not p_id: p_id = str(uuid.uuid4())
        kwargs["planning_task_id"] = p_id
        kwargs["id"] = p_id
        super().__init__(**kwargs)
