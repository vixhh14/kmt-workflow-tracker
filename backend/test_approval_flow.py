from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.models_db import User, UserApproval
import uuid

client = TestClient(app)

def test_approval_flow():
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "TestPassword123!"
    email = f"{username}@example.com"
    
    print(f"Testing with user: {username}")

    # 1. Signup
    print("\n1. Testing Signup...")
    response = client.post("/auth/signup", json={
        "username": username,
        "password": password,
        "email": email,
        "full_name": "Test User",
        "contact_number": "1234567890",
        "address": "Test Address"
    })
    
    if response.status_code != 200:
        print(f"❌ Signup failed: {response.json()}")
        return
    print("✅ Signup successful")
    
    # 2. Verify Pending Status (Login attempt)
    print("\n2. Testing Login (Pending)...")
    response = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 403:
        print("✅ Login blocked as expected (403 Forbidden)")
        print(f"   Message: {response.json()['detail']}")
    else:
        print(f"❌ Login should have failed with 403, got {response.status_code}")
        return

    # 3. Admin Approval
    print("\n3. Testing Admin Approval...")
    # Need admin token first
    # Assuming there is an admin user 'admin' with password 'admin123' (demo credentials)
    # If not, we might need to create one or mock the dependency.
    # Let's try to login as admin.
    admin_login = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123" # Default demo password
    })
    
    if admin_login.status_code != 200:
        print("⚠️ Could not login as 'admin'. Skipping approval test via API.")
        print("   Please ensure 'admin' user exists.")
        return
        
    admin_token = admin_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    approve_response = client.post(f"/admin/users/{username}/approve", json={
        "unit_id": "1", # Assuming unit 1 exists or is mocked
        "machine_types": "CNC,Lathe"
    }, headers=headers)
    
    if approve_response.status_code == 200:
        print("✅ Admin approval successful")
    else:
        print(f"❌ Admin approval failed: {approve_response.json()}")
        return

    # 4. Verify Login (Approved)
    print("\n4. Testing Login (Approved)...")
    response = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 200:
        print("✅ Login successful")
        print(f"   Token: {response.json()['access_token'][:10]}...")
    else:
        print(f"❌ Login failed: {response.json()}")
        return

    print("\n🎉 End-to-End Test Passed!")

if __name__ == "__main__":
    test_approval_flow()
