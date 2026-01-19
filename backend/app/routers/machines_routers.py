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
    """Get all active machines."""
    all_ms = db.query(Machine).all()
    # Filter by both is_deleted and is_active for robustness
    machines = [m for m in all_ms if not getattr(m, 'is_deleted', False) and getattr(m, 'is_active', True)]
    
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

@router.post("", response_model=MachineOut, status_code=201)
async def create_machine(machine: MachineCreate, db: Any = Depends(get_db)):
    """Creates a machine using plain dictionary (Sheets-native)."""
    # 1. Mandatory Uniqueness Check
    new_name = machine.machine_name.strip()
    existing = db.query(Machine).all()
    if any(str(getattr(m, 'machine_name', '')).strip().lower() == new_name.lower() and not getattr(m, 'is_deleted', False) for m in existing):
        raise HTTPException(status_code=400, detail=f"Machine with name '{new_name}' already exists")

    # 2. Build Plain Dictionary (Avoids model constructor conflicts)
    m_id = str(uuid.uuid4())
    now = get_current_time_ist().isoformat()
    
    # Extract data from Pydantic model
    payload = machine.dict()
    
    # Build canonical row data
    new_m_data = {
        **payload,
        "id": m_id,
        "machine_id": m_id,
        "created_at": now,
        "updated_at": now,
        "status": payload.get("status", "active"), # Explicitly handle status
        "is_active": True,
        "is_deleted": False
    }
    
    # 3. Insert directly via repository
    # db.add(new_m) would normally work with SheetsDB if we used models,
    # but the user requested avoiding models to stop keyword conflicts.
    # SheetsDB.add accepts instances. Let's use db.repository.insert for raw dict.
    from app.repositories.sheets_repository import sheets_repo
    try:
        inserted = sheets_repo.insert("machines", new_m_data)
        return inserted
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write to Google Sheets: {e}")

@router.put("/{machine_id}", response_model=MachineOut)
async def update_machine(machine_id: str, machine_update: MachineUpdate, db: Any = Depends(get_db)):
    """Updates a machine using plain dict updates."""
    m = db.query(Machine).filter(id=machine_id).first()
    if not m: raise HTTPException(status_code=404, detail="Machine not found")
    
    data = machine_update.dict(exclude_unset=True)
    
    # Check uniqueness if name changes
    if "machine_name" in data:
        new_name = data["machine_name"].strip()
        if new_name.lower() != str(getattr(m, 'machine_name', '')).strip().lower():
            existing = db.query(Machine).all()
            if any(str(getattr(ex, 'machine_name', '')).strip().lower() == new_name.lower() and str(getattr(ex, 'id', '')) != machine_id and not getattr(ex, 'is_deleted', False) for ex in existing):
                raise HTTPException(status_code=400, detail=f"Machine name '{new_name}' taken")

    # Update row data
    from app.repositories.sheets_repository import sheets_repo
    data["updated_at"] = get_current_time_ist().isoformat()
    
    success = sheets_repo.update("machines", machine_id, data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update Google Sheets")
    
    # Return updated object
    return {**m.dict(), **data}

@router.delete("/{machine_id}")
async def delete_machine(machine_id: str, db: Any = Depends(get_db)):
    """Soft delete machine."""
    from app.repositories.sheets_repository import sheets_repo
    success = sheets_repo.update("machines", machine_id, {
        "is_active": False,
        "is_deleted": True,
        "updated_at": get_current_time_ist().isoformat()
    })
    if not success:
         raise HTTPException(status_code=500, detail="Failed to delete from Google Sheets")
    return {"message": "Success"}

