"""
User Skills Router - API endpoints for user-machine skill mapping
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..core.database import get_db_connection

router = APIRouter(prefix="/api/user-skills", tags=["user-skills"])

class UserMachine(BaseModel):
    id: int
    user_id: str
    machine_id: str
    skill_level: str
    created_at: Optional[datetime] = None

class UserMachineCreate(BaseModel):
    machine_id: str
    skill_level: str = "intermediate"

class UserMachinesBulk(BaseModel):
    machines: List[UserMachineCreate]

@router.get("/{user_id}/machines", response_model=List[UserMachine])
async def get_user_machines(user_id: str):
    """Get all machines a user can operate"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_id, machine_id, skill_level, created_at
        FROM user_machines
        WHERE user_id = ?
    """, (user_id,))
    
    machines = []
    for row in cursor.fetchall():
        machines.append({
            "id": row[0],
            "user_id": row[1],
            "machine_id": row[2],
            "skill_level": row[3],
            "created_at": row[4]
        })
    
    conn.close()
    return machines

@router.post("/{user_id}/machines")
async def add_user_machines(user_id: str, data: UserMachinesBulk):
    """Add multiple machine skills for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for machine in data.machines:
            cursor.execute("""
                INSERT OR REPLACE INTO user_machines (user_id, machine_id, skill_level)
                VALUES (?, ?, ?)
            """, (user_id, machine.machine_id, machine.skill_level))
        
        conn.commit()
        return {"message": f"Added {len(data.machines)} machine skills for user {user_id}"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.delete("/{user_id}/machines/{machine_id}")
async def remove_user_machine(user_id: str, machine_id: int):
    """Remove a machine skill from user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM user_machines
        WHERE user_id = ? AND machine_id = ?
    """, (user_id, machine_id))
    
    conn.commit()
    conn.close()
    
    return {"message": "Machine skill removed"}
