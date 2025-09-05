#!/usr/bin/env python3
"""
Script to create a super admin user for the FitAccess admin dashboard
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.admin import Admin, AdminRole, AdminStatus
from passlib.context import CryptContext
from datetime import datetime

def create_super_admin():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create password context
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    # Create session
    db = SessionLocal()

    try:
        # Check existing super admins
        super_admins = db.query(Admin).filter(Admin.role == AdminRole.SUPER_ADMIN).all()
        print(f'Existing super admins: {len(super_admins)}')
        for admin in super_admins:
            print(f'  - {admin.email} ({admin.full_name}) - Status: {admin.status}')

        # Create a super admin if none exists
        if not super_admins:
            print('Creating super admin...')
            hashed_password = pwd_context.hash('superadmin123')
            super_admin = Admin(
                email='superadmin@fitaccess.com',
                username='superadmin',
                full_name='Super Administrator',
                hashed_password=hashed_password,
                role=AdminRole.SUPER_ADMIN,
                status=AdminStatus.APPROVED,
                is_active=True,
                approved_by=None,  # Self-approved
                approved_at=datetime.utcnow()
            )
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)
            print(f'Super admin created: {super_admin.email} / superadmin123')
            print(f'Role: {super_admin.role}, Status: {super_admin.status}')
            print(f'Initials: {super_admin.get_initials()}')
        else:
            print('Super admin accounts already exist')
            
        # Show all admins
        all_admins = db.query(Admin).all()
        print(f'\nAll admin accounts ({len(all_admins)}):')
        for admin in all_admins:
            print(f'  - {admin.email} | {admin.full_name} | {admin.role} | {admin.status} | Initials: {admin.get_initials()}')
            
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()
