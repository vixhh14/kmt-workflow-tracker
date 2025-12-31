import sys
import os
sys.path.append(os.getcwd())
print("Starting script...")
try:
    from app.core.database import SessionLocal
    from app.models.models_db import User
    print("Imports successful.")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def check_masters():
    print("Connecting to DB...")
    try:
        db = SessionLocal()
        print("DB Connected.")
    except Exception as e:
        print(f"DB Connection failed: {e}")
        return

    masters = ["FILE_MASTER", "FAB_MASTER", "admin"]
    for role in masters:
        # Check by username
        u = db.query(User).filter(User.username == role).first()
        if u:
            print(f"User '{role}' FOUND: ID={u.user_id}, Role={u.role}")
        else:
            print(f"User '{role}' NOT FOUND")
            # enhanced check: case insensitive
            u2 = db.query(User).filter(User.username.ilike(role)).first()
            if u2:
                 print(f"User '{role}' FOUND (Case Variant): {u2.username}, ID={u2.user_id}")

    # Also list all users to be sure
    all_users = db.query(User).all()
    print("\nAll Users:")
    for user in all_users:
        print(f"- {user.username} ({user.role}) ID: {user.user_id}")

    db.close()

if __name__ == "__main__":
    check_masters()
