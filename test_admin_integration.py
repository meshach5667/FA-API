#!/usr/bin/env python3
"""
FitAccess Admin Integration Test Script
This script tests all the admin API endpoints to ensure proper integration
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@fitaccess.com"
ADMIN_PASSWORD = "admin123"

class AdminAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.token = None
        self.headers = {}
    
    def authenticate(self):
        """Authenticate admin user and get token"""
        print("🔑 Authenticating admin user...")
        
        login_data = {
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/admin/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoints"""
        print("\\n📊 Testing Dashboard Statistics...")
        
        endpoints = [
            "/admin/stats/overview",
            "/admin/stats/users",
            "/admin/analytics/overview",
            "/admin/analytics/users",
            "/admin/analytics/revenue"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    print(f"✅ {endpoint} - OK")
                    # Print sample data
                    data = response.json()
                    print(f"   Sample data: {json.dumps(data, indent=2)[:200]}...")
                else:
                    print(f"❌ {endpoint} - Error: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} - Exception: {str(e)}")
    
    def test_user_management(self):
        """Test user management endpoints"""
        print("\\n👥 Testing User Management...")
        
        # Test get users
        try:
            response = self.session.get(
                f"{self.base_url}/admin/users",
                headers=self.headers,
                params={"limit": 5}
            )
            
            if response.status_code == 200:
                print("✅ Get users - OK")
                users = response.json()
                print(f"   Found {len(users)} users")
                
                if users:
                    # Test user details
                    user_id = users[0]["id"]
                    detail_response = self.session.get(
                        f"{self.base_url}/admin/users/{user_id}",
                        headers=self.headers
                    )
                    if detail_response.status_code == 200:
                        print("✅ Get user details - OK")
                    else:
                        print(f"❌ Get user details - Error: {detail_response.status_code}")
                    
                    # Test user history
                    history_response = self.session.get(
                        f"{self.base_url}/admin/users/{user_id}/history",
                        headers=self.headers
                    )
                    if history_response.status_code == 200:
                        print("✅ Get user history - OK")
                    else:
                        print(f"❌ Get user history - Error: {history_response.status_code}")
            else:
                print(f"❌ Get users - Error: {response.status_code}")
        except Exception as e:
            print(f"❌ User management error: {str(e)}")
    
    def test_transaction_management(self):
        """Test transaction management endpoints"""
        print("\\n💰 Testing Transaction Management...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/transactions",
                headers=self.headers,
                params={"limit": 5}
            )
            
            if response.status_code == 200:
                print("✅ Get transactions - OK")
                transactions = response.json()
                print(f"   Found {len(transactions)} transactions")
            else:
                print(f"❌ Get transactions - Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Transaction management error: {str(e)}")
    
    def test_reward_management(self):
        """Test reward management endpoints"""
        print("\\n🎁 Testing Reward Management...")
        
        # Test get rewards
        try:
            response = self.session.get(
                f"{self.base_url}/admin/rewards",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ Get rewards - OK")
                rewards = response.json()
                print(f"   Found {len(rewards)} rewards")
            else:
                print(f"❌ Get rewards - Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Reward management error: {str(e)}")
        
        # Test create reward
        try:
            new_reward = {
                "title": "Test Reward",
                "description": "Test reward for API testing",
                "points_required": 100,
                "is_active": True
            }
            
            response = self.session.post(
                f"{self.base_url}/admin/rewards",
                headers=self.headers,
                json=new_reward
            )
            
            if response.status_code == 200:
                print("✅ Create reward - OK")
                reward = response.json()
                reward_id = reward["id"]
                
                # Test update reward
                update_data = {"title": "Updated Test Reward"}
                update_response = self.session.put(
                    f"{self.base_url}/admin/rewards/{reward_id}",
                    headers=self.headers,
                    json=update_data
                )
                
                if update_response.status_code == 200:
                    print("✅ Update reward - OK")
                else:
                    print(f"❌ Update reward - Error: {update_response.status_code}")
                
                # Clean up - delete test reward
                delete_response = self.session.delete(
                    f"{self.base_url}/admin/rewards/{reward_id}",
                    headers=self.headers
                )
                if delete_response.status_code == 200:
                    print("✅ Delete reward - OK")
            else:
                print(f"❌ Create reward - Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Reward CRUD error: {str(e)}")
    
    def test_community_management(self):
        """Test community management endpoints"""
        print("\\n🏘️ Testing Community Management...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/communities",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ Get communities - OK")
                communities = response.json()
                print(f"   Found {len(communities)} communities")
            else:
                print(f"❌ Get communities - Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Community management error: {str(e)}")
    
    def test_business_management(self):
        """Test business management endpoints"""
        print("\\n🏢 Testing Business Management...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/businesses",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ Get businesses - OK")
                businesses = response.json()
                print(f"   Found {len(businesses)} businesses")
                
                if businesses:
                    # Test business details
                    business_id = businesses[0]["id"]
                    detail_response = self.session.get(
                        f"{self.base_url}/admin/businesses/{business_id}",
                        headers=self.headers
                    )
                    if detail_response.status_code == 200:
                        print("✅ Get business details - OK")
                    else:
                        print(f"❌ Get business details - Error: {detail_response.status_code}")
            else:
                print(f"❌ Get businesses - Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Business management error: {str(e)}")
    
    def test_notification_management(self):
        """Test notification management endpoints"""
        print("\\n🔔 Testing Notification Management...")
        
        try:
            # Test get notifications
            response = self.session.get(
                f"{self.base_url}/admin/notifications",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ Get notifications - OK")
            else:
                print(f"❌ Get notifications - Error: {response.status_code}")
            
            # Test send broadcast
            broadcast_data = {
                "title": "Test Broadcast",
                "message": "This is a test broadcast message"
            }
            
            broadcast_response = self.session.post(
                f"{self.base_url}/admin/broadcast/send",
                headers=self.headers,
                json=broadcast_data
            )
            
            if broadcast_response.status_code == 200:
                print("✅ Send broadcast - OK")
            else:
                print(f"❌ Send broadcast - Error: {broadcast_response.status_code}")
                
        except Exception as e:
            print(f"❌ Notification management error: {str(e)}")
    
    def test_system_health(self):
        """Test system health endpoints"""
        print("\\n🏥 Testing System Health...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/admin/system/health",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ System health - OK")
                health = response.json()
                print(f"   Status: {health['status']}")
                print(f"   Database: {health['database']}")
            else:
                print(f"❌ System health - Error: {response.status_code}")
        except Exception as e:
            print(f"❌ System health error: {str(e)}")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting FitAccess Admin API Integration Tests")
        print(f"   Base URL: {self.base_url}")
        print(f"   Admin Email: {ADMIN_EMAIL}")
        print("=" * 60)
        
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Run all test suites
        self.test_dashboard_stats()
        self.test_user_management()
        self.test_transaction_management()
        self.test_reward_management()
        self.test_community_management()
        self.test_business_management()
        self.test_notification_management()
        self.test_system_health()
        
        print("\\n" + "=" * 60)
        print("🎉 Integration tests completed!")
        return True

def main():
    """Main function"""
    tester = AdminAPITester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
