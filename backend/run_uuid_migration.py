"""
Database Migration Runner: Complete project_id UUID Migration
Executes fix_project_id_uuid.sql safely with rollback on error
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    sys.exit(1)

# Fix Render-style postgres:// URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print("="*60)
print("DATABASE MIGRATION: project_id UUID Conversion")
print("="*60)
print(f"Target Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
print("="*60)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

def run_migration():
    """Execute the SQL migration script"""
    
    # Read SQL file
    sql_file = os.path.join(os.path.dirname(__file__), "fix_project_id_uuid.sql")
    
    if not os.path.exists(sql_file):
        print(f"❌ Migration file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    session = SessionLocal()
    
    try:
        print("\n🚀 Starting migration...")
        print("-"*60)
        
        # Execute the entire script
        # Note: PostgreSQL will handle the transaction (BEGIN...COMMIT)
        session.execute(text(sql_script))
        session.commit()
        
        print("-"*60)
        print("✅ Migration completed successfully!")
        print("="*60)
        
        # Verify results
        print("\n📊 Verification:")
        print("-"*60)
        
        result = session.execute(text("""
            SELECT 
                table_name, 
                column_name, 
                data_type 
            FROM information_schema.columns 
            WHERE column_name = 'project_id' 
            AND table_name IN ('projects', 'tasks', 'filing_tasks', 'fabrication_tasks')
            ORDER BY table_name
        """))
        
        for row in result:
            status = "✅" if row.data_type == "uuid" else "❌"
            print(f"{status} {row.table_name}.{row.column_name}: {row.data_type}")
        
        print("-"*60)
        
        # Check foreign keys
        print("\n🔗 Foreign Key Constraints:")
        print("-"*60)
        
        fk_result = session.execute(text("""
            SELECT 
                tc.table_name, 
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND kcu.column_name = 'project_id'
            ORDER BY tc.table_name
        """))
        
        for row in fk_result:
            print(f"✅ {row.table_name}.{row.column_name} → {row.foreign_table_name} ({row.constraint_name})")
        
        print("-"*60)
        
        # Check view
        print("\n👁️ Database Views:")
        print("-"*60)
        
        view_result = session.execute(text("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_name = 'project_overview'
        """))
        
        if view_result.fetchone():
            print("✅ project_overview view exists")
        else:
            print("❌ project_overview view not found")
        
        print("-"*60)
        print("\n🎉 Migration verification complete!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("-"*60)
        import traceback
        traceback.print_exc()
        session.rollback()
        print("\n🔄 Changes rolled back")
        print("="*60)
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will modify database schema!")
    print("⚠️  Ensure you have a backup before proceeding.")
    print("\nPress ENTER to continue, or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(0)
    
    success = run_migration()
    
    if success:
        print("\n✅ Next steps:")
        print("1. Restart the backend application")
        print("2. Test /projects endpoint")
        print("3. Verify dashboards load correctly")
        print("4. Check graphs populate with data")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Please review errors above.")
        sys.exit(1)
