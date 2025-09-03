from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
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

router = APIRouter()

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
    
    profile_data = profile.dict(exclude_unset=True)
    print(f"Updating business profile for business {current_business.id} with data: {profile_data}")
    
    # If name is being updated, also update the business_name in the Business table
    if 'name' in profile_data:
        new_name = profile_data['name'].strip() if profile_data['name'] else None
        print(f"Business name update: current='{current_business.business_name}', new='{new_name}'")
        
        if not new_name:
            raise HTTPException(status_code=400, detail="Business name cannot be empty")
            
        # Only check for duplicates if the name is actually changing
        if new_name != current_business.business_name:
            existing_business = db.query(Business).filter(
                and_(
                    Business.business_name == new_name,
                    Business.id != current_business.id
                )
            ).first()
            
            if existing_business:
                print(f"Business name '{new_name}' already taken by business ID {existing_business.id}")
                # Suggest some alternatives
                suggestions = [
                    f"{new_name} Fitness",
                    f"{new_name} Gym", 
                    f"{new_name} Sports",
                    f"The {new_name}",
                    f"{new_name} Club"
                ]
                suggestions_text = ", ".join([f'"{s}"' for s in suggestions[:3]])
                raise HTTPException(
                    status_code=400, 
                    detail=f"Business name '{new_name}' is already taken. Try alternatives like: {suggestions_text}"
                )
            
            # Update the business_name in the Business table
            current_business.business_name = new_name
            print(f"Updated business_name to '{new_name}'")
        else:
            print("Business name unchanged, skipping validation")
    
    # Update the profile
    try:
        for key, value in profile_data.items():
            setattr(db_profile, key, value)
        
        db.commit()
        db.refresh(db_profile)
        return db_profile
    except Exception as e:
        db.rollback()
        print(f"Database error updating business profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not update profile: {str(e)}"
        )

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
        logo_url=profile.logo_url,
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

@router.post("/profile/upload-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    """Upload a single business profile image (replaces existing)"""
    import os
    import uuid
    
    # Check if profile exists
    db_profile = db.query(BusinessProfile).filter_by(business_id=current_business.id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    
    # Create upload directory if it doesn't exist
    upload_dir = "uploads/business_profiles"
    os.makedirs(upload_dir, exist_ok=True)
    
    try:
        # Delete existing image if it exists
        if db_profile.logo_url:
            try:
                old_file_path = db_profile.logo_url.replace("/uploads/", "uploads/")
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            except Exception as e:
                print(f"Warning: Could not delete old image: {e}")
        
        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if file.filename else "jpg"
        unique_filename = f"{current_business.id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create URL (relative path that can be served by FastAPI)
        file_url = f"/uploads/business_profiles/{unique_filename}"
        
        # Update profile with new image URL (using logo_url field for single image)
        db_profile.logo_url = file_url
        db.commit()
        db.refresh(db_profile)
        
        return {
            "message": "Successfully uploaded profile image",
            "image_url": file_url
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.delete("/profile/image")
def delete_profile_image(
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    """Delete the business profile image"""
    import os
    
    db_profile = db.query(BusinessProfile).filter_by(business_id=current_business.id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if not db_profile.logo_url:
        raise HTTPException(status_code=404, detail="No image found")
    
    # Get the image URL to delete
    image_url = db_profile.logo_url
    
    try:
        # Delete the physical file
        if image_url.startswith("/uploads/"):
            file_path = image_url[1:]  # Remove leading slash
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Clear the logo_url in database
        db_profile.logo_url = None
        db.commit()
        
        return {
            "message": "Profile image deleted successfully"
        }
        file_path = image_url[1:]  # Remove leading slash
        if os.path.exists(file_path):
                os.remove(file_path)
        
        # Update database
        db_profile.pictures = updated_pictures
        db.commit()
        
        return {
            "message": "Image deleted successfully",
            "remaining_images": updated_pictures
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
