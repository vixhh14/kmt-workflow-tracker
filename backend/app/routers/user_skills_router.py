from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import datetime
import uuid
from ..core.database import get_db
from ..models.models_db import UserMachine as UserMachineModel

router = APIRouter(prefix="/api/user-skills", tags=["user-skills"])

class UserMachine(BaseModel):
    id: str
    user_id: str
    machine_id: str
    skill_level: str
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserMachineCreate(BaseModel):
    machine_id: str
    skill_level: str = "intermediate"

class UserMachinesBulk(BaseModel):
    machines: List[UserMachineCreate]

@router.get("/{user_id}/machines", response_model=List[UserMachine])
async def get_user_machines(user_id: str, db: Any = Depends(get_db)):
    """Get all machines a user can operate"""
    all_skills = db.query(UserMachineModel).all()
    machines = [s for s in all_skills if str(s.user_id) == str(user_id)]
    for m in machines:
        m.id = str(m.id)
    return machines

@router.post("/{user_id}/machines")
async def add_user_machines(user_id: str, data: UserMachinesBulk, db: Any = Depends(get_db)):
    """Add multiple machine skills for a user"""
    try:
        all_skills = db.query(UserMachineModel).all()
        for machine in data.machines:
            existing = next((s for s in all_skills if str(s.user_id) == str(user_id) and str(s.machine_id) == str(machine.machine_id)), None)
            
            if existing:
                existing.skill_level = machine.skill_level
            else:
                new_skill = UserMachineModel(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    machine_id=machine.machine_id,
                    skill_level=machine.skill_level,
                    created_at=datetime.now().isoformat()
                )
                db.add(new_skill)
        
        db.commit()
        return {"message": f"Added {len(data.machines)} machine skills for user {user_id}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}/machines/{machine_id}")
async def remove_user_machine(user_id: str, machine_id: str, db: Any = Depends(get_db)):
    """Remove a machine skill from user"""
    all_skills = db.query(UserMachineModel).all()
    skill = next((s for s in all_skills if str(s.user_id) == str(user_id) and str(s.machine_id) == str(machine_id)), None)
    
    if skill:
        db.delete(skill)
        db.commit()
    
    return {"message": "Machine skill removed"}
