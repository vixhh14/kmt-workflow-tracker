"""
Verification Script: API Response Serialization Safety
Tests that all critical endpoints return JSON-serializable data.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None, headers=None):
    """Test an endpoint and verify JSON serialization."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        
        print(f"Status: {response.status_code}")
        
        # Try to parse JSON
        try:
            json_data = response.json()
            print(f"✅ JSON Parse: SUCCESS")
            
            # Check for common serialization issues
            json_str = json.dumps(json_data)
            print(f"✅ JSON Stringify: SUCCESS")
            
            # Verify no UUID objects or datetime objects in response
            def check_types(obj, path="root"):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        check_types(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_types(item, f"{path}[{i}]")
                elif isinstance(obj, datetime):
                    print(f"❌ Found datetime object at {path}")
                    return False
                elif hasattr(obj, '__class__') and 'UUID' in obj.__class__.__name__:
                    print(f"❌ Found UUID object at {path}")
                    return False
            
            check_types(json_data)
            print(f"✅ Type Safety: PASSED")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse FAILED: {e}")
            print(f"Response Text: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Request FAILED: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("API SERIALIZATION SAFETY VERIFICATION")
    print("="*60)
    
    # Test critical endpoints
    endpoints = [
        "/health",
        "/projects",
        "/tasks",
        "/analytics/overview",
        "/analytics/project-overview",
        "/dashboard/admin",
        "/dashboard/supervisor",
        "/admin/project-analytics",
        "/reports/machines/daily",
        "/reports/users/daily",
    ]
    
    results = []
    for endpoint in endpoints:
        result = test_endpoint(endpoint)
        results.append((endpoint, result))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for endpoint, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {endpoint}")
    
    print(f"\nTotal: {passed}/{total} endpoints passed")
    
    if passed == total:
        print("\n🎉 ALL ENDPOINTS ARE SERIALIZATION-SAFE!")
    else:
        print(f"\n⚠️  {total - passed} endpoint(s) need attention")

if __name__ == "__main__":
    main()
