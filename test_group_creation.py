#!/usr/bin/env python3
"""
Test script to verify that group creation works after fixing database permissions.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.db.database import SessionLocal, engine
from sqlalchemy import text

def test_database_connection():
    """Test basic database connection and write permissions"""
    print("Testing database connection...")
    
    try:
        db = SessionLocal()
        
        # Test a simple query
        result = db.execute(text("SELECT COUNT(*) FROM businesses")).scalar()
        print(f"Found {result} businesses in database")
        
        # Test write operation
        db.execute(text("CREATE TABLE IF NOT EXISTS test_permissions (id INTEGER PRIMARY KEY)"))
        db.execute(text("INSERT INTO test_permissions (id) VALUES (999)"))
        db.execute(text("DELETE FROM test_permissions WHERE id = 999"))
        db.execute(text("DROP TABLE test_permissions"))
        db.commit()
        
        print("✅ Database write test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        db.close()

def test_group_creation():
    """Test creating a group through SQLAlchemy ORM"""
    print("\nTesting group creation...")
    
    try:
        from app.models.group_activity import Group
        from app.models.business import Business
        
        db = SessionLocal()
        
        # Check if we have any businesses
        business = db.query(Business).first()
        if not business:
            print("No businesses found in database. Creating test business...")
            business = Business(
                business_name="Test Gym",
                email="test@example.com",
                phone="1234567890",
                address="Test Address"
            )
            db.add(business)
            db.commit()
            db.refresh(business)
        
        # Create a test group
        test_group = Group(
            business_id=business.id,
            name='Database Test Group',
            description='Testing database write permissions',
            category='testing',
            is_private=False,
            max_members=5,
            status='active'
        )
        
        db.add(test_group)
        db.commit()
        db.refresh(test_group)
        
        print(f"✅ Successfully created group with ID: {test_group.id}")
        
        # Clean up
        db.delete(test_group)
        db.commit()
        print("✅ Test group cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Group creation test failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Testing database write permissions fix...\n")
    
    success = True
    success &= test_database_connection()
    success &= test_group_creation()
    
    if success:
        print("\n🎉 All tests passed! The database permissions issue has been fixed.")
        print("You should now be able to create groups through the API.")
    else:
        print("\n💥 Some tests failed. Please check the error messages above.")
    
    sys.exit(0 if success else 1)
