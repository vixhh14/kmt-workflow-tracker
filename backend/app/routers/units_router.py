from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.core.database import get_db
from app.models.models_db import Unit as UnitModel

router = APIRouter(prefix="/api/units", tags=["units"])

# Pydantic Schemas - updated for SheetsDB flexibility
class UnitResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class UnitCreate(BaseModel):
    name: str
    description: Optional[str] = None

# Endpoints
@router.get("", response_model=List[UnitResponse])
async def get_units(db: Any = Depends(get_db)):
    """Get all units"""
    all_units = db.query(UnitModel).all()
    # Ensure all have str() IDs for schema
    for u in all_units:
        u.id = str(getattr(u, 'unit_id', getattr(u, 'id', '')))
    return all_units

@router.get("/{unit_id}", response_model=UnitResponse)
async def get_unit(unit_id: str, db: Any = Depends(get_db)):
    """Get unit by ID"""
    unit = db.query(UnitModel).filter(unit_id=unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    unit.id = str(getattr(unit, 'unit_id', getattr(unit, 'id', '')))
    return unit

@router.post("", response_model=UnitResponse)
async def create_unit(unit: UnitCreate, db: Any = Depends(get_db)):
    """Create new unit"""
    all_units = db.query(UnitModel).all()
    # Case-insensitive check
    existing = next((u for u in all_units if str(u.name).strip().lower() == unit.name.strip().lower()), None)
    if existing:
        raise HTTPException(status_code=400, detail="Unit with this name already exists")
    
    # ID generation: use str(max+1) or uuid. I'll stick to max+1 for small masters.
    try:
        max_id = max([int(getattr(u, 'unit_id', 0)) for u in all_units if str(getattr(u, 'unit_id', '')).isdigit()] + [0])
        new_id = str(max_id + 1)
    except:
        import uuid
        new_id = str(uuid.uuid4())
    
    new_unit = UnitModel(
        unit_id=new_id,
        name=unit.name.strip(),
        description=unit.description,
        status="active",
        created_at=datetime.now().isoformat()
    )
    
    db.add(new_unit)
    db.commit()
    
    # Map for response
    new_unit.id = new_id
    
    return new_unit
