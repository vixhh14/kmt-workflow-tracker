import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123" # Default demo password, might need to be updated if changed

def get_admin_token():
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Failed to login as admin: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return None

def check_pending_users_endpoint(token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/admin/pending-users", headers=headers)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response Body:")
            print(response.json())
        else:
            print("Error Response:")
            print(response.text)
            
    except Exception as e:
        print(f"Error calling endpoint: {e}")

if __name__ == "__main__":
    print("1. Getting Admin Token...")
    token = get_admin_token()
    
    if token:
        print("\n2. Checking /admin/pending-users endpoint...")
        check_pending_users_endpoint(token)
    else:
        print("Skipping endpoint check due to login failure.")
