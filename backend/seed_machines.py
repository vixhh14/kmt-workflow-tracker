import sys
import os
import uuid
import time
sys.path.append(os.path.join(os.getcwd())) # Add backend root

from app.core.sheets_db import get_sheets_db, SheetsDB
from app.models.models_db import Machine
from app.core.time_utils import get_current_time_ist

# Data from Prompt
UNIT_1_MACHINES = [
    ("Hand Grinder", "Grinder"),
    ("Bench Grinder", "Grinder"),
    ("Tool and Cutter Grinder", "Grinder"),
    ("Turnmaster", "Lathe"),
    ("Leader", "Lathe"),
    ("Bandsaw Cutting Manual", "Material Cutting"),
    ("Bandsaw Cutting Auto", "Material Cutting"),
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
    ("Hand Drilling 1", "Drilling"),
    ("Hand Drilling 2", "Drilling"),
    ("Hand Grinding 1", "Grinder"),
    ("Hand Grinding 2", "Grinder"),
    ("Hitachi Cutting Machine", "Material Cutting"),
    ("HMT Rack Cutting", "Rack Cutting"),
    ("L Rack Cutting", "Rack Cutting"),
    ("Reinecker", "Lathe"),
    ("Zimberman", "CNC"),
    ("EIFCO Stationary Drilling", "Drilling")
]

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
    ("EIFCO Radial Drilling", "Drilling")
]

def seed_machines():
    print("🚀 Starting Machine Seeding Process...")
    
    db = get_sheets_db()
    
    # 1. Fetch Existing Machines for Idempotency
    print("Fetching existing machines...")
    # Trigger a read to populate cache
    all_machines = db.query(Machine).all()
    
    existing_map = {} # Key: "{name}|{unit}"
    for m in all_machines:
        # Normalize keys for comparison
        name = str(getattr(m, 'machine_name', '')).strip().lower()
        unit = str(getattr(m, 'unit_id', '')).strip().lower()
        if not getattr(m, 'is_deleted', False):
             existing_map[f"{name}|{unit}"] = True
             
    print(f"Found {len(existing_map)} existing active machines.")
    
    machines_to_add = []
    
    # Helper to prepare machine dict
    def prepare_machine(name, category, unit):
        key = f"{name.strip().lower()}|{unit.strip().lower()}"
        if key in existing_map:
            print(f"  ⏭️ Skipping {name} ({unit}) - Already exists")
            return None
        
        now = get_current_time_ist().isoformat()
        return {
            "id": str(uuid.uuid4()),
            "machine_name": name.strip(),
            "category_id": category.strip(), # Using string as requested mapping
            "unit_id": unit.strip(),         # Using string as requested mapping
            "status": "Active",
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
            
            # Default empty fields to prevent irregularities
            "hourly_rate": "",
            "last_maintenance": "",
            "current_operator": ""
        }

    # Process Unit 1
    print("\nProcessing Unit 1...")
    for name, cat in UNIT_1_MACHINES:
        m = prepare_machine(name, cat, "Unit 1")
        if m: machines_to_add.append(m)

    # Process Unit 2
    print("\nProcessing Unit 2...")
    for name, cat in UNIT_2_MACHINES:
        m = prepare_machine(name, cat, "Unit 2")
        if m: machines_to_add.append(m)
        
    if not machines_to_add:
        print("\n✅ All machines already exist. No action taken.")
        return

    # Batch Insert
    print(f"\n📝 Inserting {len(machines_to_add)} new machines...")
    
    # Use repo directly for batch append since SheetsDB doesn't expose it directly yet
    # But wait, SheetsDB abstracts repo. 
    # sheets_repo is a singleton in sheets_repository.py, imported by sheets_db
    
    from app.repositories.sheets_repository import sheets_repo
    
    # We need to manually inject them via repo to use batch_append
    success = sheets_repo.batch_append("Machines", machines_to_add)
    
    if success:
        print("\n✅ Machines seeded successfully (Unit 1 & Unit 2)")
        print(f"Added {len(machines_to_add)} records.")
        # Verify cache update
        print("Verifying cache...")
        new_count = len(db.query(Machine).all())
        print(f"Total machines in cache now: {new_count}")
    else:
        print("\n❌ Failed to batch seed machines.")

if __name__ == "__main__":
    seed_machines()
