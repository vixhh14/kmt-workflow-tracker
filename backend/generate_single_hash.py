import bcrypt

# Generate hash for admin password
password = "Admin@Demo2025!"
hash_result = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
hash_str = hash_result.decode('utf-8')

print("\n" + "=" * 80)
print("🔐 PASSWORD HASH FOR ADMIN")
print("=" * 80)
print(f"\nPassword: {password}")
print(f"\nHash (copy this entire line):")
print(hash_str)
print(f"\nHash length: {len(hash_str)} characters")
print("\n" + "=" * 80)
print("\n📋 INSTRUCTIONS:")
print("1. Copy the hash above (the long string starting with $2b$12$)")
print("2. Open your Google Sheets")
print("3. Find the 'admin' user row")
print("4. Paste this hash into column G (password_hash)")
print("5. Make sure column I (approval_status) = 'approved'")
print("6. Make sure column J (is_deleted) = 'FALSE'")
print("7. Try logging in with:")
print(f"   Username: admin")
print(f"   Password: {password}")
print("=" * 80)
