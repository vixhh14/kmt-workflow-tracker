import os
import requests
from dotenv import load_dotenv

load_dotenv('.env.production')

BASE_URL = "http://localhost:8000"  # Assuming backend is running locally on port 8000
# If testing against production, change to your Render URL

users = {
    'admin': 'Admin@Demo2025!',
    'operator': 'Operator@Demo2025!',
    'supervisor': 'Supervisor@Demo2025!',
    'planning': 'Planning@Demo2025!'
}

print(f"Testing login against {BASE_URL}...")

for username, password in users.items():
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"✅ Login SUCCESS for {username}")
            token = response.json().get("access_token")
            print(f"   Token: {token[:20]}...")
        else:
            print(f"❌ Login FAILED for {username}: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing {username}: {e}")
