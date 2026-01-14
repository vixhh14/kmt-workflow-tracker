#!/usr/bin/env python3
"""
Generate password hashes for manual update in Google Sheets
"""
import bcrypt

# User credentials
users_passwords = {
    "admin": "Admin@Demo2025!",
    "operator": "Operator@Demo2025!",
    "supervisor": "Supervisor@Demo2025!",
    "planning": "Planning@Demo2025!",
    "file_master": "File@Demo2025!",
    "fab_master": "Fab@Demo2025!",
}

print("🔐 Password Hashes for Google Sheets")
print("=" * 100)
print("\nCopy these hashes into column G (password_hash) in your Users sheet:")
print("-" * 100)

for username, password in users_passwords.items():
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    hash_str = hashed.decode('utf-8')
    
    print(f"\n{username:15} | Password: {password:25} | Hash:")
    print(f"                  {hash_str}")

print("\n" + "=" * 100)
print("\n📋 INSTRUCTIONS:")
print("1. Open your Google Sheets")
print("2. Go to the Users worksheet")
print("3. For each user, copy the hash above and paste it into column G (password_hash)")
print("4. Make sure:")
print("   - Column I (approval_status) = 'approved'")
print("   - Column J (is_deleted) = 'FALSE'")
print("   - Column E (active) = 'TRUE'")
print("\n✅ After updating, you can log in with the passwords shown above!")
