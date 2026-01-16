
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
    __tablename__ = "Users"
    def __init__(self, **kwargs):
        # Sync id and user_id
        u_id = kwargs.get("id") or kwargs.get("user_id")
        if not u_id: u_id = str(uuid.uuid4())
        kwargs["id"] = u_id
        kwargs["user_id"] = u_id
        super().__init__(**kwargs)

class Project(SheetsModel):
    __tablename__ = "Projects"
    def __init__(self, **kwargs):
        # Sync id and project_id
        p_id = kwargs.get("id") or kwargs.get("project_id")
        if not p_id: p_id = str(uuid.uuid4())
        kwargs["id"] = p_id
        kwargs["project_id"] = p_id
        super().__init__(**kwargs)

class Task(SheetsModel):
    __tablename__ = "Tasks"
    def __init__(self, **kwargs):
        # Handle legacy task_id
        if "id" not in kwargs and "task_id" in kwargs:
            kwargs["id"] = kwargs.pop("task_id")
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)

class Attendance(SheetsModel):
    __tablename__ = "Attendance"
    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = f"att_{int(datetime.now().timestamp())}"
        super().__init__(**kwargs)

class FabricationTask(SheetsModel):
    __tablename__ = "FabricationTasks"
    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)

class FilingTask(SheetsModel):
    __tablename__ = "FilingTasks"
    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)

class TaskTimeLog(SheetsModel):
    __tablename__ = "TaskTimeLog"
    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)

class TaskHold(SheetsModel):
    __tablename__ = "TaskHold"
    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)

class MachineRuntimeLog(SheetsModel):
    __tablename__ = "MachineRuntimeLog"
    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)

class UserWorkLog(SheetsModel):
    __tablename__ = "UserWorkLog"
    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)

class Machine(SheetsModel):
    __tablename__ = "Machines"
    def __init__(self, **kwargs):
        # Sync id and machine_id
        m_id = kwargs.get("id") or kwargs.get("machine_id")
        if not m_id: m_id = str(uuid.uuid4())
        kwargs["id"] = m_id
        kwargs["machine_id"] = m_id
        super().__init__(**kwargs)

class Unit(SheetsModel):
    __tablename__ = "Units"

class MachineCategory(SheetsModel):
    __tablename__ = "MachineCategories"

class UserMachine(SheetsModel):
    __tablename__ = "UserMachine"

class Subtask(SheetsModel):
    __tablename__ = "Subtasks"

class OutsourceItem(SheetsModel):
    __tablename__ = "OutsourceItems"

class RescheduleRequest(SheetsModel):
    __tablename__ = "RescheduleRequests"
    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)

class PlanningTask(SheetsModel):
    __tablename__ = "PlanningTasks"
    def __init__(self, **kwargs):
        if "id" not in kwargs or not kwargs["id"]:
            kwargs["id"] = str(uuid.uuid4())
        super().__init__(**kwargs)
