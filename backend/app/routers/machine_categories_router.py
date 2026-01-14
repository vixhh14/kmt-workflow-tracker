from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import datetime
from ..core.database import get_db
from ..models.models_db import MachineCategory as MachineCategoryModel

router = APIRouter(prefix="/api/machine-categories", tags=["machine-categories"])

class MachineCategory(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[MachineCategory])
async def get_machine_categories(db: Any = Depends(get_db)):
    """Get all machine categories"""
    categories = db.query(MachineCategoryModel).all()
    # Sort in memory by name
    categories.sort(key=lambda x: str(getattr(x, 'name', '')).lower())
    
    # Ensure IDs are strings
    for c in categories:
        c.id = str(c.id)
        
    return categories
