from sqlalchemy import Column, String, Integer, BigInteger, Float, ForeignKey, DateTime, Boolean, Date, UniqueConstraint
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
    name = Column(String, index=True)
    status = Column(String)  # active, maintenance, offline
    hourly_rate = Column(Float)
    last_maintenance = Column(String, nullable=True)
    current_operator = Column(String, nullable=True)  # user_id of current operator
    category_id = Column(Integer, ForeignKey("machine_categories.id"), nullable=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_ist, onupdate=get_current_time_ist)

class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String, primary_key=True, index=True)
    project_name = Column(String, index=True)
    work_order_number = Column(String, nullable=True)
    client_name = Column(String, nullable=True)
    project_code = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    project = Column(String, nullable=True)  # Legacy string field
    description = Column(String, nullable=True)
    part_item = Column(String, nullable=True)  # Part or item name
    nos_unit = Column(String, nullable=True)  # Number of units (e.g., "10 pcs")
    status = Column(String)  # pending, in_progress, on_hold, completed, denied
    priority = Column(String)  # low, medium, high
    assigned_to = Column(String, nullable=True)  # operator user_id
    machine_id = Column(String, ForeignKey("machines.id"), nullable=True)
    assigned_by = Column(String, nullable=True)  # user_id who assigned the task
    due_date = Column(String, nullable=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=True) # New FK
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
    expected_completion_time = Column(String, nullable=True)  # Format: "HH:MM" or ISO datetime

    # Relationships
    machine = relationship("Machine")
    project_obj = relationship("Project")

class TaskHold(Base):
    __tablename__ = "task_holds"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    hold_reason = Column(String, nullable=True)
    hold_started_at = Column(DateTime(timezone=True), default=get_current_time_ist)
    hold_ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

class RescheduleRequest(Base):
    __tablename__ = "reschedule_requests"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    requested_by = Column(String, ForeignKey("users.user_id"))
    requested_for_date = Column(DateTime(timezone=True))
    reason = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)

class TaskTimeLog(Base):
    __tablename__ = "task_time_logs"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    action = Column(String)  # start, hold, resume, complete, deny
    timestamp = Column(DateTime(timezone=True), default=get_current_time_ist)
    reason = Column(String, nullable=True)
    
    # Relationship
    task = relationship("Task")

class PlanningTask(Base):
    __tablename__ = "planning_tasks"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    project_name = Column(String)
    task_sequence = Column(Integer)  # Order in project (1, 2, 3...)
    assigned_supervisor = Column(String, nullable=True)  # supervisor user_id
    status = Column(String)  # planning, approved, in_progress, completed
    updated_at = Column(DateTime(timezone=True), default=get_current_time_ist, onupdate=get_current_time_ist)
    
    # Relationship
    task = relationship("Task")

class OutsourceItem(Base):
    __tablename__ = "outsource_items"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)  # Related task
    title = Column(String, index=True)
    vendor = Column(String)
    dc_generated = Column(Boolean, default=False)  # Delivery challan generated
    transport_status = Column(String, default="pending")  # pending, in_transit, delivered
    follow_up_time = Column(DateTime(timezone=True), nullable=True)  # Next follow-up date/time
    pickup_status = Column(String, default="pending")  # pending, scheduled, picked_up
    status = Column(String)  # pending, received
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
    date = Column(Date, nullable=False)  # Date of attendance (DATE type, not DATETIME)
    check_in = Column(DateTime(timezone=True), nullable=True)  # First login time of the day
    check_out = Column(DateTime(timezone=True), nullable=True)  # Logout time (only on explicit logout)
    login_time = Column(DateTime(timezone=True), nullable=True)  # Latest login time of the day
    status = Column(String, default="Present")  # Present, Absent, Leave
    ip_address = Column(String, nullable=True)
    
    # Relationship
    user = relationship("User")

class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    title = Column(String)
    status = Column(String, default="pending")  # pending, completed
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_time_ist)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_ist, onupdate=get_current_time_ist)

    # Relationship
    task = relationship("Task")
