#!/usr/bin/env python3
"""
Quick test - verify password without Google Sheets
"""
import bcrypt

# The hash from your screenshot (might be truncated)
stored_hash = "$2b$12$LQv3c1yqBwo/sVDwjDjinOSeRt9YJUBv7cPJmqjIHc7fKlMC8pFm"

# Test passwords
test_passwords = [
    "Admin@Demo2025!",
    "Operator@Demo2025!",
    "Supervisor@Demo2025!",
    "Planning@Demo2025!",
    "File@Demo2025!",
    "Fab@Demo2025!",
]

print("🔍 Quick password verification test")
print("=" * 80)
print(f"Hash: {stored_hash}")
print(f"Hash length: {len(stored_hash)}")
print("=" * 80)

for pwd in test_passwords:
    try:
        password_bytes = pwd.encode('utf-8')
        hash_bytes = stored_hash.encode('utf-8')
        result = bcrypt.checkpw(password_bytes, hash_bytes)
        status = "✅ MATCH!" if result else "❌ No match"
        print(f"{status:15} | {pwd}")
        
        if result:
            print("\n" + "=" * 80)
            print(f"🎉 FOUND IT! The correct password is: {pwd}")
            print("=" * 80)
            break
    except Exception as e:
        print(f"❌ Error: {e}")
        break

print("\n💡 Generating fresh hash for 'Admin@Demo2025!'...")
fresh_hash = bcrypt.hashpw("Admin@Demo2025!".encode('utf-8'), bcrypt.gensalt())
print(f"Fresh hash: {fresh_hash.decode('utf-8')}")
print(f"Stored hash: {stored_hash}")
