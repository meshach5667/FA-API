#!/usr/bin/env python3

import requests
import json

# Test the new role-based admin system
base_url = "http://localhost:8000"

print("=== Testing Role-Based Admin System ===\n")

# Test 1: Super Admin Login
print("1. Testing Super Admin Login...")
login_data = {
    "username": "superadmin@fitaccess.com",
    "password": "superadmin123"
}

login_response = requests.post(
    f"{base_url}/admin/login",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

print(f"Login Status: {login_response.status_code}")
if login_response.status_code == 200:
    token_data = login_response.json()
    super_admin_token = token_data["access_token"]
    admin_info = token_data.get("admin", {})
    
    print(f"✅ Super Admin Login Successful")
    print(f"Admin Info: {json.dumps(admin_info, indent=2)}")
    
    super_admin_headers = {
        "Authorization": f"Bearer {super_admin_token}",
        "Content-Type": "application/json"
    }
    
    # Test 2: Get current admin info
    print("\n2. Testing Get Current Admin Info...")
    me_response = requests.get(f"{base_url}/admin/me", headers=super_admin_headers)
    print(f"Status: {me_response.status_code}")
    if me_response.status_code == 200:
        print(f"✅ Admin Info: {json.dumps(me_response.json(), indent=2, default=str)}")
    
    # Test 3: Register a new admin (should be pending)
    print("\n3. Testing New Admin Registration...")
    new_admin_data = {
        "email": "testadmin@fitaccess.com",
        "username": "testadmin",
        "full_name": "Test Administrator",
        "password": "testadmin123",
        "role": "admin"
    }
    
    register_response = requests.post(
        f"{base_url}/admin/register",
        json=new_admin_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Registration Status: {register_response.status_code}")
    if register_response.status_code == 200:
        new_admin = register_response.json()
        print(f"✅ New Admin Registered: {json.dumps(new_admin, indent=2, default=str)}")
        new_admin_id = new_admin["id"]
        
        # Test 4: Try to login with pending admin (should fail)
        print("\n4. Testing Pending Admin Login (should fail)...")
        pending_login_data = {
            "username": "testadmin@fitaccess.com",
            "password": "testadmin123"
        }
        
        pending_login_response = requests.post(
            f"{base_url}/admin/login",
            data=pending_login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Pending Login Status: {pending_login_response.status_code}")
        if pending_login_response.status_code != 200:
            print(f"✅ Correctly blocked pending admin: {pending_login_response.json()}")
        
        # Test 5: Get pending admins (super admin only)
        print("\n5. Testing Get Pending Admins...")
        pending_response = requests.get(f"{base_url}/admin/management/admins/pending", headers=super_admin_headers)
        print(f"Status: {pending_response.status_code}")
        if pending_response.status_code == 200:
            pending_admins = pending_response.json()
            print(f"✅ Pending Admins: {json.dumps(pending_admins, indent=2, default=str)}")
        
        # Test 6: Approve the admin
        print("\n6. Testing Admin Approval...")
        approve_response = requests.post(
            f"{base_url}/admin/management/admins/{new_admin_id}/approve",
            params={"action": "approve", "notes": "Approved by super admin"},
            headers=super_admin_headers
        )
        print(f"Approval Status: {approve_response.status_code}")
        if approve_response.status_code == 200:
            print(f"✅ Admin Approved: {json.dumps(approve_response.json(), indent=2, default=str)}")
            
            # Test 7: Try to login with approved admin (should work)
            print("\n7. Testing Approved Admin Login...")
            approved_login_response = requests.post(
                f"{base_url}/admin/login",
                data=pending_login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            print(f"Approved Login Status: {approved_login_response.status_code}")
            if approved_login_response.status_code == 200:
                approved_token_data = approved_login_response.json()
                print(f"✅ Approved Admin Login Successful: {json.dumps(approved_token_data.get('admin', {}), indent=2)}")
                
                # Test regular admin permissions
                approved_admin_token = approved_token_data["access_token"]
                approved_admin_headers = {
                    "Authorization": f"Bearer {approved_admin_token}",
                    "Content-Type": "application/json"
                }
                
                # Test 8: Regular admin accessing dashboard (should work)
                print("\n8. Testing Regular Admin Dashboard Access...")
                dashboard_response = requests.get(f"{base_url}/admin/dashboard/stats", headers=approved_admin_headers)
                print(f"Dashboard Status: {dashboard_response.status_code}")
                if dashboard_response.status_code == 200:
                    print(f"✅ Regular Admin Dashboard Access: Success")
                
                # Test 9: Regular admin trying to access management (should fail)
                print("\n9. Testing Regular Admin Management Access (should fail)...")
                mgmt_response = requests.get(f"{base_url}/admin/management/admins", headers=approved_admin_headers)
                print(f"Management Status: {mgmt_response.status_code}")
                if mgmt_response.status_code == 403:
                    print(f"✅ Correctly blocked regular admin from management: {mgmt_response.json()}")
        
        # Test 10: Get admin management stats (super admin only)
        print("\n10. Testing Admin Management Stats...")
        stats_response = requests.get(f"{base_url}/admin/management/stats", headers=super_admin_headers)
        print(f"Stats Status: {stats_response.status_code}")
        if stats_response.status_code == 200:
            print(f"✅ Admin Management Stats: {json.dumps(stats_response.json(), indent=2)}")
        
        # Test 11: Get all admins (super admin only)
        print("\n11. Testing Get All Admins...")
        all_admins_response = requests.get(f"{base_url}/admin/management/admins", headers=super_admin_headers)
        print(f"All Admins Status: {all_admins_response.status_code}")
        if all_admins_response.status_code == 200:
            all_admins = all_admins_response.json()
            print(f"✅ All Admins: {len(all_admins)} admins found")
            for admin in all_admins:
                print(f"  - {admin['email']} | {admin['full_name']} | {admin['role']} | {admin['status']} | Initials: {admin.get('initials', 'N/A')}")
    
else:
    print(f"❌ Super Admin Login Failed: {login_response.text}")

print("\n=== Role-Based Admin System Test Complete ===")
