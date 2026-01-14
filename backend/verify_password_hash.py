#!/usr/bin/env python3
"""
Verify what password matches the stored hash
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_hash():
    """Test various passwords against the stored hash"""
    from app.core.auth_utils import verify_password
    
    # The hash from your screenshot
    stored_hash = "$2b$12$LQv3c1yqBwo/sVDwjDjinOSeRt9YJUBv7cPJmqjIHc7fKlMC8pFm"
    
    # Test passwords
    test_passwords = [
        "Admin@Demo2025!",
        "admin@demo2025!",
        "ADMIN@DEMO2025!",
        "Operator@Demo2025!",
        "operator@demo2025!",
        "Supervisor@Demo2025!",
        "Planning@Demo2025!",
        "File@Demo2025!",
        "Fab@Demo2025!",
        "password",
        "admin",
        "Admin",
        "demo",
        "Demo2025",
    ]
    
    print("🔍 Testing passwords against stored hash...")
    print(f"Hash: {stored_hash}")
    print("=" * 80)
    
    for pwd in test_passwords:
        try:
            result = verify_password(pwd, stored_hash)
            status = "✅ MATCH!" if result else "❌ No match"
            print(f"{status:15} | {pwd}")
            
            if result:
                print("\n" + "=" * 80)
                print(f"🎉 FOUND IT! The password is: {pwd}")
                print("=" * 80)
                return pwd
        except Exception as e:
            print(f"❌ Error testing '{pwd}': {e}")
    
    print("\n❌ None of the test passwords matched!")
    print("\n💡 The hash might have been generated with a different password.")
    print("   Let me generate a new hash for 'Admin@Demo2025!'...")
    
    from app.core.auth_utils import hash_password
    new_hash = hash_password("Admin@Demo2025!")
    print(f"\n🔐 New hash for 'Admin@Demo2025!': {new_hash}")
    print(f"📋 Stored hash:                      {stored_hash}")
    print(f"   Match: {new_hash == stored_hash}")

if __name__ == "__main__":
    try:
        verify_hash()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
