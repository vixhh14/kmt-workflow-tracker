import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123" 

def get_admin_token(f):
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            f.write(f"Failed to login as admin: {response.status_code} - {response.text}\n")
            return None
    except Exception as e:
        f.write(f"Error connecting to backend: {e}\n")
        return None

def check_pending_users_endpoint(token, f):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/admin/pending-users", headers=headers)
        
        f.write(f"Status Code: {response.status_code}\n")
        if response.status_code == 200:
            f.write("Response Body:\n")
            f.write(str(response.json()) + "\n")
        else:
            f.write("Error Response:\n")
            f.write(response.text + "\n")
            
    except Exception as e:
        f.write(f"Error calling endpoint: {e}\n")

if __name__ == "__main__":
    with open('test_endpoint_output.txt', 'w') as f:
        f.write("1. Getting Admin Token...\n")
        token = get_admin_token(f)
        
        if token:
            f.write("\n2. Checking /admin/pending-users endpoint...\n")
            check_pending_users_endpoint(token, f)
        else:
            f.write("Skipping endpoint check due to login failure.\n")
