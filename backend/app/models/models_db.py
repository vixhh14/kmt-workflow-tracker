from sqlalchemy import Column, String, Integer, BigInteger, Float, ForeignKey, DateTime, Boolean, Date, UniqueConstraint, or_
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.time_utils import get_current_time_ist

# NOTE: All DateTime columns are now timezone-aware (TIMESTAMPTZ in Postgres)
# Default values use get_current_time_ist to ensure all timestamps are generated in IST context.

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)
    full_name = Column(String)
    machine_types = Column(String, nullable=True)  # Comma-separated machine types (e.g., "CNC,Lathe,Mill")
    
    # New fields for onboarding
    date_of_birth = Column(String, nullable=True)
    address = Column(String, nullable=True)
    contact_number = Column(String, nullable=True)
    unit_id = Column(String, nullable=True)
    approval_status = Column(String, default='pending') # pending, approved, rejected
    
    # Security Question for Password Reset
    security_question = Column(String, nullable=True)
    security_answer = Column(String, nullable=True)
    
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_ist, onupdate=get_current_time_ist)

class Unit(Base):
    __tablename__ = "units"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

class MachineCategory(Base):
    __tablename__ = "machine_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

class UserApproval(Base):
    __tablename__ = "user_approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    status = Column(String, default="pending")
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

class UserMachine(Base):
    __tablename__ = "user_machines"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    machine_id = Column(String, ForeignKey("machines.id"))
    skill_level = Column(String, default="intermediate")
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

class Machine(Base):
    __tablename__ = "machines"

    id = Column(String, primary_key=True, index=True)
    machine_name = Column(String, index=True) # Renamed from name
    status = Column(String)  # active, maintenance, offline
    hourly_rate = Column(Float)
    last_maintenance = Column(String, nullable=True)
    current_operator = Column(String, nullable=True)  # user_id of current operator
    category_id = Column(Integer, ForeignKey("machine_categories.id"), nullable=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_ist, onupdate=get_current_time_ist)

class Project(Base):
    __tablename__ = "projects"

    # Changed from String UUID to Integer Autoincrement
    project_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    project_name = Column(String, index=True)
    work_order_number = Column(String, nullable=True)
    client_name = Column(String, nullable=True)
    project_code = Column(String, unique=True, index=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

import uuid

class Task(Base):
    __tablename__ = "tasks"

    # Tasks use UUID (Safe for existing data)
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, index=True)
    project = Column(String, nullable=True)  # Legacy string field (optional)
    description = Column(String, nullable=True)
    part_item = Column(String, nullable=True)
    nos_unit = Column(String, nullable=True)
    status = Column(String)
    priority = Column(String)
    assigned_to = Column(String, nullable=True)
    machine_id = Column(String, ForeignKey("machines.id"), nullable=True)
    assigned_by = Column(String, nullable=True)
    due_date = Column(String, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)
    
    # Time tracking fields
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_duration_seconds = Column(Integer, default=0)
    hold_reason = Column(String, nullable=True)
    denial_reason = Column(String, nullable=True)
    
    # New accurate timing fields
    actual_start_time = Column(DateTime(timezone=True), nullable=True)
    actual_end_time = Column(DateTime(timezone=True), nullable=True)
    total_held_seconds = Column(BigInteger, default=0)
    expected_completion_time = Column(Integer, nullable=True) # Duration in minutes
    due_datetime = Column(DateTime(timezone=False), nullable=True) # Precisely selected date + time
    work_order_number = Column(String, nullable=True) # Work Order Number for Normal Tasks

    # Relationships
    machine = relationship("Machine")
    project_obj = relationship("Project")

class TaskHold(Base):
    __tablename__ = "task_holds"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True) # UUID FK
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    hold_reason = Column(String, nullable=True)
    hold_started_at = Column(DateTime(timezone=True), default=get_current_time_ist)
    hold_ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

