from app.core.hashing import pwd_context
users = {
    'admin': 'Admin@Demo2025!',
    'operator': 'Operator@Demo2025!',
    'supervisor': 'Supervisor@Demo2025!',
    'planning': 'Planning@Demo2025!'
}
for u, p in users.items():
    print(f"{u}:{pwd_context.hash(p)}")
