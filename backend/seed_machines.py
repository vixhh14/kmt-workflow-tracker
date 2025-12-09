"""
Seed script to populate machines with categories and units.
Run this script after deploying to add the 39 machines to the database.

Usage: python seed_machines.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import engine, Base, get_db
from app.models.models_db import Machine, Unit, MachineCategory
from datetime import datetime
import uuid

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Units data
UNITS = [
    {"id": 1, "name": "Unit 1", "description": "Main production unit"},
    {"id": 2, "name": "Unit 2", "description": "Secondary production unit"},
]

# Categories data
CATEGORIES = [
    {"id": 1, "name": "Material Cutting", "description": "Gas cutting and bandsaw machines"},
    {"id": 2, "name": "Welding", "description": "Tig and CO2 welding machines"},
    {"id": 3, "name": "Lathe", "description": "Lathe and turning machines"},
    {"id": 4, "name": "CNC", "description": "Computer numerical control machines"},
    {"id": 5, "name": "Slotting", "description": "Slotting machines"},
    {"id": 6, "name": "Grinding", "description": "Surface and precision grinding"},
    {"id": 7, "name": "Drilling", "description": "Drilling and boring machines"},
    {"id": 8, "name": "Grinder", "description": "Hand and bench grinders"},
    {"id": 9, "name": "VMC", "description": "Vertical machining center"},
    {"id": 10, "name": "Milling", "description": "Milling machines"},
    {"id": 11, "name": "Engraving", "description": "Engraving machines"},
    {"id": 12, "name": "Honing", "description": "Honing machines"},
    {"id": 13, "name": "Buffing", "description": "Buffing and polishing machines"},
    {"id": 14, "name": "Tooth Rounding", "description": "Gear tooth rounding machines"},
    {"id": 15, "name": "Lapping", "description": "Lapping machines"},
    {"id": 16, "name": "Rack Cutting", "description": "Rack cutting machines"},
]

# Machines data - Unit 1 (11 machines)
UNIT1_MACHINES = [
    {"name": "Gas Cutting", "category": "Material Cutting"},
    {"name": "Tig Welding", "category": "Welding"},
    {"name": "CO2 Welding LD", "category": "Welding"},
    {"name": "CO2 Welding HD", "category": "Welding"},
    {"name": "PSG", "category": "Lathe"},
    {"name": "Ace Superjobber", "category": "CNC"},
    {"name": "Slotting Machine", "category": "Slotting"},
    {"name": "Surface Grinding", "category": "Grinding"},
    {"name": "Thakur Drilling", "category": "Drilling"},
    {"name": "Toolvasor Magnetic Drilling", "category": "Drilling"},
    {"name": "EIFCO Radial Drilling", "category": "Drilling"},
]

# Machines data - Unit 2 (27 machines)
UNIT2_MACHINES = [
    {"name": "Hand Grinder", "category": "Grinder"},
    {"name": "Bench Grinder", "category": "Grinder"},
    {"name": "Tool and Cutter Grinder", "category": "Grinder"},
    {"name": "Turnmaster", "category": "Lathe"},
    {"name": "Leader", "category": "Lathe"},
    {"name": "Bandsaw cutting Manual", "category": "Material Cutting"},
    {"name": "Bandsaw cutting Auto", "category": "Material Cutting"},
    {"name": "VMC Pilot", "category": "VMC"},
    {"name": "ESTEEM DRO", "category": "Milling"},
    {"name": "FW Horizontal", "category": "Milling"},
    {"name": "Arno", "category": "Milling"},
    {"name": "BFW No 2", "category": "Milling"},
    {"name": "Engraving Machine", "category": "Engraving"},
    {"name": "Delapena Honing Machine", "category": "Honing"},
    {"name": "Buffing Machine", "category": "Buffing"},
    {"name": "Tooth Rounding Machine", "category": "Tooth Rounding"},
    {"name": "Lapping Machine", "category": "Lapping"},
    {"name": "Hand Drilling 2", "category": "Drilling"},
    {"name": "Hand Drilling 1", "category": "Drilling"},
    {"name": "Hand Grinding 2", "category": "Grinder"},
    {"name": "Hand Grinding 1", "category": "Grinder"},
    {"name": "Hitachi Cutting Machine", "category": "Material Cutting"},
    {"name": "HMT Rack Cutting", "category": "Rack Cutting"},
    {"name": "L Rack Cutting", "category": "Rack Cutting"},
    {"name": "Reinecker", "category": "Lathe"},
    {"name": "Zimberman", "category": "CNC"},
    {"name": "EIFCO Stationary Drilling", "category": "Drilling"},
]


def seed_database():
    """Seed the database with units, categories, and machines."""
    db = next(get_db())
    
    try:
        # Create category name to id mapping
        category_map = {cat["name"]: cat["id"] for cat in CATEGORIES}
        
        # Insert Units
        print("Inserting units...")
        for unit_data in UNITS:
            existing = db.query(Unit).filter(Unit.id == unit_data["id"]).first()
            if not existing:
                unit = Unit(**unit_data, created_at=datetime.utcnow())
                db.add(unit)
                print(f"  + Added: {unit_data['name']}")
            else:
                print(f"  - Exists: {unit_data['name']}")
        
        # Insert Categories
        print("\nInserting categories...")
        for cat_data in CATEGORIES:
            existing = db.query(MachineCategory).filter(MachineCategory.id == cat_data["id"]).first()
            if not existing:
                category = MachineCategory(**cat_data, created_at=datetime.utcnow())
                db.add(category)
                print(f"  + Added: {cat_data['name']}")
            else:
                print(f"  - Exists: {cat_data['name']}")
        
        db.commit()
        
        # Insert Unit 2 Machines
        print(f"\nInserting Unit 2 machines ({len(UNIT2_MACHINES)} machines)...")
        for machine_data in UNIT2_MACHINES:
            existing = db.query(Machine).filter(Machine.name == machine_data["name"]).first()
            if not existing:
                machine = Machine(
                    id=str(uuid.uuid4()),
                    name=machine_data["name"],
                    status="active",
                    hourly_rate=0.0,
                    category_id=category_map.get(machine_data["category"]),
                    unit_id=2,  # Unit 2
                    updated_at=datetime.utcnow()
                )
                db.add(machine)
                print(f"  + Added: {machine_data['name']} ({machine_data['category']})")
            else:
                print(f"  - Exists: {machine_data['name']}")
        
        # Insert Unit 1 Machines
        print(f"\nInserting Unit 1 machines ({len(UNIT1_MACHINES)} machines)...")
        for machine_data in UNIT1_MACHINES:
            existing = db.query(Machine).filter(Machine.name == machine_data["name"]).first()
            if not existing:
                machine = Machine(
                    id=str(uuid.uuid4()),
                    name=machine_data["name"],
                    status="active",
                    hourly_rate=0.0,
                    category_id=category_map.get(machine_data["category"]),
                    unit_id=1,  # Unit 1
                    updated_at=datetime.utcnow()
                )
                db.add(machine)
                print(f"  + Added: {machine_data['name']} ({machine_data['category']})")
            else:
                print(f"  - Exists: {machine_data['name']}")
        
        db.commit()
        
        # Summary
        total_units = db.query(Unit).count()
        total_categories = db.query(MachineCategory).count()
        total_machines = db.query(Machine).count()
        
        print("\n" + "="*50)
        print("SEED COMPLETE!")
        print("="*50)
        print(f"Total Units: {total_units}")
        print(f"Total Categories: {total_categories}")
        print(f"Total Machines: {total_machines}")
        print("="*50)
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("="*50)
    print("MACHINE MASTER LIST SEED SCRIPT")
    print("="*50)
    seed_database()
