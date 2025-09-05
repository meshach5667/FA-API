#!/usr/bin/env python3

import requests
import json

# Test admin endpoints
base_url = "http://localhost:8000"

# First, let's try to login as admin (we need a token)
admin_login_data = {
    "username": "admin@fitaccess.com",  # You'll need to create this admin
    "password": "admin123"
}

print("Testing admin endpoints...")

# Test endpoints without authentication first to see the responses
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
        response = requests.get(f"{base_url}{endpoint}")
        print(f"\n{endpoint}: Status {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error testing {endpoint}: {e}")

print("\nTest completed.")
