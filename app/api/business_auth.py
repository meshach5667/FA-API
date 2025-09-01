from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, UploadFile, File
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.business import Business, BusinessProfile
from app.schemas.business import (
    BusinessCreate, BusinessLogin, BusinessOut, PasswordResetRequest, PasswordReset,
    BusinessProfileOut, BusinessProfileCreate, BusinessProfileUpdate, BusinessProfileSummary
)
from app.core.security import create_access_token
from app.core.email import send_reset_email
from app.api.deps import get_current_business
from datetime import datetime, timedelta
import secrets
import os
import shutil
from pathlib import Path
from typing import List

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads/business_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- Business Auth ---

@router.post("/signup", response_model=BusinessOut)
def create_business(business: BusinessCreate, db: Session = Depends(get_db)):
    if business.password != business.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if db.query(Business).filter(Business.email == business.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(Business).filter(Business.business_name == business.business_name).first():
        raise HTTPException(status_code=400, detail="Business name already taken")
    
    db_business = Business(
        business_name=business.business_name,
        email=business.email,
        phone=business.phone,
        address=business.address
    )
    db_business.set_password(business.password)
    db.add(db_business)
    db.commit()
    db.refresh(db_business)

    # Automatically create a default business profile
    db_profile = BusinessProfile(
        business_id=db_business.id,
        name=db_business.business_name,
        email=db_business.email,
        address=db_business.address,
        phone=db_business.phone,
        pictures=[],
        description=""
    )
    db.add(db_profile)
    db.commit()

    return db_business

@router.post("/login")
def login(business_login: BusinessLogin, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.email == business_login.email).first()
    if not business or not business.check_password(business_login.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": business.email, "type": "business"})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(
    request: PasswordResetRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    business = db.query(Business).filter(Business.email == request.email).first()
    if not business:
        raise HTTPException(status_code=404, detail="Email not found")
    token = secrets.token_urlsafe(32)
    business.reset_token = token
    business.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    background_tasks.add_task(
        send_reset_email,
        email_to=business.email,
        token=token,
        business_name=business.business_name
    )
    return {"message": "Password reset email sent"}

@router.post("/reset-password")
def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    business = db.query(Business).filter(
        Business.reset_token == reset_data.token,
        Business.reset_token_expires > datetime.utcnow()
    ).first()
    if not business:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    business.set_password(reset_data.new_password)
    business.reset_token = None
    business.reset_token_expires = None
    db.commit()
    return {"message": "Password reset successful"}

@router.get("/me", response_model=BusinessOut)
def get_my_business(db: Session = Depends(get_db), current_business: Business = Depends(get_current_business)):
    return current_business

# --- Business Profile ---

@router.get("/profile/me", response_model=BusinessProfileOut)
def get_my_profile(db: Session = Depends(get_db), current_business: Business = Depends(get_current_business)):
    profile = db.query(BusinessProfile).filter_by(business_id=current_business.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/profile", response_model=BusinessProfileOut)
def create_profile(
    profile: BusinessProfileCreate,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    if db.query(BusinessProfile).filter_by(business_id=current_business.id).first():
        raise HTTPException(status_code=400, detail="Profile already exists")
    db_profile = BusinessProfile(**profile.dict(), business_id=current_business.id)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.put("/profile", response_model=BusinessProfileOut)
def update_profile(
    profile: BusinessProfileUpdate,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    db_profile = db.query(BusinessProfile).filter_by(business_id=current_business.id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get the update data and handle it properly
    update_data = profile.dict(exclude_unset=True)
    print(f"Updating profile with data: {update_data}")
    
    for key, value in update_data.items():
        if hasattr(db_profile, key):
            setattr(db_profile, key, value)
        else:
            print(f"Warning: BusinessProfile model does not have attribute '{key}'")
    
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.get("/profile/summary", response_model=BusinessProfileSummary)
def get_business_profile_summary(
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    profile = db.query(BusinessProfile).filter_by(business_id=current_business.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Compute achievements, created_year, created_month if needed
    achievements = {
        "memberships": len(profile.membership_plans) if profile.membership_plans else 0,
        # Add more as needed
    }
    created_year = current_business.created_at.year if current_business.created_at else None
    created_month = current_business.created_at.month if current_business.created_at else None

    return BusinessProfileSummary(
        id=profile.id,
        business_name=current_business.business_name,
        email=profile.email,
        phone=profile.phone,
        address=profile.address,
        state=profile.state,
        country=profile.country,
        logo_url=profile.logo_url,  # Fixed: was profile instead of profile.logo_url
        cac_number=profile.cac_number,
        membership_plans=profile.membership_plans,
        business_hours=profile.business_hours,
        description=profile.description,
        longitude=profile.longitude,
        latitude=profile.latitude,
        achievements=achievements,
        created_year=created_year,
        created_month=created_month
    )

# Image upload endpoint
@router.post("/profile/upload-image")
async def upload_business_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Create filename
    import uuid
    file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
    filename = f"business_{current_business.id}_{uuid.uuid4()}.{file_extension}"
    file_path = f"uploads/business_images/{filename}"
    
    # Save file
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Get or create business profile
    profile = db.query(BusinessProfile).filter_by(business_id=current_business.id).first()
    if not profile:
        profile = BusinessProfile(
            business_id=current_business.id,
            name=current_business.business_name,
            email=current_business.email
        )
        db.add(profile)
    
    # Update logo URL
    profile.logo_url = f"/{file_path}"
    db.commit()
    
    return {"message": "Image uploaded successfully", "logo_url": profile.logo_url}
