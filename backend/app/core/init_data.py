import sqlite3
import os
import uuid
from datetime import datetime
from datetime import datetime
from app.core.database import DEFAULT_DB_PATH
from app.core.migration_utils import migrate_sqlite_to_postgres

def init_db_data():
    print(f"Initializing database data...")
    
    # 0. MIGRATION: Attempt to migrate from SQLite to Postgres if needed
    migrate_sqlite_to_postgres()
    
    print(f"Checking for seeding at: {DEFAULT_DB_PATH}")
    
    # Ensure directory exists (only relevant for local SQLite)
    if "workflow.db" in DEFAULT_DB_PATH:
        os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)
    
    # Connect to the ACTIVE database (could be SQLite or Postgres)
    # We use SQLAlchemy engine for agnostic connection or direct sqlite for legacy
    # For seeding, we'll stick to the configured connection in database.py
    from app.core.database import engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # 1. MIGRATION: Check for created_at in machines (Legacy SQLite check, kept for safety)
        # In Postgres, Alembic/SQLAlchemy should handle schema, but we'll leave this for SQLite compat
        if "sqlite" in str(engine.url):
            conn = sqlite3.connect(DEFAULT_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(machines)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'created_at' not in columns:
                print("Migrating: Adding created_at column to machines table...")
                cursor.execute("ALTER TABLE machines ADD COLUMN created_at TIMESTAMP")
                cursor.execute("UPDATE machines SET created_at = ?", (datetime.utcnow(),))
                conn.commit()
                print("✅ created_at column added.")
            conn.close()
        
        # 2. SEEDING: Ensure Categories
        categories = [
            "Material Cutting", "Welding", "Lathe", "CNC", "Slotting", "Grinding", "Drilling",
            "Grinder", "VMC", "Milling", "Engraving", "Honing", "Buffing", "Tooth Rounding",
            "Lapping", "Rack Cutting"
        ]
        
        for cat in categories:
            # SQL-agnostic insert
            session.execute(text("INSERT INTO machine_categories (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"), {"name": cat})
            
        # Get category IDs
        result = session.execute(text("SELECT id, name FROM machine_categories"))
        category_map = {row.name: row.id for row in result}
        
        # 3. SEEDING: Ensure Units
        unit_map = {}
        units = [("Unit 1", "Main production unit"), ("Unit 2", "Secondary production unit")]
        
        for u_name, u_desc in units:
            # Check if exists
            res = session.execute(text("SELECT id FROM units WHERE name = :name"), {"name": u_name}).fetchone()
            if res:
                unit_map[u_name] = res.id
            else:
                # Insert
                # Note: Postgres returns ID via RETURNING, SQLite via lastrowid. 
                # Simplest is insert then select.
                session.execute(text("INSERT INTO units (name, description) VALUES (:name, :desc)"), {"name": u_name, "desc": u_desc})
                session.commit()
                res = session.execute(text("SELECT id FROM units WHERE name = :name"), {"name": u_name}).fetchone()
                unit_map[u_name] = res.id

        # 4. SEEDING: Machines List
        # ... (Machine lists remain the same)

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

            # Check if existing
            existing = session.execute(text("SELECT id FROM machines WHERE name = :name AND unit_id = :uid"), {"name": name, "uid": unit_id}).fetchone()
            
            if existing:
                # Update existing
                session.execute(text("""
                    UPDATE machines 
                    SET category_id = :cat_id, status = 'active', updated_at = :now
                    WHERE id = :id
                """), {"cat_id": category_id, "now": datetime.utcnow(), "id": existing.id})
            else:
                # Insert new
                machine_id = str(uuid.uuid4())
                session.execute(text("""
                    INSERT INTO machines (id, name, status, hourly_rate, unit_id, category_id, created_at, updated_at)
                    VALUES (:id, :name, 'active', 0.0, :uid, :cat_id, :now, :now)
                """), {"id": machine_id, "name": name, "uid": unit_id, "cat_id": category_id, "now": datetime.utcnow()})

        for name, cat in unit2_machines:
            upsert_machine(name, cat, "Unit 2")

        for name, cat in unit1_machines:
            upsert_machine(name, cat, "Unit 1")

        session.commit()
        print("✅ Database initialization (migration + seeding) complete.")
            
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        session.rollback()
    finally:
        session.close()
