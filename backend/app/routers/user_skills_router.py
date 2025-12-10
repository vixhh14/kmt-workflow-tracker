"""
User Skills Router - API endpoints for user-machine skill mapping
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.models_db import UserMachine as UserMachineModel

router = APIRouter(prefix="/api/user-skills", tags=["user-skills"])

class UserMachine(BaseModel):
    id: int
    user_id: str
    machine_id: str
    skill_level: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class UserMachineCreate(BaseModel):
    machine_id: str
    skill_level: str = "intermediate"

class UserMachinesBulk(BaseModel):
    machines: List[UserMachineCreate]

@router.get("/{user_id}/machines", response_model=List[UserMachine])
async def get_user_machines(user_id: str, db: Session = Depends(get_db)):
    """Get all machines a user can operate"""
    machines = db.query(UserMachineModel).filter(UserMachineModel.user_id == user_id).all()
    return machines

@router.post("/{user_id}/machines")
async def add_user_machines(user_id: str, data: UserMachinesBulk, db: Session = Depends(get_db)):
    """Add multiple machine skills for a user"""
    try:
        for machine in data.machines:
            # Check if exists
            existing = db.query(UserMachineModel).filter(
                UserMachineModel.user_id == user_id,
                UserMachineModel.machine_id == machine.machine_id
            ).first()
            
            if existing:
                existing.skill_level = machine.skill_level
            else:
                new_skill = UserMachineModel(
                    user_id=user_id,
                    machine_id=machine.machine_id,
                    skill_level=machine.skill_level
                )
                db.add(new_skill)
        
        db.commit()
        return {"message": f"Added {len(data.machines)} machine skills for user {user_id}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}/machines/{machine_id}")
async def remove_user_machine(user_id: str, machine_id: str, db: Session = Depends(get_db)):
    """Remove a machine skill from user"""
    # Note: machine_id in path is str, but in model it is String.
    # The original code had machine_id: int in the function signature but the SQL used it as is.
    # Machines table id is String. UserMachine machine_id is String.
    
    skill = db.query(UserMachineModel).filter(
        UserMachineModel.user_id == user_id,
        UserMachineModel.machine_id == machine_id
    ).first()
    
    if skill:
        db.delete(skill)
        db.commit()
    
    return {"message": "Machine skill removed"}