class RescheduleRequest(Base):
    __tablename__ = "reschedule_requests"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True) # UUID FK
    requested_by = Column(String, ForeignKey("users.user_id"))
    requested_for_date = Column(DateTime(timezone=True))
    reason = Column(String, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

class TaskTimeLog(Base):
    __tablename__ = "task_time_logs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), index=True) # UUID FK
    action = Column(String)
    timestamp = Column(DateTime(timezone=True), default=get_current_time_ist)
    reason = Column(String, nullable=True)
    
    # Relationship
    task = relationship("Task")

class PlanningTask(Base):
    __tablename__ = "planning_tasks"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), index=True) # UUID FK
    project_name = Column(String)
    task_sequence = Column(Integer)
    assigned_supervisor = Column(String, nullable=True)
    status = Column(String)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_ist, onupdate=get_current_time_ist)
    
    # Relationship
    task = relationship("Task")

class OutsourceItem(Base):
    __tablename__ = "outsource_items"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)  # UUID FK
    title = Column(String, index=True)
    vendor = Column(String)
    dc_generated = Column(Boolean, default=False)
    transport_status = Column(String, default="pending")
    follow_up_time = Column(DateTime(timezone=True), nullable=True)
    pickup_status = Column(String, default="pending")
    status = Column(String)
    cost = Column(Float)
    expected_date = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_ist, onupdate=get_current_time_ist)
    
    # Relationship
    task = relationship("Task")

class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='idx_attendance_user_date'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    date = Column(Date, nullable=False)
    check_in = Column(DateTime(timezone=True), nullable=True)
    check_out = Column(DateTime(timezone=True), nullable=True)
    login_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="Present")
    ip_address = Column(String, nullable=True)
    
    # Relationship
    user = relationship("User")

class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), index=True) # UUID FK
    title = Column(String)
    status = Column(String, default="pending")
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_ist, onupdate=get_current_time_ist)

    # Relationship
    task = relationship("Task")

class MachineRuntimeLog(Base):
    __tablename__ = "machine_runtime_logs"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, ForeignKey("machines.id"), index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True) # UUID FK
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0)
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

    # Relationships
    machine = relationship("Machine")
    task = relationship("Task")

class UserWorkLog(Base):
    __tablename__ = "user_work_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True) # UUID FK
    machine_id = Column(String, ForeignKey("machines.id"), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0)
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

    # Relationships
    user = relationship("User")
    task = relationship("Task")
    machine = relationship("Machine")

class FilingTask(Base):
    __tablename__ = "filing_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=True)
    part_item = Column(String, nullable=True)  # Project / Item
    quantity = Column(Integer, default=1)
    due_date = Column(Date, nullable=True)
    priority = Column(String, default="medium")
    assigned_to = Column(String, ForeignKey("users.user_id"), nullable=True)
    completed_quantity = Column(Integer, default=0)
    remarks = Column(String, nullable=True)
    status = Column(String, default="Pending") # Pending, In Progress, On Hold, Completed
    machine_id = Column(String, ForeignKey("machines.id"), nullable=True)
    work_order_number = Column(String, nullable=True)
    assigned_by = Column(String, ForeignKey("users.user_id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_ist, onupdate=get_current_time_ist)

    # Relationships
    project = relationship("Project")
    machine = relationship("Machine")
    assignee = relationship("User", foreign_keys=[assigned_to])
    assigner = relationship("User", foreign_keys=[assigned_by])

class FabricationTask(Base):
    __tablename__ = "fabrication_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=True)
    part_item = Column(String, nullable=True)  # Project / Item
    quantity = Column(Integer, default=1)
    due_date = Column(Date, nullable=True)
    priority = Column(String, default="medium")
    assigned_to = Column(String, ForeignKey("users.user_id"), nullable=True)
    completed_quantity = Column(Integer, default=0)
    remarks = Column(String, nullable=True)
    status = Column(String, default="Pending") # Pending, In Progress, On Hold, Completed
    machine_id = Column(String, ForeignKey("machines.id"), nullable=True)
    work_order_number = Column(String, nullable=True)
    assigned_by = Column(String, ForeignKey("users.user_id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_ist, onupdate=get_current_time_ist)

    # Relationships
    project = relationship("Project")
    machine = relationship("Machine")
    assignee = relationship("User", foreign_keys=[assigned_to])
    assigner = relationship("User", foreign_keys=[assigned_by])
