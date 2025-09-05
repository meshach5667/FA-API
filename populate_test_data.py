#!/usr/bin/env python3
"""
Script to populate test data for FitAccess admin dashboard
"""

import sys
import os
sys.path.append('.')

from app.db.database import get_db
from app.models.user import User
from app.models.business import Business
from app.models.community import Community, CommunityMessage, CommunityMember
from app.models.group_activity import Group, GroupPost, GroupMember
from app.models.payment import Payment, PaymentStatusEnum, PaymentTypeEnum
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.check_in import CheckIn
from app.models.reward import Reward
from app.models.activity import Activity
from app.models.advertisement import Advertisement, AdStatusEnum, AdTargetTypeEnum
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

def populate_users(db: Session):
    """Create sample users"""
    users_data = [
        {"name": "John Doe", "email": "john.doe@example.com", "phone_number": "+1234567890"},
        {"name": "Jane Smith", "email": "jane.smith@example.com", "phone_number": "+1234567891"},
        {"name": "Mike Johnson", "email": "mike.johnson@example.com", "phone_number": "+1234567892"},
        {"name": "Sarah Wilson", "email": "sarah.wilson@example.com", "phone_number": "+1234567893"},
        {"name": "David Brown", "email": "david.brown@example.com", "phone_number": "+1234567894"},
    ]
    
    for user_data in users_data:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            user = User(**user_data)
            db.add(user)
            print(f"Created user: {user_data['name']}")
    
    db.commit()

def populate_businesses(db: Session):
    """Create sample businesses"""
    businesses_data = [
        {"name": "FitZone Gym", "location": "Lagos, Nigeria", "contact_info": "contact@fitzone.com"},
        {"name": "PowerFit Center", "location": "Abuja, Nigeria", "contact_info": "info@powerfit.com"},
        {"name": "Elite Fitness", "location": "Port Harcourt, Nigeria", "contact_info": "hello@elitefitness.com"},
    ]
    
    for business_data in businesses_data:
        existing_business = db.query(Business).filter(Business.name == business_data["name"]).first()
        if not existing_business:
            business = Business(**business_data)
            db.add(business)
            print(f"Created business: {business_data['name']}")
    
    db.commit()

def populate_communities(db: Session):
    """Create sample communities"""
    communities_data = [
        {"name": "Fitness Beginners", "description": "A community for those starting their fitness journey", 
         "category": "fitness", "center_id": 1},
        {"name": "Weight Loss Warriors", "description": "Support group for weight loss goals", 
         "category": "fitness", "center_id": 1},
        {"name": "Nutrition Enthusiasts", "description": "Share healthy recipes and nutrition tips", 
         "category": "nutrition", "center_id": 2},
        {"name": "Yoga & Meditation", "description": "Find inner peace through yoga and meditation", 
         "category": "wellness", "center_id": 2},
    ]
    
    for community_data in communities_data:
        existing_community = db.query(Community).filter(Community.name == community_data["name"]).first()
        if not existing_community:
            community = Community(**community_data)
            db.add(community)
            print(f"Created community: {community_data['name']}")
    
    db.commit()

def populate_groups(db: Session):
    """Create sample groups"""
    groups_data = [
        {"name": "Morning Runners", "description": "Early morning running group", 
         "business_id": 1, "member_count": 15},
        {"name": "Strength Training Club", "description": "Focus on building muscle and strength", 
         "business_id": 1, "member_count": 22},
        {"name": "Weekend Warriors", "description": "Intense weekend workout sessions", 
         "business_id": 2, "member_count": 18},
        {"name": "Cardio Kings", "description": "High-intensity cardio workouts", 
         "business_id": 2, "member_count": 12},
    ]
    
    for group_data in groups_data:
        existing_group = db.query(Group).filter(Group.name == group_data["name"]).first()
        if not existing_group:
            group = Group(**group_data)
            db.add(group)
            print(f"Created group: {group_data['name']}")
    
    db.commit()

