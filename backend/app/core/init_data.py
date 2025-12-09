import sqlite3
import os
import uuid
from datetime import datetime
from app.core.database import DEFAULT_DB_PATH

def init_db_data():
    print(f"Initializing database data at: {DEFAULT_DB_PATH}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. MIGRATION: Check for created_at in machines
        cursor.execute("PRAGMA table_info(machines)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'created_at' not in columns:
            print("Migrating: Adding created_at column to machines table...")
            cursor.execute("ALTER TABLE machines ADD COLUMN created_at TIMESTAMP")
            cursor.execute("UPDATE machines SET created_at = ?", (datetime.utcnow(),))
            print("✅ created_at column added.")
        
        # 2. SEEDING: Ensure Categories
        categories = [
            "Material Cutting", "Welding", "Lathe", "CNC", "Slotting", "Grinding", "Drilling",
            "Grinder", "VMC", "Milling", "Engraving", "Honing", "Buffing", "Tooth Rounding",
            "Lapping", "Rack Cutting"
        ]
        
        for cat in categories:
            cursor.execute("INSERT OR IGNORE INTO machine_categories (name) VALUES (?)", (cat,))
            
        # Get category IDs
        cursor.execute("SELECT id, name FROM machine_categories")
        category_map = {name: id for id, name in cursor.fetchall()}
        
        # 3. SEEDING: Ensure Units
        unit_map = {}
        units = [("Unit 1", "Main production unit"), ("Unit 2", "Secondary production unit")]
        
        for u_name, u_desc in units:
            cursor.execute("SELECT id FROM units WHERE name = ?", (u_name,))
            res = cursor.fetchone()
            if res:
                unit_map[u_name] = res[0]
            else:
                cursor.execute("INSERT INTO units (name, description) VALUES (?, ?)", (u_name, u_desc))
                unit_map[u_name] = cursor.lastrowid

        # 4. SEEDING: Machines List
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

        def upsert_machine(name, category, unit_name):
            unit_id = unit_map.get(unit_name)
            category_id = category_map.get(category)
            
            if not category_id:
                print(f"Warning: Category '{category}' not found for machine '{name}'")
                return

            cursor.execute("SELECT id FROM machines WHERE name = ? AND unit_id = ?", (name, unit_id))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                cursor.execute("""
                    UPDATE machines 
                    SET category_id = ?, status = 'active', updated_at = ?
                    WHERE id = ?
                """, (category_id, datetime.utcnow(), existing[0]))
            else:
                # Insert new
                machine_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO machines (id, name, status, hourly_rate, unit_id, category_id, created_at, updated_at)
                    VALUES (?, ?, 'active', 0.0, ?, ?, ?, ?)
                """, (machine_id, name, unit_id, category_id, datetime.utcnow(), datetime.utcnow()))

        for name, cat in unit2_machines:
            upsert_machine(name, cat, "Unit 2")

        for name, cat in unit1_machines:
            upsert_machine(name, cat, "Unit 1")

        conn.commit()
        print("✅ Database initialization (migration + seeding) complete.")
            
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        conn.rollback()
    finally:
        conn.close()
