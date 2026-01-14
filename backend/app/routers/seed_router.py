from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.database import get_db
from app.models.models_db import Machine, MachineCategory, User
from app.core.dependencies import get_current_user
from app.core.auth_utils import hash_password
import uuid
import secrets
import string
import os
from datetime import datetime

router = APIRouter(prefix="/seed", tags=["seed"])

MIGRATION_SECRET = os.getenv("MIGRATION_SECRET", "change-this-in-production")

UNIT_1_MACHINES = [
    ("Hand Grinder", "Grinder"), ("Bench Grinder", "Grinder"), ("Tool and Cutter Grinder", "Grinder"),
    ("Turnmaster", "Lathe"), ("Leader", "Lathe"), ("Bandsaw Cutting Manual", "Material Cutting"),
    ("Bandsaw Cutting Auto", "Material Cutting"), ("VMC Pilot", "VMC"), ("ESTEEM DRO", "Milling"),
    ("FW Horizontal", "Milling"), ("Arno", "Milling"), ("BFW No 2", "Milling"),
    ("Engraving Machine", "Engraving"), ("Delapena Honing Machine", "Honing"), ("Buffing Machine", "Buffing"),
    ("Tooth Rounding Machine", "Tooth Rounding"), ("Lapping Machine", "Lapping"), ("Hand Drilling 1", "Drilling"),
    ("Hand Drilling 2", "Drilling"), ("Hand Grinding 1", "Grinder"), ("Hand Grinding 2", "Grinder"),
    ("Hitachi Cutting Machine", "Material Cutting"), ("HMT Rack Cutting", "Rack Cutting"), ("L Rack Cutting", "Rack Cutting"),
    ("Reinecker", "Lathe"), ("Zimberman", "CNC"), ("EIFCO Stationary Drilling", "Drilling")
]

UNIT_2_MACHINES = [
    ("Gas Cutting", "Material Cutting"), ("Tig Welding", "Welding"), ("CO2 Welding LD", "Welding"),
    ("CO2 Welding HD", "Welding"), ("PSG", "Lathe"), ("Ace Superjobber", "CNC"),
    ("Slotting Machine", "Slotting"), ("Surface Grinding", "Grinding"), ("Thakur Drilling", "Drilling"),
    ("Toolvasor Magnetic Drilling", "Drilling"), ("EIFCO Radial Drilling", "Drilling")
]

def generate_secure_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def get_or_create_category(db: any, category_name: str) -> any:
    all_cats = db.query(MachineCategory).all()
    cat = next((c for c in all_cats if str(getattr(c, 'name', '')).lower() == category_name.lower()), None)
    if not cat:
        try:
            max_id = max([int(c.id) for c in all_cats if str(getattr(c, 'id', '')).isdigit()] + [0])
            new_id = str(max_id + 1)
        except: new_id = str(uuid.uuid4())
        
        cat = MachineCategory(id=new_id, name=category_name, description=f"{category_name} machines", created_at=datetime.now().isoformat())
        db.add(cat)
        db.commit()
    return cat

@router.post("/machines")
async def seed_machines(db: any = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can seed")
    
    try:
        # Clear existing via soft delete
        existing = db.query(Machine).all()
        for m in existing:
            db.delete(m, soft=False) # Hard delete for seeding? Non-destructive is better but here we usually re-init
        
        added = []
        for name, cat_name in UNIT_1_MACHINES:
            cat = get_or_create_category(db, cat_name)
            m = Machine(id=str(uuid.uuid4()), machine_name=name, status="active", hourly_rate=0.0, category_id=str(cat.id), unit_id="1", is_deleted=False, created_at=datetime.now().isoformat())
            db.add(m)
            added.append(name)
            
        for name, cat_name in UNIT_2_MACHINES:
            cat = get_or_create_category(db, cat_name)
            m = Machine(id=str(uuid.uuid4()), machine_name=name, status="active", hourly_rate=0.0, category_id=str(cat.id), unit_id="2", is_deleted=False, created_at=datetime.now().isoformat())
            db.add(m)
            added.append(name)
            
        db.commit()
        return {"count": len(added), "machines": added}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migrate-passwords")
async def migrate_passwords(secret: str = Query(..., description="Migration secret"), db: any = Depends(get_db)):
    if secret != MIGRATION_SECRET: raise HTTPException(status_code=403, detail="Invalid secret")
    
    fixed = {'admin': 'Admin@Secure2024!', 'operator': 'Operator#Safe99', 'supervisor': 'Super$Visor88', 'planning': 'Plan%Ning77'}
    all_u = db.query(User).all()
    migrated = []
    
    for username, pw in fixed.items():
        u = next((user for user in all_u if str(getattr(user, 'username', '')).lower() == username.lower()), None)
        if u:
            u.password_hash = hash_password(pw)
            u.updated_at = datetime.now().isoformat()
            migrated.append(username)
    
    db.commit()
    return {"migrated": migrated}
