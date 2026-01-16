from app.core.database import get_sheets_db
from app.models.models_db import User

db = get_sheets_db()
users = db.query(User).all()
print(f"Total users found: {len(users)}")
for u in users:
    print(f"User: {u.username}, Role: {u.role}, Status: {u.approval_status}, Deleted: {u.is_deleted}")
