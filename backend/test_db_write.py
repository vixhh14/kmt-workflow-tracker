"""
Test that writing to the database updates the file timestamp.
This verifies the fix is working correctly.
"""
import sys
import os
import datetime

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

from app.core.database import DEFAULT_DB_PATH, engine, SessionLocal, Base
from app.models.models_db import Machine

print("=" * 60)
print("DATABASE WRITE TEST")
print("=" * 60)

# Get file timestamp before
stat_before = os.stat(DEFAULT_DB_PATH)
mtime_before = datetime.datetime.fromtimestamp(stat_before.st_mtime)
print(f"\nFile timestamp BEFORE write: {mtime_before}")

# Test write operation
db = SessionLocal()
try:
    # Check if test machine exists
    test_machine = db.query(Machine).filter(Machine.id == "TEST_PERSISTENCE_CHECK").first()
    
    if test_machine:
        # Update existing
        test_machine.status = f"tested_{datetime.datetime.now().strftime('%H%M%S')}"
        action = "UPDATED"
    else:
        # Create new
        test_machine = Machine(
            id="TEST_PERSISTENCE_CHECK",
            name="Persistence Test Machine",
            status="active",
            hourly_rate=0.0
        )
        db.add(test_machine)
        action = "CREATED"
    
    db.commit()
    print(f"\n[OK] {action} test machine in database")
    
except Exception as e:
    print(f"\n[ERROR] Write failed: {e}")
    db.rollback()
finally:
    db.close()

# Get file timestamp after
stat_after = os.stat(DEFAULT_DB_PATH)
mtime_after = datetime.datetime.fromtimestamp(stat_after.st_mtime)
print(f"File timestamp AFTER write:  {mtime_after}")

# Compare
if mtime_after > mtime_before:
    print(f"\n[SUCCESS] File timestamp updated! Difference: {mtime_after - mtime_before}")
else:
    print(f"\n[WARNING] File timestamp did NOT change - this may indicate writes are going elsewhere")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
