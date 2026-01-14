
from app.core.sheets_db import SheetsDB
from app.models.models_db import User

def check():
    db = SheetsDB()
    users = db.query(User).all()
    print(f"Total users found: {len(users)}")
    for u in users:
        print(f"User: {u.username}, Role: {u.role}, HashExists: {bool(u.password_hash)}")

if __name__ == "__main__":
    check()
