"""
Units Router - API endpoints for factory units
Refactored to use SQLAlchemy for better compatibility with Render (Postgres/SQLite)
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.core.database import get_db
from app.models.models_db import Unit as UnitModel

router = APIRouter(prefix="/api/units", tags=["units"])

# Pydantic Schemas
class UnitResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class UnitCreate(BaseModel):
    name: str
    description: Optional[str] = None

# Endpoints
@router.get("", response_model=List[UnitResponse])
async def get_units(db: Session = Depends(get_db)):
    """Get all units"""
    return db.query(UnitModel).all()

@router.get("/{unit_id}", response_model=UnitResponse)
async def get_unit(unit_id: int, db: Session = Depends(get_db)):
    """Get unit by ID"""
    unit = db.query(UnitModel).filter(UnitModel.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit

@router.post("", response_model=UnitResponse)
async def create_unit(unit: UnitCreate, db: Session = Depends(get_db)):
    """Create new unit"""
    existing = db.query(UnitModel).filter(UnitModel.name == unit.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Unit with this name already exists")
    
    new_unit = UnitModel(
        name=unit.name,
        description=unit.description
    )
    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)
    return new_unit
