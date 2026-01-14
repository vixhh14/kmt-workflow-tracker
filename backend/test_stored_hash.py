import bcrypt

# The hash from your Google Sheets
stored_hash = "$2b$12$LQv3c1yqBwo/sVDwjDjinOSeRt9YJUBv7cPJmqjIHc7fKlMC8pFm"

# Test passwords
test_passwords = [
    "Admin@Demo2025!",
    "admin",
    "Admin",
    "password",
    "demo",
]

print("=" * 80)
print("🔍 TESTING STORED HASH")
print("=" * 80)
print(f"\nStored hash: {stored_hash}")
print(f"Hash length: {len(stored_hash)} characters (should be 60)")
print("\nTesting passwords:")
print("-" * 80)

for pwd in test_passwords:
    try:
        result = bcrypt.checkpw(pwd.encode('utf-8'), stored_hash.encode('utf-8'))
        status = "✅ MATCH!" if result else "❌ No match"
        print(f"{status:15} | {pwd}")
        
        if result:
            print("\n" + "=" * 80)
            print(f"🎉 SUCCESS! The password is: {pwd}")
            print("=" * 80)
            break
    except Exception as e:
        print(f"❌ Error testing '{pwd}': {e}")
        break

print("\n" + "=" * 80)
print("💡 If no password matched, the hash might be incomplete or corrupted.")
print("   A valid bcrypt hash should be exactly 60 characters long.")
print("=" * 80)
