
from app.core.database import get_db
from app.models.models_db import User

def verify_db():
    db = next(get_db())
    # Try to find 'admin' user
    admin = db.query(User).filter(username="admin").first()
    if admin:
        print(f"✅ Found Admin: ID={getattr(admin, 'id')}, Role={getattr(admin, 'role')}")
        print(f"   Full Name: {getattr(admin, 'full_name')}")
    else:
        print("❌ Admin user not found in cache (might be different username case?)")
        all_u = db.query(User).all()
        print(f"   Total Users in cache: {len(all_u)}")
        if all_u:
            print(f"   First user: {getattr(all_u[0], 'username')}")

if __name__ == "__main__":
    verify_db()
