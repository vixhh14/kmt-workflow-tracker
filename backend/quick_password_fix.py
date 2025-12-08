"""
Quick Password Migration - Non-interactive version
"""
import sys
import os
import secrets
import string

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models_db import User
from app.core.auth_utils import hash_password


def generate_secure_password(length=12):
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*"
    
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    
    all_chars = uppercase + lowercase + digits + special
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    
    return ''.join(password_list)


def migrate_now():
    # Fixed secure passwords so we can share them with the user
    # These meet all security requirements (8+ chars, Upper, Lower, Digit, Special)
    fixed_passwords = {
        'admin': 'Admin@Secure2024!',
        'operator': 'Operator#Safe99',
        'supervisor': 'Super$Visor88',
        'planning': 'Plan%Ning77'
    }
    
    demo_usernames = ['admin', 'operator', 'supervisor', 'planning']
    
    print("=" * 60)
    print("UPDATING DEMO USER PASSWORDS")
    print("=" * 60)
    
    db = SessionLocal()
    credentials = []
    
    try:
        for username in demo_usernames:
            user = db.query(User).filter(User.username == username).first()
            
            if user:
                # Use fixed secure password
                new_password = fixed_passwords.get(username, generate_secure_password())
                
                user.password_hash = hash_password(new_password)
                credentials.append((username, new_password, user.role))
                print(f"Updated: {username}")
            else:
                print(f"Not found: {username}")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("NEW CREDENTIALS - SAVE THESE NOW!")
        print("=" * 60)
        
        # Write to file for the agent to read
        with open("new_credentials.txt", "w") as f:
            f.write("NEW CREDENTIALS - SAVE THESE NOW!\n")
            f.write("============================================================\n")
            for username, password, role in credentials:
                f.write(f"Username: {username}\n")
                f.write(f"Password: {password}\n")
                f.write(f"Role:     {role}\n")
                f.write("------------------------------------------------------------\n")
                
                # Also print to console
                print(f"\nUsername: {username}")
                print(f"Password: {password}")
                print(f"Role:     {role}")
        
        print("\n" + "=" * 60)
        print(f"DONE! Credentials saved to {os.path.abspath('new_credentials.txt')}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    migrate_now()
