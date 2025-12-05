"""
Seed data script: Populate units, categories, and machines
Populates Unit 1 and Unit 2 with all machines as specified
"""

import sqlite3
import os
import uuid

def seed_units_and_machines():
    db_path = os.path.join(os.path.dirname(__file__), 'workflow.db')
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Insert Units
        print("\n1. Creating Units...")
        units = [
            (1, "Unit 1", "Main production unit"),
            (2, "Unit 2", "Secondary production unit")
        ]
        
        for unit in units:
            cursor.execute("""
                INSERT OR IGNORE INTO units (id, name, description)
                VALUES (?, ?, ?)
            """, unit)
        print(f"✓ Created {len(units)} units")
        
        # 2. Insert Machine Categories
        print("\n2. Creating Machine Categories...")
        categories = [
            "Grinder", "Lathe", "Material Cutting", "VMC", "Milling",
            "Engraving", "Honing", "Buffing", "Tooth Rounding", "Lapping",
            "Drilling", "Rack Cutting", "CNC", "Welding", "Slotting", "Grinding"
        ]
        
        for cat in categories:
            cursor.execute("""
                INSERT OR IGNORE INTO machine_categories (name)
                VALUES (?)
            """, (cat,))
        print(f"✓ Created {len(categories)} machine categories")
        
        # Get category IDs
        cursor.execute("SELECT id, name FROM machine_categories")
        category_map = {name: id for id, name in cursor.fetchall()}
        
        # 3. Insert Unit 1 Machines
        print("\n3. Creating Unit 1 Machines...")
        unit1_machines = [
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
            ("EIFCO Stationary Drilling", "Drilling")
        ]
        
        for machine_name, category_name in unit1_machines:
            category_id = category_map.get(category_name)
            machine_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT OR IGNORE INTO machines (id, name, status, hourly_rate, unit_id, category_id)
                VALUES (?, ?, 'active', 0.0, 1, ?)
            """, (machine_id, machine_name, category_id))
        print(f"✓ Created {len(unit1_machines)} machines for Unit 1")
        
        # 4. Insert Unit 2 Machines
        print("\n4. Creating Unit 2 Machines...")
        unit2_machines = [
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
        
        for machine_name, category_name in unit2_machines:
            category_id = category_map.get(category_name)
            machine_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT OR IGNORE INTO machines (id, name, status, hourly_rate, unit_id, category_id)
                VALUES (?, ?, 'active', 0.0, 2, ?)
            """, (machine_id, machine_name, category_id))
        print(f"✓ Created {len(unit2_machines)} machines for Unit 2")
        
        conn.commit()
        
        # 5. Display summary
        print("\n" + "="*50)
        print("SEED DATA SUMMARY")
        print("="*50)
        
        cursor.execute("SELECT COUNT(*) FROM units")
        print(f"\nUnits: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM machine_categories")
        print(f"Machine Categories: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM machines WHERE unit_id = 1")
        print(f"Unit 1 Machines: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM machines WHERE unit_id = 2")
        print(f"Unit 2 Machines: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM machines")
        print(f"Total Machines: {cursor.fetchone()[0]}")
        
        print("\n✅ Seed data inserted successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    seed_units_and_machines()
