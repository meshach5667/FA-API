#!/usr/bin/env python3
"""
Simple test for admin login
"""
import requests
import json

try:
    print("Testing admin login...")
    response = requests.post(
        'http://localhost:8000/admin/login',
        data={'username': 'admin@fitaccess.com', 'password': 'admin123'},
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token', '')
        print("✅ Login successful!")
        print(f"Token: {token[:50]}...")
        
        # Test dashboard stats with the token
        print("\nTesting dashboard stats...")
        headers = {'Authorization': f'Bearer {token}'}
        stats_response = requests.get('http://localhost:8000/admin/dashboard/stats', headers=headers, timeout=10)
        print(f"Dashboard Stats Status: {stats_response.status_code}")
        
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print("✅ Dashboard stats retrieved!")
            print(f"Total Users: {stats_data.get('total_users', 'N/A')}")
            print(f"Total Revenue: {stats_data.get('total_revenue', 'N/A')}")
        else:
            print(f"❌ Dashboard stats failed: {stats_response.text}")
            
    else:
        print(f"❌ Login failed: {response.text}")
        
except requests.exceptions.Timeout:
    print("❌ Request timed out")
except Exception as e:
    print(f"❌ Error: {e}")
