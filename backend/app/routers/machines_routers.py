from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.machines_model import MachineCreate, MachineUpdate
from app.models.models_db import Machine
from app.core.database import get_db
import uuid

router = APIRouter(
    prefix="/machines",
    tags=["machines"],
    responses={404: {"description": "Not found"}},
)

# ----------------------------------------------------------------------
# GET ALL MACHINES
# ----------------------------------------------------------------------
@router.get("/", response_model=List[dict])
async def read_machines(db: Session = Depends(get_db)):
    machines = db.query(Machine).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "status": m.status,
            "hourly_rate": m.hourly_rate,
            "last_maintenance": m.last_maintenance,
            "current_operator": m.current_operator,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            "category_id": m.category_id,
            "unit_id": m.unit_id,
        }
        for m in machines
    ]

# ----------------------------------------------------------------------
# CREATE MACHINE
# ----------------------------------------------------------------------
@router.post("/", response_model=dict)
async def create_machine(machine: MachineCreate, db: Session = Depends(get_db)):
    new_machine = Machine(
        id=str(uuid.uuid4()),
        name=machine.name,
        status=machine.status,
        hourly_rate=machine.hourly_rate,
        last_maintenance=machine.last_maintenance,
        current_operator=machine.current_operator,
        updated_at=datetime.utcnow(),
    )
    db.add(new_machine)
    db.commit()
    db.refresh(new_machine)
    
    return {
        "id": new_machine.id,
        "name": new_machine.name,
        "status": new_machine.status,
        "hourly_rate": new_machine.hourly_rate,
        "last_maintenance": new_machine.last_maintenance,
        "current_operator": new_machine.current_operator,
        "updated_at": new_machine.updated_at.isoformat(),
    }

# ----------------------------------------------------------------------
# UPDATE MACHINE
# ----------------------------------------------------------------------
@router.put("/{machine_id}", response_model=dict)
async def update_machine(machine_id: str, machine_update: MachineUpdate, db: Session = Depends(get_db)):
    db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    update_data = machine_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_machine, key, value)
    
    # Always bump the updated_at timestamp
    db_machine.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_machine)
    
    return {
        "id": db_machine.id,
        "name": db_machine.name,
        "status": db_machine.status,
        "hourly_rate": db_machine.hourly_rate,
        "last_maintenance": db_machine.last_maintenance,
        "current_operator": db_machine.current_operator,
        "updated_at": db_machine.updated_at.isoformat(),
    }

# ----------------------------------------------------------------------
# DELETE MACHINE
# ----------------------------------------------------------------------
@router.delete("/{machine_id}")
async def delete_machine(machine_id: str, db: Session = Depends(get_db)):
    db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    db.delete(db_machine)
    db.commit()
    return {"message": "Machine deleted successfully"}
