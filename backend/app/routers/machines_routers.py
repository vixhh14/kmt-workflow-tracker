from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any, Optional
from datetime import datetime
from app.schemas.machine_schema import MachineCreate, MachineUpdate, MachineOut
from app.models.models_db import Machine, Unit, MachineCategory
from app.core.database import get_db
import uuid
from app.core.time_utils import get_current_time_ist

router = APIRouter(prefix="/machines", tags=["Machines"])

def normalize_machine_data(data: dict) -> dict:
    """Canonical normalization as per mandatory user rules."""
    # 1. Normalize Unit
    u = str(data.get("unit", "")).strip().lower()
    if u in ["1", "unit1", "unit 1"]:
        data["unit"] = "Unit 1"
    elif u in ["2", "unit2", "unit 2"]:
        data["unit"] = "Unit 2"
    
    # 2. Normalize Category
    cat = str(data.get("category", "")).strip()
    data["category"] = cat.title()
    
    # 3. Status
    status = str(data.get("status", "active")).strip().lower()
    data["status"] = "active" if status in ["active", "1", "true"] else "inactive"
    
    # 4. is_deleted must be boolean
    is_del = data.get("is_deleted", False)
    if isinstance(is_del, str):
        data["is_deleted"] = is_del.lower() in ["true", "1", "yes"]
    else:
        data["is_deleted"] = bool(is_del)
        
    return data

@router.get("", response_model=List[MachineOut])
async def read_machines(db: Any = Depends(get_db)):
    """Get all active machines with post-fetch normalization and safety guard."""
    all_ms = db.query(Machine).all()
    
    results = []
    for m in all_ms:
        try:
            m_dict = m.dict()
            # 1. Post-Fetch Normalization
            norm_data = normalize_machine_data(m_dict)
            
            # 2. Skip if deleted
            if norm_data.get("is_deleted", False):
                continue

            # 3. Defensive Check: Ensure required ID fields are populated
            if not norm_data.get("machine_id"):
                print(f"⚠️ [Machines] Skipping row with missing ID: {norm_data.get('machine_name', 'Unnamed')}")
                continue

            # 4. Final Validation against Pydantic schema
            valid_m = MachineOut(**norm_data)
            results.append(valid_m)
        except Exception as e:
            msg = getattr(m, 'machine_name', 'Unknown')
            print(f"❌ [Machines] Invalid row '{msg}' skipped: {e}")
            
    return results

@router.post("", response_model=MachineOut, status_code=201)
async def create_machine(machine: MachineCreate, db: Any = Depends(get_db)):
    """Creates a machine using STRICT APPEND logic."""
    from app.repositories.sheets_repository import sheets_repo
    
    # 1. Normalize Input (handling legacy unit_id/category_id)
    payload = machine.dict(exclude_none=True)
    if "unit_id" in payload and not payload.get("unit"):
        payload["unit"] = str(payload["unit_id"])
    if "category_id" in payload and not payload.get("category"):
        payload["category"] = str(payload["category_id"])
        
    payload = normalize_machine_data(payload)
    
    # 2. Uniqueness Check (Case Insensitive)
    new_name = payload.get("machine_name", "").strip().lower()
    all_current = sheets_repo.get_all("machines", include_deleted=True)
    if any(str(m.get('machine_name', '')).strip().lower() == new_name and not bool(m.get('is_deleted')) for m in all_current):
         raise HTTPException(status_code=400, detail=f"Machine '{payload['machine_name']}' already exists")

    # 3. Build canonical row
    m_id = str(uuid.uuid4())
    now = get_current_time_ist().isoformat()
    
    new_m_data = {
        "machine_id": m_id,
        "machine_name": payload.get("machine_name"),
        "category": payload.get("category"),
        "unit": payload.get("unit"),
        "status": payload.get("status", "active"),
        "created_at": now,
        "updated_at": now,
        "is_deleted": False
    }
    
    try:
        # Mandatory: Use repository insert (which uses append_row)
        inserted = sheets_repo.insert("machines", new_m_data)
        return inserted
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to append machine: {e}")

@router.put("/{machine_id}", response_model=MachineOut)
async def update_machine(machine_id: str, machine_update: MachineUpdate, db: Any = Depends(get_db)):
    """Updates a machine using machine_id only."""
    from app.repositories.sheets_repository import sheets_repo
    
    m = db.query(Machine).filter(machine_id=machine_id).first()
    if not m: raise HTTPException(status_code=404, detail="Machine not found")
    
    data = machine_update.dict(exclude_unset=True)
    if "unit" in data or "category" in data or "status" in data:
        # Re-normalize if critical fields change
        temp_data = {**m.dict(), **data}
        data = normalize_machine_data(temp_data)
        # We only want the updated fields for the repo.update call
        data = {k: data[k] for k in machine_update.dict(exclude_unset=True).keys()}

    data["updated_at"] = get_current_time_ist().isoformat()
    
    success = sheets_repo.update("machines", machine_id, data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update machine")
    
    return {**m.dict(), **data}

@router.delete("/{machine_id}")
async def delete_machine(machine_id: str, db: Any = Depends(get_db)):
    from app.repositories.sheets_repository import sheets_repo
    success = sheets_repo.update("machines", machine_id, {
        "is_deleted": True,
        "status": "inactive",
        "updated_at": get_current_time_ist().isoformat()
    })
    return {"message": "Success"}

