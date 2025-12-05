"""
Script to update machines in the database.
Run this script from the backend directory: python update_machines.py
"""
import sys
import os

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from app.models.models_db import Machine, MachineCategory, Base
import uuid

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

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

def get_or_create_category(db, category_name):
    """Get existing category or create new one."""
    category = db.query(MachineCategory).filter(MachineCategory.name == category_name).first()
    if not category:
        category = MachineCategory(name=category_name, description=f"{category_name} machines")
        db.add(category)
        db.commit()
        db.refresh(category)
        print(f"  Created category: {category_name}")
    return category

def main():
    db = SessionLocal()
    
    try:
        # Step 1: Delete all existing machines
        print("=" * 50)
        print("Removing existing demo machines...")
        deleted_count = db.query(Machine).delete()
        db.commit()
        print(f"  Deleted {deleted_count} existing machines")
        
        # Step 2: Add Unit 1 machines
        print("\n" + "=" * 50)
        print("Adding Unit 1 machines...")
        for name, category_name in UNIT_1_MACHINES:
            category = get_or_create_category(db, category_name)
            
            machine = Machine(
                id=str(uuid.uuid4()),
                name=name,
                status="active",
                hourly_rate=0.0,
                category_id=category.id,
                unit_id=1  # Unit 1
            )
            db.add(machine)
            print(f"  Added: {name} ({category_name}) - Unit 1")
        
        db.commit()
        print(f"\nAdded {len(UNIT_1_MACHINES)} Unit 1 machines")
        
        # Step 3: Add Unit 2 machines
        print("\n" + "=" * 50)
        print("Adding Unit 2 machines...")
        for name, category_name in UNIT_2_MACHINES:
            category = get_or_create_category(db, category_name)
            
            machine = Machine(
                id=str(uuid.uuid4()),
                name=name,
                status="active",
                hourly_rate=0.0,
                category_id=category.id,
                unit_id=2  # Unit 2
            )
            db.add(machine)
            print(f"  Added: {name} ({category_name}) - Unit 2")
        
        db.commit()
        print(f"\nAdded {len(UNIT_2_MACHINES)} Unit 2 machines")
        
        # Summary
        total_machines = db.query(Machine).count()
        total_categories = db.query(MachineCategory).count()
        
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(f"Total machines in database: {total_machines}")
        print(f"Total categories in database: {total_categories}")
        print("\nMachines update completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
