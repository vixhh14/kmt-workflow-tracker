"""
Database Migration Script for Attendance System Fix

This script applies the attendance system database migration.
Run this after updating the codebase to ensure database schema is correct.

Usage:
    python backend/run_attendance_migration.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine
from sqlalchemy import text

def run_migration():
    """Run the attendance system migration"""
    
    migration_file = Path(__file__).parent / 'migrations' / 'fix_attendance_system.sql'
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print("📋 Reading migration file...")
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print("🔄 Executing migration...")
    try:
        with engine.begin() as conn:
            # Execute the migration SQL
            conn.execute(text(migration_sql))
            print("✅ Migration completed successfully!")
            
            # Verify the changes
            print("\n📊 Verifying migration...")
            
            # Check if unique index exists
            result = conn.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'attendance' 
                AND indexname = 'idx_attendance_user_date'
            """))
            
            if result.fetchone():
                print("  ✓ Unique index created successfully")
            else:
                print("  ⚠️  Warning: Unique index may not have been created")
            
            # Check column types
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'attendance'
                ORDER BY ordinal_position
            """))
            
            print("\n  📋 Attendance table columns:")
            for row in result:
                print(f"     - {row.column_name}: {row.data_type}")
            
            # Count total records
            result = conn.execute(text("SELECT COUNT(*) FROM attendance"))
            count = result.scalar()
            print(f"\n  📊 Total attendance records: {count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("ATTENDANCE SYSTEM DATABASE MIGRATION")
    print("=" * 60)
    print()
    
    success = run_migration()
    
    print()
    print("=" * 60)
    if success:
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print()
        print("Next steps:")
        print("  1. Restart your backend server")
        print("  2. Test login/logout functionality")
        print("  3. Verify attendance records in database")
    else:
        print("❌ MIGRATION FAILED")
        print()
        print("Please check the error messages above and fix any issues.")
    print("=" * 60)
