"""
Router for seeding machines and migrating passwords.
This provides admin-only endpoints for database management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models_db import Machine, MachineCategory, User
from app.core.dependencies import get_current_user
from app.core.auth_utils import hash_password
import uuid
import secrets
import string
import os

router = APIRouter(prefix="/seed", tags=["seed"])

# Migration secret - set this as environment variable for security
MIGRATION_SECRET = os.getenv("MIGRATION_SECRET", "change-this-in-production")


def generate_secure_password(length=12):
    """Generate a secure password meeting all requirements."""
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*"
    
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    
    all_chars = uppercase + lowercase + digits + special
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    
    return ''.join(password_list)


@router.post("/migrate-passwords")
async def migrate_passwords(
    secret: str = Query(..., description="Migration secret key"),
    db: Session = Depends(get_db)
):
    """
    One-time endpoint to migrate demo user passwords to secure ones.
    
    SECURITY: Requires a secret key to execute.
    Set MIGRATION_SECRET environment variable in production.
    
    Usage: POST /seed/migrate-passwords?secret=your-secret-key
    """
    # Verify secret
    if secret != MIGRATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid migration secret")
    
    # Fixed secure passwords (matching the ones shared with user)
    fixed_passwords = {
        'admin': 'Admin@Secure2024!',
        'operator': 'Operator#Safe99',
        'supervisor': 'Super$Visor88',
        'planning': 'Plan%Ning77'
    }
    
    demo_usernames = ['admin', 'operator', 'supervisor', 'planning']
    migrated_users = []
    
    try:
        for username in demo_usernames:
            user = db.query(User).filter(User.username == username).first()
            
            if user:
                # Use fixed secure password
                new_password = fixed_passwords.get(username, generate_secure_password())
                user.password_hash = hash_password(new_password)
                
                migrated_users.append({
                    "username": username,
                    "new_password": new_password,
                    "role": user.role,
                    "email": user.email
                })
        
        db.commit()
        
        return {
            "success": True,
            "message": "SAVE THESE CREDENTIALS! They won't be shown again.",
            "warning": "Delete this endpoint after use for security!",
            "migrated_count": len(migrated_users),
            "credentials": migrated_users
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

# Unit 1 Machines
UNIT_1_MACHINES = [
    ("Hand Grinder", "Grinder"),
    ("Bench Grinder", "Grinder"),
    ("Tool and Cutter Grinder", "Grinder"),
    ("Turnmaster", "Lathe"),
    ("Leader", "Lathe"),
    ("Bandsaw cutting Manual", "Material Cutting"),
    ("Bandsaw cutting Auto", "Material Cutting"),
    ("VMC Pilot", "VMC"),
    ("ESTEEM DRO", "Milling"),
    ("FW Horizontal", "Milling"),
    ("Arno", "Milling"),
    ("BFW No 2", "Milling"),
    ("Engraving Machine", "Engraving"),
    ("Delapena Honing Machine", "Honing"),
    ("Buffing Machine", "Buffing"),
    ("Tooth Rounding Machine", "Tooth Rounding"),
    ("Lapping Machine", "Lapping"),
    ("Hand Drilling 2", "Drilling"),
    ("Hand Drilling 1", "Drilling"),
    ("Hand Grinding 2", "Grinder"),
    ("Hand Grinding 1", "Grinder"),
    ("Hitachi Cutting Machine", "Material Cutting"),
    ("HMT Rack Cutting", "Rack Cutting"),
    ("L Rack Cutting", "Rack Cutting"),
    ("Reinecker", "Lathe"),
    ("Zimberman", "CNC"),
    ("EIFCO Stationary Drilling", "Drilling"),
]

# Unit 2 Machines
UNIT_2_MACHINES = [
    ("Gas Cutting", "Material Cutting"),
    ("Tig Welding", "Welding"),
    ("CO2 Welding LD", "Welding"),
    ("CO2 Welding HD", "Welding"),
    ("PSG", "Lathe"),
    ("Ace Superjobber", "CNC"),
    ("Slotting Machine", "Slotting"),
    ("Surface Grinding", "Grinding"),
    ("Thakur Drilling", "Drilling"),
    ("Toolvasor Magnetic Drilling", "Drilling"),
    ("EIFCO Radial Drilling", "Drilling"),
]


def get_or_create_category(db: Session, category_name: str) -> MachineCategory:
    """Get existing category or create new one."""
    category = db.query(MachineCategory).filter(MachineCategory.name == category_name).first()
    if not category:
        category = MachineCategory(name=category_name, description=f"{category_name} machines")
        db.add(category)
        db.commit()
        db.refresh(category)
    return category


@router.post("/machines")
async def seed_machines(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Seed the database with production machines.
    This will DELETE all existing machines and add the new ones.
    Admin only endpoint.
    """
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can seed machines")
    
    try:
        # Step 1: Delete all existing machines
        deleted_count = db.query(Machine).delete()
        db.commit()
        
        added_machines = []
        
        # Step 2: Add Unit 1 machines
        for name, category_name in UNIT_1_MACHINES:
            category = get_or_create_category(db, category_name)
            
            machine = Machine(
                id=str(uuid.uuid4()),
                machine_name=name,
                status="active",
                hourly_rate=0.0,
                category_id=category.id,
                unit_id=1  # Unit 1
            )
            db.add(machine)
            added_machines.append({"name": name, "category": category_name, "unit": 1})
        
        # Step 3: Add Unit 2 machines
        for name, category_name in UNIT_2_MACHINES:
            category = get_or_create_category(db, category_name)
            
            machine = Machine(
                id=str(uuid.uuid4()),
                machine_name=name,
                status="active",
                hourly_rate=0.0,
                category_id=category.id,
                unit_id=2  # Unit 2
            )
            db.add(machine)
            added_machines.append({"name": name, "category": category_name, "unit": 2})
        
        db.commit()
        
        # Get totals
        total_machines = db.query(Machine).count()
        total_categories = db.query(MachineCategory).count()
        
        return {
            "success": True,
            "message": "Machines seeded successfully",
            "deleted_count": deleted_count,
            "added_count": len(added_machines),
            "total_machines": total_machines,
            "total_categories": total_categories,
            "machines": added_machines
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to seed machines: {str(e)}")
