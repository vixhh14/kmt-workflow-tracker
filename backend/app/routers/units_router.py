"""
Units Router - API endpoints for factory units
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
from ..core.database import get_db_connection

router = APIRouter(prefix="/api/units", tags=["units"])

class Unit(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

class UnitCreate(BaseModel):
    name: str
    description: Optional[str] = None

@router.get("", response_model=List[Unit])
async def get_units():
    """Get all units"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, description, created_at
        FROM units
        ORDER BY id
    """)
    
    units = []
    for row in cursor.fetchall():
        units.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3]
        })
    
    conn.close()
    return units

@router.get("/{unit_id}", response_model=Unit)
async def get_unit(unit_id: int):
    """Get unit by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, description, created_at
        FROM units
        WHERE id = ?
    """, (unit_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "created_at": row[3]
    }

@router.post("", response_model=Unit)
async def create_unit(unit: UnitCreate):
    """Create new unit (admin only)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO units (name, description)
            VALUES (?, ?)
        """, (unit.name, unit.description))
        
        unit_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("SELECT id, name, description, created_at FROM units WHERE id = ?", (unit_id,))
        row = cursor.fetchone()
        
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3]
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Unit with this name already exists")
    finally:
        conn.close()
