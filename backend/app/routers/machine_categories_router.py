"""
Machine Categories Router - API endpoints for machine categories
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..core.database import get_db_connection

router = APIRouter(prefix="/api/machine-categories", tags=["machine-categories"])

class MachineCategory(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

@router.get("", response_model=List[MachineCategory])
async def get_machine_categories():
    """Get all machine categories"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, description, created_at
        FROM machine_categories
        ORDER BY name
    """)
    
    categories = []
    for row in cursor.fetchall():
        categories.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3]
        })
    
    conn.close()
    return categories
