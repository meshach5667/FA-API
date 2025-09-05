#!/usr/bin/env python3
"""
Script to create an admin user for the FitAccess admin dashboard
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.admin import Admin
from passlib.context import CryptContext

def create_admin():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create password context
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    # Create session
    db = SessionLocal()

    try:
        # Check existing admins
        admins = db.query(Admin).all()
        print(f'Existing admins: {len(admins)}')
        for admin in admins:
            print(f'  - {admin.email} ({admin.full_name})')

        # Create a test admin if none exists
        if not admins:
            print('Creating test admin...')
            hashed_password = pwd_context.hash('admin123')
            test_admin = Admin(
                email='admin@fitaccess.com',
                full_name='Test Admin',
                hashed_password=hashed_password,
                is_active=True
            )
            db.add(test_admin)
            db.commit()
            db.refresh(test_admin)
            print(f'Test admin created: {test_admin.email} / admin123')
        else:
            print('Admin accounts already exist')
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
