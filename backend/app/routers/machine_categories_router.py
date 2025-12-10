"""
Machine Categories Router - API endpoints for machine categories
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.models_db import MachineCategory as MachineCategoryModel

router = APIRouter(prefix="/api/machine-categories", tags=["machine-categories"])

class MachineCategory(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

@router.get("", response_model=List[MachineCategory])
async def get_machine_categories(db: Session = Depends(get_db)):
    """Get all machine categories"""
    categories = db.query(MachineCategoryModel).order_by(MachineCategoryModel.name).all()
    return categories
