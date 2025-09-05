#!/usr/bin/env python3

import requests
import json

# Test admin endpoints with authentication
base_url = "http://localhost:8000"

# First, login to get a token
print("Logging in as admin...")
login_data = {
    "username": "admin@fitaccess.com",
    "password": "admin123"
}

# Use form data for login
login_response = requests.post(
    f"{base_url}/admin/login",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

print(f"Login response: {login_response.status_code}")
print(f"Response: {login_response.text}")

if login_response.status_code == 200:
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # Create headers with the token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\nAccess token obtained: {access_token[:50]}...")
    print("\nTesting admin endpoints with authentication...")
    
    # Test endpoints with authentication
    endpoints_to_test = [
        "/admin/dashboard/stats",
        "/admin/system/health", 
        "/admin/businesses?limit=100",
        "/admin/users/stats",
        "/admin/analytics/revenue?period=today",
        "/admin/communities/all?limit=100"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"\n{endpoint}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Data: {json.dumps(data, indent=2, default=str)[:200]}...")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error testing {endpoint}: {e}")
else:
    print("Failed to login. Cannot test authenticated endpoints.")

print("\nTest completed.")