def populate_payments(db: Session):
    """Create sample payments"""
    users = db.query(User).all()
    businesses = db.query(Business).all()
    
    if not users or not businesses:
        print("No users or businesses found, skipping payments")
        return
    
    for i in range(20):
        payment = Payment(
            user_id=random.choice(users).id,
            business_id=random.choice(businesses).id,
            amount=random.uniform(1000, 5000),
            currency="NGN",
            payment_type=random.choice(list(PaymentTypeEnum)),
            status=random.choice(list(PaymentStatusEnum)),
            transaction_id=f"txn_{i+1:04d}",
            payment_method="card",
            description=f"Payment for gym access #{i+1}",
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
        )
        db.add(payment)
        print(f"Created payment: {payment.transaction_id}")
    
    db.commit()

def populate_check_ins(db: Session):
    """Create sample check-ins"""
    users = db.query(User).all()
    
    if not users:
        print("No users found, skipping check-ins")
        return
    
    for i in range(50):
        checkin = CheckIn(
            user_id=random.choice(users).id,
            center_id=random.randint(1, 3),
            check_in_time=datetime.utcnow() - timedelta(days=random.randint(0, 90)),
            timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 90))
        )
        db.add(checkin)
        print(f"Created check-in #{i+1}")
    
    db.commit()

def populate_rewards(db: Session):
    """Create sample rewards"""
    rewards_data = [
        {"name": "First Timer", "description": "Welcome bonus for first gym visit", 
         "points_required": 0, "tokens_reward": 50},
        {"name": "Frequent Visitor", "description": "Visit 10 times in a month", 
         "points_required": 100, "tokens_reward": 100},
        {"name": "Consistency Champion", "description": "Visit 20 times in a month", 
         "points_required": 200, "tokens_reward": 200},
        {"name": "Referral Master", "description": "Refer 5 new users", 
         "points_required": 50, "tokens_reward": 300},
    ]
    
    for reward_data in rewards_data:
        existing_reward = db.query(Reward).filter(Reward.name == reward_data["name"]).first()
        if not existing_reward:
            reward = Reward(**reward_data)
            db.add(reward)
            print(f"Created reward: {reward_data['name']}")
    
    db.commit()

def populate_advertisements(db: Session):
    """Create sample advertisements"""
    ads_data = [
        {
            "title": "Summer Fitness Challenge",
            "description": "Join our 30-day summer fitness challenge and win amazing prizes!",
            "status": AdStatusEnum.active,
            "target_type": AdTargetTypeEnum.all,
            "start_date": datetime.utcnow() - timedelta(days=10),
            "end_date": datetime.utcnow() + timedelta(days=20),
            "created_by": 1
        },
        {
            "title": "New Yoga Classes",
            "description": "Try our new yoga classes every Tuesday and Thursday",
            "status": AdStatusEnum.active,
            "target_type": AdTargetTypeEnum.location,
            "target_locations": ["Lagos", "Abuja"],
            "start_date": datetime.utcnow() - timedelta(days=5),
            "end_date": datetime.utcnow() + timedelta(days=25),
            "created_by": 1
        },
        {
            "title": "Membership Discount",
            "description": "Get 20% off on annual memberships this month only!",
            "status": AdStatusEnum.scheduled,
            "target_type": AdTargetTypeEnum.all,
            "start_date": datetime.utcnow() + timedelta(days=5),
            "end_date": datetime.utcnow() + timedelta(days=35),
            "created_by": 1
        }
    ]
    
    for ad_data in ads_data:
        existing_ad = db.query(Advertisement).filter(Advertisement.title == ad_data["title"]).first()
        if not existing_ad:
            ad = Advertisement(**ad_data)
            db.add(ad)
            print(f"Created advertisement: {ad_data['title']}")
    
    db.commit()

def main():
    """Main function to populate all test data"""
    print("🚀 Populating test data for FitAccess admin dashboard...")
    
    db = next(get_db())
    
    try:
        print("\n📊 Creating sample users...")
        populate_users(db)
        
        print("\n🏢 Creating sample businesses...")
        populate_businesses(db)
        
        print("\n👥 Creating sample communities...")
        populate_communities(db)
        
        print("\n🤝 Creating sample groups...")
        populate_groups(db)
        
        print("\n💳 Creating sample payments...")
        populate_payments(db)
        
        print("\n✅ Creating sample check-ins...")
        populate_check_ins(db)
        
        print("\n🎁 Creating sample rewards...")
        populate_rewards(db)
        
        print("\n📢 Creating sample advertisements...")
        populate_advertisements(db)
        
        print("\n✅ Test data population completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error populating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
