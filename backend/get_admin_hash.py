import bcrypt

# Generate ONE hash for admin
password = "Admin@Demo2025!"
hash_result = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
hash_str = hash_result.decode('utf-8')

print("\n" + "=" * 80)
print("COPY THIS HASH FOR ADMIN USER")
print("=" * 80)
print(hash_str)
print("=" * 80)
print(f"\nHash length: {len(hash_str)} characters")
print(f"Password: {password}")
print("\nPaste this into cell G2 (admin's password_hash) in your Google Sheets")
print("=" * 80)
