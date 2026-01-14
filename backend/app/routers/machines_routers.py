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
    machines = [m for m in db.query(Machine).all() if not getattr(m, 'is_deleted', False)]
    # Resolve names
    units = db.query(Unit).all()
    cats = db.query(MachineCategory).all()
    
    u_map = {str(u.id): str(u.name) for u in units}
    c_map = {str(c.id): str(c.name) for c in cats}
    
    for m in machines:
        m.unit_name = u_map.get(str(m.unit_id), "Unknown")
        m.category_name = c_map.get(str(m.category_id), "Unknown")
        # Field alias support for id
        m.id = str(m.id)
        
    return machines

@router.post("", response_model=MachineOut)
async def create_machine(machine: MachineCreate, db: Any = Depends(get_db)):
    new_id = str(uuid.uuid4())
    new_m = Machine(
        id=new_id,
        **machine.dict(),
        created_at=datetime.now().isoformat(),
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
    m.updated_at = datetime.now().isoformat()
    db.commit()
    return m

@router.delete("/{machine_id}")
async def delete_machine(machine_id: str, db: Any = Depends(get_db)):
    m = db.query(Machine).filter(id=machine_id).first()
    if not m: raise HTTPException(status_code=404, detail="Machine not found")
    m.is_deleted = True
    m.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Success"}
