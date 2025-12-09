import sqlite3
import os
import uuid
from datetime import datetime

def seed_fresh_machines():
    db_path = 'workflow.db'
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing machines to ensure fresh start as requested ("fresh records")
        # Or should we just add them? The user said "add the following machines... as fresh records".
        # But also "Store them permanently".
        # To avoid duplicates if they run this multiple times, let's check if they exist or just clear and re-add.
        # Given "fresh records" and the comprehensive list, it implies this is the desired state.
        # However, deleting might remove history linked to machine IDs if any.
        # But since this is likely a setup phase or a reset request, let's try to upsert or clear.
        # Safest is to check if machine exists by name and unit, if so update, else insert.
        # But user said "fresh records", implying new IDs potentially?
        # Let's assume we want to ensure THESE machines exist.
        
        # Let's first ensure categories exist
        categories = [
            "Material Cutting", "Welding", "Lathe", "CNC", "Slotting", "Grinding", "Drilling",
            "Grinder", "VMC", "Milling", "Engraving", "Honing", "Buffing", "Tooth Rounding",
            "Lapping", "Rack Cutting"
        ]
        
        print("\nEnsuring categories exist...")
        for cat in categories:
            cursor.execute("INSERT OR IGNORE INTO machine_categories (name) VALUES (?)", (cat,))
            
        # Get category IDs
        cursor.execute("SELECT id, name FROM machine_categories")
        category_map = {name: id for id, name in cursor.fetchall()}
        
        # Get Unit IDs
        cursor.execute("SELECT id, name FROM units")
        unit_map = {name: id for id, name in cursor.fetchall()}
        
        # Ensure units exist if not found
        if "Unit 1" not in unit_map:
            cursor.execute("INSERT INTO units (name, description) VALUES (?, ?)", ("Unit 1", "Main production unit"))
            unit_map["Unit 1"] = cursor.lastrowid
        if "Unit 2" not in unit_map:
            cursor.execute("INSERT INTO units (name, description) VALUES (?, ?)", ("Unit 2", "Secondary production unit"))
            unit_map["Unit 2"] = cursor.lastrowid
            
        # Refresh unit map
        cursor.execute("SELECT id, name FROM units")
        unit_map = {name: id for id, name in cursor.fetchall()}

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

        unit1_machines = [
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

        # Function to insert machine
        def insert_machine(name, category, unit_name):
            unit_id = unit_map.get(unit_name)
            category_id = category_map.get(category)
            
            if not category_id:
                print(f"Warning: Category '{category}' not found for machine '{name}'")
                return

            # Check if machine already exists
            cursor.execute("SELECT id FROM machines WHERE name = ? AND unit_id = ?", (name, unit_id))
            existing = cursor.fetchone()
            
            if existing:
                print(f"Machine '{name}' already exists in {unit_name}. Updating...")
                cursor.execute("""
                    UPDATE machines 
                    SET category_id = ?, status = 'active', updated_at = ?
                    WHERE id = ?
                """, (category_id, datetime.utcnow(), existing[0]))
            else:
                print(f"Inserting new machine '{name}' into {unit_name}...")
                machine_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO machines (id, name, status, hourly_rate, unit_id, category_id, created_at, updated_at)
                    VALUES (?, ?, 'active', 0.0, ?, ?, ?, ?)
                """, (machine_id, name, unit_id, category_id, datetime.utcnow(), datetime.utcnow()))

        print("\nProcessing Unit 2 Machines...")
        for name, cat in unit2_machines:
            insert_machine(name, cat, "Unit 2")

        print("\nProcessing Unit 1 Machines...")
        for name, cat in unit1_machines:
            insert_machine(name, cat, "Unit 1")

        conn.commit()
        print("\n✅ Machines processed successfully!")
        
        # Verification
        cursor.execute("SELECT COUNT(*) FROM machines WHERE unit_id = ?", (unit_map["Unit 1"],))
        u1_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM machines WHERE unit_id = ?", (unit_map["Unit 2"],))
        u2_count = cursor.fetchone()[0]
        
        print(f"\nTotal Machines in Unit 1: {u1_count}")
        print(f"Total Machines in Unit 2: {u2_count}")

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_fresh_machines()
