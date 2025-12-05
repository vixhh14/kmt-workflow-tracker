"""
Complete setup script for the workflow tracker onboarding system.
This script will:
1. Initialize the database with all tables
2. Run the onboarding system migration
3. Seed units, categories, and machines
4. Create demo users

Run this script to set up the complete onboarding system.
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("WORKFLOW TRACKER - ONBOARDING SYSTEM SETUP")
    print("=" * 60)
    
    # Step 1: Initialize database
    print("\n[1/4] Initializing database...")
    try:
        from init_db import init_db
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return
    
    # Step 2: Run onboarding migration
    print("\n[2/4] Running onboarding system migration...")
    try:
        from migrate_onboarding_system import migrate_onboarding_system
        migrate_onboarding_system()
        print("✅ Migration completed successfully")
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return
    
    # Step 3: Seed units and machines
    print("\n[3/4] Seeding units, categories, and machines...")
    try:
        from seed_units_and_machines import seed_units_and_machines
        seed_units_and_machines()
        print("✅ Seed data inserted successfully")
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        return
    
    # Step 4: Summary
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\n📋 What was created:")
    print("  ✓ Database tables (users, machines, tasks, etc.)")
    print("  ✓ Onboarding tables (units, machine_categories, user_machines, user_approvals)")
    print("  ✓ 2 Units (Unit 1, Unit 2)")
    print("  ✓ 16 Machine categories")
    print("  ✓ 38 Machines (27 in Unit 1, 11 in Unit 2)")
    print("  ✓ 5 Demo users (admin, operator, supervisor, planning, vendor)")
    
    print("\n🔐 Demo User Credentials:")
    print("  Admin:      username: admin      | password: admin123")
    print("  Operator:   username: operator   | password: operator123")
    print("  Supervisor: username: supervisor | password: supervisor123")
    print("  Planning:   username: planning   | password: planning123")
    print("  Vendor:     username: vendor     | password: vendor123")
    
    print("\n🚀 Next Steps:")
    print("  1. Start the backend: cd backend && uvicorn app.main:app --reload")
    print("  2. Start the frontend: cd frontend && npm run dev")
    print("  3. Visit http://localhost:5173 to access the application")
    print("  4. New users can sign up at http://localhost:5173/signup")
    print("  5. Admin can approve users at http://localhost:5173/admin/approvals")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
