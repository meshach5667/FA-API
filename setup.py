#!/usr/bin/env python3
"""
Setup script for FitAccess Admin Backend
This script creates the database tables and an initial admin user
"""

import sys
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.db.database import engine, Base, get_db
from app.models import user, center, check_in, check_out, advertisement, payment, business, admin, token
from app.models.admin import Admin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")

def create_admin_user():
    """Create an initial admin user"""
    db = next(get_db())
    
    # Check if admin already exists
    existing_admin = db.query(Admin).filter(Admin.email == "admin@fitaccess.com").first()
    if existing_admin:
        print("✓ Admin user already exists!")
        return
    
    # Create admin user
    admin_user = Admin(
        email="admin@fitaccess.com",
        full_name="FitAccess Admin",
        hashed_password=pwd_context.hash("admin123"),
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.close()
    
    print("✓ Admin user created successfully!")
    print("  Email: admin@fitaccess.com")
    print("  Password: admin123")
    print("  Please change this password after first login!")

def main():
    """Main setup function"""
    print("🚀 Setting up FitAccess Admin Backend...")
    
    try:
        # Create database tables
        create_tables()
        
        # Create initial admin user
        create_admin_user()
        
        print("\n✅ Setup completed successfully!")
        print("\nYou can now:")
        print("1. Start the backend server: uvicorn app.main:app --reload")
        print("2. Login to the admin panel with the credentials above")
        print("3. Start creating advertisements and managing the platform")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
