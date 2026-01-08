import os
import uuid
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from app.core.time_utils import get_current_time_ist

def sync_schema():
    """Manually sync schema changes that create_all might skip (like new columns)"""
    from sqlalchemy import text
    from sqlalchemy.orm import sessionmaker
    from app.core.database import engine

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # 1. New Columns Sync
        tables = ["filing_tasks", "fabrication_tasks"]
        new_cols = [
            ("started_at", "TIMESTAMPTZ"),
            ("on_hold_at", "TIMESTAMPTZ"),
            ("resumed_at", "TIMESTAMPTZ"),
            ("completed_at", "TIMESTAMPTZ"),
            ("total_active_duration", "INTEGER DEFAULT 0")
        ]
        
        for table in tables:
            for col_name, col_type in new_cols:
                try:
                    # Check if column exists
                    query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col_name}'")
                    exists = session.execute(query).fetchone()
                    
                    if not exists:
                        print(f"🛠 Adding column {col_name} to {table}...")
                        session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                        session.commit()
                except Exception as col_err:
                    print(f"⚠️ Could not add {col_name} to {table}: {col_err}")
                    session.rollback()

        # 2. project_id Type Sync (INTEGER -> VARCHAR)
        # This is critical for preventing 500 errors on project creation
        tables_to_fix = ["tasks", "filing_tasks", "fabrication_tasks", "projects"]
        for table in tables_to_fix:
            try:
                query = text(f"SELECT data_type FROM information_schema.columns WHERE table_name='{table}' AND column_name='project_id'")
                result = session.execute(query).fetchone()
                if result and 'int' in result[0].lower():
                    print(f"🛠 Converting {table}.project_id to VARCHAR...")
                    session.execute(text(f"ALTER TABLE {table} ALTER COLUMN project_id TYPE VARCHAR USING project_id::VARCHAR"))
                    session.commit()
            except Exception as type_err:
                print(f"⚠️ Could not convert project_id in {table}: {type_err}")
                session.rollback()

        # 3. Tasks Table Audit Fields
        task_cols = [
            ("ended_by", "VARCHAR"),
            ("end_reason", "VARCHAR")
        ]
        
        for col_name, col_type in task_cols:
             try:
                query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='tasks' AND column_name='{col_name}'")
                exists = session.execute(query).fetchone()

                if not exists:
                    print(f"🛠 Adding column {col_name} to tasks...")
                    session.execute(text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}"))
                    session.commit()
             except Exception as task_col_err:
                 print(f"⚠️ Could not add {col_name} to tasks: {task_col_err}")
                 session.rollback()

    except Exception as e:
        print(f"❌ sync_schema error: {e}")
    finally:
        session.close()

def init_db_data():
    print(f"Initializing database data...")
    
    # 1. Sync Schema (Add missing columns if any)
    sync_schema()

    # Connect to the ACTIVE database
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
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
            existing = session.execute(text("SELECT id FROM machines WHERE machine_name = :name AND unit_id = :uid"), {"name": name, "uid": unit_id}).fetchone()
            
            if existing:
                # Update existing
                session.execute(text("""
                    UPDATE machines 
                    SET category_id = :cat_id, status = 'active', updated_at = :now, is_deleted = FALSE
                    WHERE id = :id
                """), {"cat_id": category_id, "now": get_current_time_ist(), "id": existing.id})
            else:
                # Insert new
                machine_id = str(uuid.uuid4())
                # Insert new
                machine_id = str(uuid.uuid4())
                session.execute(text("""
                    INSERT INTO machines (id, machine_name, status, hourly_rate, unit_id, category_id, created_at, updated_at, is_deleted)
                    VALUES (:id, :name, 'active', 0.0, :uid, :cat_id, :now, :now, FALSE)
                """), {"id": machine_id, "name": name, "uid": unit_id, "cat_id": category_id, "now": get_current_time_ist()})

        for name, cat in unit2_machines:
            upsert_machine(name, cat, "Unit 2")

        for name, cat in unit1_machines:
            upsert_machine(name, cat, "Unit 1")

        session.commit()
        print("✅ Database initialization (seeding) complete.")
            
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        session.rollback()
    finally:
        session.close()
