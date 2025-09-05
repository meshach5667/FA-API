#!/usr/bin/env python3
"""
Test script for admin endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_admin_login():
    """Test admin login"""
    response = requests.post(f"{BASE_URL}/admin/login", 
                           data={'username': 'admin@fitaccess.com', 'password': 'admin123'})
    if response.status_code == 200:
        token = response.json()['access_token']
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_dashboard_stats(token):
    """Test dashboard stats endpoint"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BASE_URL}/admin/dashboard/stats", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✅ Dashboard stats retrieved successfully")
        print(f"   Total Users: {data.get('total_users', 'N/A')}")
        print(f"   Total Revenue: {data.get('total_revenue', 'N/A')}")
        return True
    else:
        print(f"❌ Dashboard stats failed: {response.text}")
        return False

def test_users_stats(token):
    """Test users stats endpoint"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BASE_URL}/admin/users/stats", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✅ Users stats retrieved successfully")
        print(f"   Active Users: {data.get('active_users', 'N/A')}")
        print(f"   Paid Users: {data.get('paid_users', 'N/A')}")
        return True
    else:
        print(f"❌ Users stats failed: {response.text}")
        return False

def test_system_health(token):
    """Test system health endpoint"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BASE_URL}/admin/system/health", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✅ System health retrieved successfully")
        print(f"   Database: {data.get('database', 'N/A')}")
        print(f"   Status: {data.get('status', 'N/A')}")
        return True
    else:
        print(f"❌ System health failed: {response.text}")
        return False

def main():
    print("🚀 Testing Admin API Endpoints...")
    print("-" * 40)
    
    # Test login
    token = test_admin_login()
    if not token:
        print("❌ Cannot proceed without valid token")
        return
    
    print("-" * 40)
    
    # Test various endpoints
    test_dashboard_stats(token)
    test_users_stats(token)
    test_system_health(token)
    
    print("-" * 40)
    print("✅ Admin API testing complete!")

if __name__ == "__main__":
    main()
