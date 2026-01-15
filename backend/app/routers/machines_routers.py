from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any, Optional
from datetime import datetime
from app.schemas.machine_schema import MachineCreate, MachineUpdate, MachineOut
from app.models.models_db import Machine, Unit, MachineCategory
from app.core.database import get_db
import uuid
from app.core.time_utils import get_current_time_ist

router = APIRouter(prefix="/machines", tags=["Machines"])

@router.get("", response_model=List[MachineOut])
async def read_machines(db: Any = Depends(get_db)):
    """Get all machines from cache."""
    machines = db.query(Machine).filter(is_deleted=False).all()
    
    # Resolve names using cached data
    units = db.query(Unit).all()
    cats = db.query(MachineCategory).all()
    
    u_map = {str(getattr(u, 'id', '')): str(getattr(u, 'name', '')) for u in units}
    c_map = {str(getattr(c, 'id', '')): str(getattr(c, 'name', '')) for c in cats}
    
    results = []
    for m in machines:
        data = m.dict()
        data['unit_name'] = u_map.get(str(data.get('unit_id')), "Unknown")
        data['category_name'] = c_map.get(str(data.get('category_id')), "Unknown")
        results.append(data)
        
    return results

@router.post("", response_model=MachineOut)
async def create_machine(machine: MachineCreate, db: Any = Depends(get_db)):
    new_m = Machine(
        **machine.dict(),
        created_at=get_current_time_ist().isoformat(),
        status="active",
        is_deleted=False
    )
    db.add(new_m)
    db.commit()
    return new_m

@router.put("/{machine_id}", response_model=MachineOut)
async def update_machine(machine_id: str, machine_update: MachineUpdate, db: Any = Depends(get_db)):
    m = db.query(Machine).filter(id=machine_id).first()
    if not m: raise HTTPException(status_code=404, detail="Machine not found")
    
    data = machine_update.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(m, k, v)
    m.updated_at = get_current_time_ist().isoformat()
    db.commit()
    return m

@router.delete("/{machine_id}")
async def delete_machine(machine_id: str, db: Any = Depends(get_db)):
    m = db.query(Machine).filter(id=machine_id).first()
    if not m: raise HTTPException(status_code=404, detail="Machine not found")
    m.is_deleted = True
    m.updated_at = get_current_time_ist().isoformat()
    db.commit()
    return {"message": "Success"}
