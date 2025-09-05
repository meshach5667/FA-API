#!/usr/bin/env python3
"""
Script to populate test data for the FitAccess admin dashboard with initials support
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.business import Business
from app.models.payment import Payment, PaymentStatusEnum, PaymentTypeEnum
from app.models.check_in import CheckIn
from app.models.community import Community
from passlib.context import CryptContext
from datetime import datetime, timedelta
import random

def create_test_data():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create password context
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    
    # Create session
    db = SessionLocal()
    
    try:
        print("Creating test data...")
        
        # Create test users
        users_data = [
            {"name": "John Doe", "email": "john.doe@example.com", "phone": "+1234567890"},
            {"name": "Jane Smith", "email": "jane.smith@example.com", "phone": "+1234567891"},
            {"name": "Mike Johnson", "email": "mike.johnson@example.com", "phone": "+1234567892"},
            {"name": "Sarah Wilson", "email": "sarah.wilson@example.com", "phone": "+1234567893"},
            {"name": "David Brown", "email": "david.brown@example.com", "phone": "+1234567894"},
            {"name": "Lisa Garcia", "email": "lisa.garcia@example.com", "phone": "+1234567895"},
            {"name": "Robert Taylor", "email": "robert.taylor@example.com", "phone": "+1234567896"},
            {"name": "Emily Davis", "email": "emily.davis@example.com", "phone": "+1234567897"},
            {"name": "Chris Anderson", "email": "chris.anderson@example.com", "phone": "+1234567898"},
            {"name": "Maria Rodriguez", "email": "maria.rodriguez@example.com", "phone": "+1234567899"}
        ]
        
        created_users = []
        for user_data in users_data:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                hashed_password = pwd_context.hash("password123")
                user = User(
                    name=user_data["name"],
                    full_name=user_data["name"],
                    username=user_data["email"].split("@")[0],
                    email=user_data["email"],
                    phone=user_data["phone"],
                    phone_number=user_data["phone"],
                    hashed_password=hashed_password,
                    balance=random.uniform(50.0, 500.0),
                    plan=random.choice(["Free", "Basic", "Premium"]),
                    flex_credit=random.randint(0, 100),
                    is_active=True
                )
                db.add(user)
                created_users.append(user)
            else:
                created_users.append(existing_user)
        
        db.commit()
        print(f"Created {len(created_users)} users")
        
        # Create test businesses
        businesses_data = [
            {"name": "FitZone Gym", "email": "contact@fitzone.com", "address": "123 Fitness St, City A"},
            {"name": "PowerHouse Fitness", "email": "info@powerhouse.com", "address": "456 Strength Ave, City B"},
            {"name": "FlexFit Studio", "email": "hello@flexfit.com", "address": "789 Yoga Blvd, City C"},
            {"name": "Iron Paradise", "email": "admin@ironparadise.com", "address": "321 Muscle Rd, City D"},
            {"name": "CardioMax Center", "email": "support@cardiomax.com", "address": "654 Cardio St, City E"},
            {"name": "ZenFit Wellness", "email": "contact@zenfit.com", "address": "987 Wellness Way, City F"},
            {"name": "Beast Mode Gym", "email": "info@beastmode.com", "address": "147 Beast St, City G"},
            {"name": "Serenity Spa & Fitness", "email": "hello@serenity.com", "address": "258 Calm Ave, City H"}
        ]
        
        created_businesses = []
        for business_data in businesses_data:
            # Check if business already exists
            existing_business = db.query(Business).filter(Business.email == business_data["email"]).first()
            if not existing_business:
                hashed_password = pwd_context.hash("business123")
                business = Business(
                    name=business_data["name"],
                    business_name=business_data["name"],
                    email=business_data["email"],
                    phone=f"+1{random.randint(1000000000, 9999999999)}",
                    phone_number=f"+1{random.randint(1000000000, 9999999999)}",
                    address=business_data["address"],
                    password_hash=hashed_password,
                    balance=random.uniform(1000.0, 10000.0),
                    is_active=True
                )
                db.add(business)
                created_businesses.append(business)
            else:
                created_businesses.append(existing_business)
        
        db.commit()
        print(f"Created {len(created_businesses)} businesses")
        
        # Refresh all objects to get their IDs
        for user in created_users:
            db.refresh(user)
        for business in created_businesses:
            db.refresh(business)
        
        # Create test payments
        print("Creating test payments...")
        for _ in range(50):
            user = random.choice(created_users)
            business = random.choice(created_businesses)
            
            payment = Payment(
                user_id=user.id,
                business_id=business.id,
                amount=random.uniform(10.0, 200.0),
                currency="USD",
                payment_type=random.choice(list(PaymentTypeEnum)),
                status=random.choice(list(PaymentStatusEnum)),
                payment_method=random.choice(["card", "bank_transfer", "paypal"]),
                description=f"Payment for {business.name}",
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.add(payment)
        
        db.commit()
        print("Created 50 test payments")
        
        # Create test check-ins
        print("Creating test check-ins...")
        for _ in range(100):
            user = random.choice(created_users)
            business = random.choice(created_businesses)
            
            checkin = CheckIn(
                user_id=user.id,
                business_id=business.id,
                center_id=None,  # Not using centers for now
                member_id=None,  # Not using members for now
                check_in_time=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                tokens_used=random.randint(1, 10),
                status="completed"
            )
            db.add(checkin)
        
        db.commit()
        print("Created 100 test check-ins")
        
        # Create test communities
        communities_data = [
            {"name": "Fitness Enthusiasts", "description": "For people who love working out"},
            {"name": "Yoga Lovers", "description": "Yoga practitioners and beginners welcome"},
            {"name": "Weightlifting Club", "description": "Serious lifters and strength training"},
            {"name": "Cardio Warriors", "description": "Running, cycling, and cardio lovers"},
            {"name": "Healthy Living", "description": "Tips and support for healthy lifestyle"}
        ]
        
        print("Creating test communities...")
        for community_data in communities_data:
            # Check if community already exists
            existing_community = db.query(Community).filter(Community.name == community_data["name"]).first()
            if not existing_community:
                creator = random.choice(created_users)
                community = Community(
                    name=community_data["name"],
                    description=community_data["description"],
                    creator_id=creator.id,
                    is_public=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
                )
                db.add(community)
        
        db.commit()
        print("Created test communities")
        
        # Print summary with initials
        print("\n=== TEST DATA SUMMARY ===")
        
        print("\nUsers:")
        for user in created_users[:5]:  # Show first 5
            print(f"  - {user.name} ({user.email}) | Initials: {user.get_initials()} | Balance: ${user.balance:.2f}")
        print(f"  ... and {len(created_users) - 5} more users")
        
        print("\nBusinesses:")
        for business in created_businesses[:5]:  # Show first 5
            print(f"  - {business.name} ({business.email}) | Initials: {business.get_initials()} | Balance: ${business.balance:.2f}")
        print(f"  ... and {len(created_businesses) - 5} more businesses")
        
        # Payment stats
        total_payments = db.query(Payment).count()
        completed_payments = db.query(Payment).filter(Payment.status == "completed").count()
        total_revenue = db.query(Payment).filter(Payment.status == "completed").with_entities(Payment.amount).all()
        revenue_sum = sum([p.amount for p in total_revenue]) if total_revenue else 0
        
        print(f"\nPayments: {total_payments} total, {completed_payments} completed")
        print(f"Total Revenue: ${revenue_sum:.2f}")
        
        # Check-in stats
        total_checkins = db.query(CheckIn).count()
        print(f"Check-ins: {total_checkins} total")
        
        # Community stats
        total_communities = db.query(Community).count()
        print(f"Communities: {total_communities} total")
        
        print("\n✅ Test data creation completed successfully!")
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
