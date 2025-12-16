from sqlalchemy import create_engine, text
from app.core.database import SQLALCHEMY_DATABASE_URL
import uuid

def verify_fix():
    print("Verifying Schema Fixes...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        with conn.begin():
            # 1. Try to Insert a Machine using machine_name
            mach_id = str(uuid.uuid4())
            print(f"Attempting to insert machine {mach_id}...")
            # We must use raw SQL to test the DB schema directly
            # Note: unit_id and category_id must enable valid FKs. 
            # I will use NULL or valid IDs if I knew them. 
            # Assuming optional for this test or I can find one.
            
            # Find a unit and category first
            r = conn.execute(text("SELECT id FROM units LIMIT 1")).first()
            u_id = r[0] if r else None
            r = conn.execute(text("SELECT id FROM machine_categories LIMIT 1")).first()
            c_id = r[0] if r else None
            
            if u_id and c_id:
                try:
                    conn.execute(text(f"""
                        INSERT INTO machines (id, machine_name, status, unit_id, category_id, is_deleted, created_at, updated_at)
                        VALUES ('{mach_id}', 'Test Machine', 'active', {u_id}, {c_id}, FALSE, NOW(), NOW())
                    """))
                    print("✅ Insert successful with 'machine_name'.")
                    
                    # 2. Select it back
                    r = conn.execute(text(f"SELECT machine_name FROM machines WHERE id='{mach_id}'")).first()
                    if r and r[0] == 'Test Machine':
                        print(f"✅ Select successful: {r[0]}")
                    else:
                        print("❌ Select failed or name mismatch.")
                        
                    # Clean up
                    conn.execute(text(f"DELETE FROM machines WHERE id='{mach_id}'"))
                except Exception as e:
                     print(f"❌ Insert failed: {e}")
            else:
                print("⚠️ Cannot test Insert: No Units or Categories found.")

            # 3. Check Tasks is_deleted column
            try:
                conn.execute(text("SELECT is_deleted FROM tasks LIMIT 1"))
                print("✅ Tasks 'is_deleted' column exists.")
            except Exception as e:
                print(f"❌ Tasks 'is_deleted' missing: {e}")

if __name__ == "__main__":
    verify_fix()
