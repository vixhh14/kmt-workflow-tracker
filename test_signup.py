"""
Test signup endpoint directly
"""
import requests
import json

# Test if backend is running
try:
    response = requests.get('http://localhost:8000/')
    print(f"✅ Backend is running: {response.json()}")
except Exception as e:
    print(f"❌ Backend is NOT running: {e}")
    print("Please start backend with: uvicorn app.main:app --reload")
    exit(1)

# Test signup
print("\n" + "="*60)
print("Testing signup endpoint...")
print("="*60)

signup_data = {
    "username": "testoperator",
    "password": "test123",
    "full_name": "Test Operator"
}

try:
    response = requests.post(
        'http://localhost:8000/auth/signup',
        json=signup_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n✅ Signup SUCCESS!")
    else:
        print(f"\n❌ Signup FAILED!")
        print(f"Error: {response.json().get('detail', 'Unknown error')}")
        
except Exception as e:
    print(f"\n❌ Request failed: {e}")
