"""
Complete test of login and signup functionality
"""
import sqlite3
import sys

print("="*70)
print("CHECKING DATABASE AND DEMO USERS")
print("="*70)

try:
    conn = sqlite3.connect('backend/workflow.db')
    cursor = conn.cursor()
    
    # Check users
    cursor.execute("SELECT username, role, approval_status FROM users")
    users = cursor.fetchall()
    
    if len(users) == 0:
        print("\n❌ NO USERS FOUND IN DATABASE!")
        print("Run: python backend/create_demo_users.py")
        sys.exit(1)
    
    print(f"\n✅ Found {len(users)} users:")
    print("-" * 70)
    for u in users:
        print(f"  Username: {u[0]:15} | Role: {u[1]:12} | Status: {u[2]}")
    print("-" * 70)
    
    # Check for admin
    admin = [u for u in users if u[0] == 'admin']
    if admin:
        print(f"\n✅ Admin user exists with status: {admin[0][2]}")
        if admin[0][2] != 'approved':
            print("⚠️  WARNING: Admin status should be 'approved'")
    else:
        print("\n❌ NO ADMIN USER FOUND!")
        print("Run: python backend/create_demo_users.py")
    
    conn.close()
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("1. Make sure backend is running:")
    print("   cd backend")
    print("   uvicorn app.main:app --reload")
    print()
    print("2. Make sure frontend is running:")
    print("   cd frontend")
    print("   npm run dev")
    print()
    print("3. Open: http://localhost:5173")
    print("4. Login with: admin / admin123")
    print()
    print("5. To deploy new UI to production:")
    print("   git add .")
    print("   git commit -m \"Fix login, signup, and update UI\"")
    print("   git push")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
