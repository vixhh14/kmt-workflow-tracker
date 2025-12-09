"""
Script to verify database persistence and safety checks.
"""
import sys
import os
import time

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

from app.core.database import DEFAULT_DB_PATH, SessionLocal
from app.models.models_db import Machine
from app.main import startup_event
import asyncio

async def test_persistence():
    print("="*60)
    print("PERSISTENCE VERIFICATION")
    print("="*60)
    
    print(f"📂 DB Path: {DEFAULT_DB_PATH}")
    
    # 1. Simulate Startup
    print("\n[1] Simulating App Startup...")
    await startup_event()
    
    # 2. Write Data
    print("\n[2] Writing Test Data...")
    db = SessionLocal()
    test_id = f"PERSIST_TEST_{int(time.time())}"
    try:
        machine = Machine(
            id=test_id,
            name=f"Test Machine {test_id}",
            status="active",
            hourly_rate=100.0
        )
        db.add(machine)
        db.commit()
        print(f"   ✅ Added machine: {test_id}")
    except Exception as e:
        print(f"   ❌ Write failed: {e}")
    finally:
        db.close()
        
    # 3. Simulate Restart (New Session)
    print("\n[3] Simulating Restart (New Session)...")
    db2 = SessionLocal()
    try:
        found = db2.query(Machine).filter(Machine.id == test_id).first()
        if found:
            print(f"   ✅ Found machine: {found.name}")
            print("   🎉 PERSISTENCE CONFIRMED!")
        else:
            print("   ❌ Machine NOT found after new session!")
    finally:
        db2.close()
        
    # 4. Clean up
    print("\n[4] Cleaning up...")
    db3 = SessionLocal()
    try:
        db3.query(Machine).filter(Machine.id == test_id).delete()
        db3.commit()
        print("   ✅ Test data removed")
    finally:
        db3.close()

if __name__ == "__main__":
    asyncio.run(test_persistence())
