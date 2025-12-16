from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.machines_model import MachineCreate, MachineUpdate
from app.models.models_db import Machine, Unit, MachineCategory
from app.core.database import get_db
import uuid
from app.core.time_utils import get_current_time_ist

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
    machines = db.query(Machine).filter(Machine.is_deleted == False).all()
    
    # Pre-fetch units and categories for efficient lookup
    units = {u.id: u.name for u in db.query(Unit).all()}
    categories = {c.id: c.name for c in db.query(MachineCategory).all()}
    
    return [
        {
            "id": m.id,
            "name": m.machine_name,
            "status": m.status,
            "hourly_rate": m.hourly_rate,
            "last_maintenance": m.last_maintenance,
            "current_operator": m.current_operator,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            "category_id": m.category_id,
            "unit_id": m.unit_id,
            "category_name": categories.get(m.category_id, None),
            "unit_name": units.get(m.unit_id, None),
        }
        for m in machines
    ]


# ----------------------------------------------------------------------
# CREATE MACHINE
# ----------------------------------------------------------------------
@router.post("/", response_model=dict)
async def create_machine(machine: MachineCreate, db: Session = Depends(get_db)):
    # Use provided location (Machine ID) as the primary key ID if provided, else UUID
    machine_id = machine.location if machine.location else str(uuid.uuid4())
    
    # Validation
    if not machine.unit_id:
        raise HTTPException(status_code=400, detail="Unit ID is required")
    if not machine.category_id:
        raise HTTPException(status_code=400, detail="Category ID is required")

    final_name = f"{machine.machine_name} ({machine.type})" if machine.type else machine.machine_name

    new_machine = Machine(
        id=machine_id,
        machine_name=final_name,
        status=machine.status,
        hourly_rate=0.0, 
        last_maintenance=None,
        current_operator=machine.current_operator,
        unit_id=machine.unit_id,
        category_id=machine.category_id,
        updated_at=get_current_time_ist().replace(tzinfo=None),
        is_deleted=False
    )
    db.add(new_machine)
    db.commit()
    db.refresh(new_machine)
    
    return {
        "id": new_machine.id,
        "name": new_machine.machine_name,
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
    
    # Manually update fields to avoid AttributeError for fields not in DB model (like type, location)
    if machine_update.machine_name is not None:
        db_machine.machine_name = machine_update.machine_name
        
    if machine_update.status is not None:
        db_machine.status = machine_update.status
        
    if machine_update.hourly_rate is not None:
        db_machine.hourly_rate = machine_update.hourly_rate
        
    if machine_update.current_operator is not None:
        db_machine.current_operator = machine_update.current_operator
    
    # Always bump the updated_at timestamp
    db_machine.updated_at = get_current_time_ist().replace(tzinfo=None)
    
    db.commit()
    db.refresh(db_machine)
    
    return {
        "id": db_machine.id,
        "name": db_machine.machine_name,
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
    from sqlalchemy.exc import IntegrityError
    
    db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    try:
        db_machine.is_deleted = True
        # db_machine.status = "archived" # Optional
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete machine: {str(e)}")

    return {"message": "Machine deleted successfully"}


# ----------------------------------------------------------------------
# SEED MACHINES (One-time endpoint to populate database)
# ----------------------------------------------------------------------
@router.post("/seed", response_model=dict)
async def seed_machines(db: Session = Depends(get_db)):
    """
    One-time endpoint to seed the database with machines, units, and categories.
    Call this once after deployment to populate the machine master list.
    """
    
    # Units data
    UNITS = [
        {"id": 1, "name": "Unit 1", "description": "Main production unit"},
        {"id": 2, "name": "Unit 2", "description": "Secondary production unit"},
    ]
    
    # Categories data
    CATEGORIES = [
        {"id": 1, "name": "Material Cutting"},
        {"id": 2, "name": "Welding"},
        {"id": 3, "name": "Lathe"},
        {"id": 4, "name": "CNC"},
        {"id": 5, "name": "Slotting"},
        {"id": 6, "name": "Grinding"},
        {"id": 7, "name": "Drilling"},
        {"id": 8, "name": "Grinder"},
        {"id": 9, "name": "VMC"},
        {"id": 10, "name": "Milling"},
        {"id": 11, "name": "Engraving"},
        {"id": 12, "name": "Honing"},
        {"id": 13, "name": "Buffing"},
        {"id": 14, "name": "Tooth Rounding"},
        {"id": 15, "name": "Lapping"},
        {"id": 16, "name": "Rack Cutting"},
    ]
    
    # Machines data - Unit 2 (11 machines)
    UNIT2_MACHINES = [
        {"machine_name": "Gas Cutting", "category_id": 1},
        {"machine_name": "Tig Welding", "category_id": 2},
        {"machine_name": "CO2 Welding LD", "category_id": 2},
        {"machine_name": "CO2 Welding HD", "category_id": 2},
        {"machine_name": "PSG", "category_id": 3},
        {"machine_name": "Ace Superjobber", "category_id": 4},
        {"machine_name": "Slotting Machine", "category_id": 5},
        {"machine_name": "Surface Grinding", "category_id": 6},
        {"machine_name": "Thakur Drilling", "category_id": 7},
        {"machine_name": "Toolvasor Magnetic Drilling", "category_id": 7},
        {"machine_name": "EIFCO Radial Drilling", "category_id": 7},
    ]
    
    # Machines data - Unit 1 (28 machines)
    UNIT1_MACHINES = [
        {"machine_name": "Hand Grinder", "category_id": 8},
        {"machine_name": "Bench Grinder", "category_id": 8},
        {"machine_name": "Tool and Cutter Grinder", "category_id": 8},
        {"machine_name": "Turnmaster", "category_id": 3},
        {"machine_name": "Leader", "category_id": 3},
        {"machine_name": "Bandsaw cutting Manual", "category_id": 1},
        {"machine_name": "Bandsaw cutting Auto", "category_id": 1},
        {"machine_name": "VMC Pilot", "category_id": 9},
        {"machine_name": "ESTEEM DRO", "category_id": 10},
        {"machine_name": "FW Horizontal", "category_id": 10},
        {"machine_name": "Arno", "category_id": 10},
        {"machine_name": "BFW No 2", "category_id": 10},
        {"machine_name": "Engraving Machine", "category_id": 11},
        {"machine_name": "Delapena Honing Machine", "category_id": 12},
        {"machine_name": "Bench Grinder 2", "category_id": 8},
        {"machine_name": "Buffing Machine", "category_id": 13},
        {"machine_name": "Tooth Rounding Machine", "category_id": 14},
        {"machine_name": "Lapping Machine", "category_id": 15},
        {"machine_name": "Hand Drilling 2", "category_id": 7},
        {"machine_name": "Hand Drilling 1", "category_id": 7},
        {"machine_name": "Hand Grinding 2", "category_id": 8},
        {"machine_name": "Hand Grinding 1", "category_id": 8},
        {"machine_name": "Hitachi Cutting Machine", "category_id": 1},
        {"machine_name": "HMT Rack Cutting", "category_id": 16},
        {"machine_name": "L Rack Cutting", "category_id": 16},
        {"machine_name": "Reinecker", "category_id": 3},
        {"machine_name": "Zimberman", "category_id": 4},
        {"machine_name": "EIFCO Stationary Drilling", "category_id": 7},
    ]
    
    added_units = 0
    added_categories = 0
    added_machines = 0
    
    try:
        # Insert Units
        for unit_data in UNITS:
            existing = db.query(Unit).filter(Unit.id == unit_data["id"]).first()
            if not existing:
                unit = Unit(id=unit_data["id"], name=unit_data["name"], description=unit_data.get("description"), created_at=get_current_time_ist().replace(tzinfo=None))
                db.add(unit)
                added_units += 1
        
        # Insert Categories
        for cat_data in CATEGORIES:
            existing = db.query(MachineCategory).filter(MachineCategory.id == cat_data["id"]).first()
            if not existing:
                category = MachineCategory(id=cat_data["id"], name=cat_data["name"], created_at=get_current_time_ist().replace(tzinfo=None))
                db.add(category)
                added_categories += 1
        
        db.commit()
        
        # Insert Unit 2 Machines
        for machine_data in UNIT2_MACHINES:
            existing = db.query(Machine).filter(Machine.machine_name == machine_data["machine_name"]).first()
            if not existing:
                machine = Machine(
                    id=str(uuid.uuid4()),
                    machine_name=machine_data["machine_name"],
                    status="active",
                    hourly_rate=0.0,
                    category_id=machine_data["category_id"],
                    unit_id=2,
                    updated_at=get_current_time_ist().replace(tzinfo=None),
                    is_deleted=False
                )
                db.add(machine)
                added_machines += 1
        
        # Insert Unit 1 Machines
        for machine_data in UNIT1_MACHINES:
            existing = db.query(Machine).filter(Machine.machine_name == machine_data["machine_name"]).first()
            if not existing:
                machine = Machine(
                    id=str(uuid.uuid4()),
                    machine_name=machine_data["machine_name"],
                    status="active",
                    hourly_rate=0.0,
                    category_id=machine_data["category_id"],
                    unit_id=1,
                    updated_at=get_current_time_ist().replace(tzinfo=None),
                    is_deleted=False
                )
                db.add(machine)
                added_machines += 1
        
        db.commit()
        
        # Get totals
        total_units = db.query(Unit).count()
        total_categories = db.query(MachineCategory).count()
        total_machines = db.query(Machine).count()
        
        return {
            "message": "Seed completed successfully!",
            "added": {
                "units": added_units,
                "categories": added_categories,
                "machines": added_machines
            },
            "totals": {
                "units": total_units,
                "categories": total_categories,
                "machines": total_machines
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Seed failed: {str(e)}")

