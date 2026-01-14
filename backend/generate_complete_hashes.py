import bcrypt

print("=" * 80)
print("🔐 GENERATING FRESH PASSWORD HASHES")
print("=" * 80)

users_passwords = {
    "admin": "Admin@Demo2025!",
    "operator": "Operator@Demo2025!",
    "supervisor": "Supervisor@Demo2025!",
    "planning": "Planning@Demo2025!",
    "file_master": "File@Demo2025!",
    "fab_master": "Fab@Demo2025!",
}

print("\n📋 COPY THESE HASHES TO YOUR GOOGLE SHEETS:")
print("=" * 80)

for username, password in users_passwords.items():
    hash_result = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hash_str = hash_result.decode('utf-8')
    
    print(f"\n{username.upper()}:")
    print(f"  Password: {password}")
    print(f"  Hash ({len(hash_str)} chars): {hash_str}")
    
    # Verify it works
    test = bcrypt.checkpw(password.encode('utf-8'), hash_str.encode('utf-8'))
    print(f"  Verified: {'✅ YES' if test else '❌ NO'}")

print("\n" + "=" * 80)
print("📝 INSTRUCTIONS:")
print("1. Copy each hash above")
print("2. Paste into column G (password_hash) in your Google Sheets")
print("3. Make sure the ENTIRE hash is copied (should be exactly 60 characters)")
print("4. Verify column I (approval_status) = 'approved'")
print("5. Verify column J (is_deleted) = 'FALSE'")
print("=" * 80)
