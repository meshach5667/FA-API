from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import os
import uuid
from pathlib import Path

from app.db.database import get_db
from app.models.advertisement import Advertisement, AdStatusEnum, AdTargetTypeEnum
from app.models.admin import Admin
from app.schemas.advertisement import (
    AdvertisementCreate, 
    AdvertisementUpdate, 
    AdvertisementOut, 
    AdvertisementStats,
    AdAnalytics
)
from app.api.deps import get_current_super_admin

router = APIRouter()

# File upload configuration
UPLOAD_DIR = Path("uploads/advertisements")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file and return the URL"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Max size: 5MB")
        buffer.write(content)
    
    # Return URL (adjust based on your static file serving)
    return f"/static/advertisements/{unique_filename}"

@router.get("/", response_model=List[AdvertisementOut])
async def get_all_advertisements(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[AdStatusEnum] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin)
):
    """Get all advertisements with optional filtering"""
    query = db.query(Advertisement)
    
    if status_filter:
        query = query.filter(Advertisement.status == status_filter)
    
    advertisements = query.offset(skip).limit(limit).all()
    
    # Format output to match frontend expectations
    result = []
    for ad in advertisements:
        ad_dict = {
            "id": str(ad.id),
            "title": ad.title,
            "description": ad.description,
            "imageUrl": ad.image_url,
            "startDate": ad.start_date.isoformat(),
            "endDate": ad.end_date.isoformat(),
            "status": ad.status,
            "target": {
                "type": ad.target_type,
                "locations": ad.target_locations or [],
                "userGroups": ad.target_user_groups or []
            },
            "clicks": ad.clicks,
            "views": ad.views,
            "createdAt": ad.created_at.isoformat(),
            "updatedAt": ad.updated_at.isoformat()
        }
        result.append(ad_dict)
    
    return result

@router.get("/stats", response_model=AdvertisementStats)
async def get_advertisement_stats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin)
):
    """Get advertisement statistics"""
    total_ads = db.query(Advertisement).count()
    active_ads = db.query(Advertisement).filter(Advertisement.status == AdStatusEnum.active).count()
    scheduled_ads = db.query(Advertisement).filter(Advertisement.status == AdStatusEnum.scheduled).count()
    ended_ads = db.query(Advertisement).filter(Advertisement.status == AdStatusEnum.ended).count()
    draft_ads = db.query(Advertisement).filter(Advertisement.status == AdStatusEnum.draft).count()
    
    total_views = db.query(func.sum(Advertisement.views)).scalar() or 0
    total_clicks = db.query(func.sum(Advertisement.clicks)).scalar() or 0
    
    ctr = (total_clicks / total_views * 100) if total_views > 0 else 0
    
    return AdvertisementStats(
        total_ads=total_ads,
        active_ads=active_ads,
        scheduled_ads=scheduled_ads,
        ended_ads=ended_ads,
        draft_ads=draft_ads,
        total_views=total_views,
        total_clicks=total_clicks,
        ctr=round(ctr, 2)
    )

@router.get("/{ad_id}")
async def get_advertisement(
    ad_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin)
):
    """Get a specific advertisement"""
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    return {
        "id": str(ad.id),
        "title": ad.title,
        "description": ad.description,
        "imageUrl": ad.image_url,
        "startDate": ad.start_date.isoformat(),
        "endDate": ad.end_date.isoformat(),
        "status": ad.status,
        "target": {
            "type": ad.target_type,
            "locations": ad.target_locations or [],
            "userGroups": ad.target_user_groups or []
        },
        "clicks": ad.clicks,
        "views": ad.views,
        "createdAt": ad.created_at.isoformat(),
        "updatedAt": ad.updated_at.isoformat()
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_advertisement(
    title: str = Form(...),
    description: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    target_type: str = Form(default="all"),
    target_locations: Optional[str] = Form(default=None),
    target_user_groups: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin)
):
    """Create a new advertisement with file upload"""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if end_dt <= start_dt:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        # Save uploaded file
        image_url = save_uploaded_file(file)
        
        # Parse target locations/groups if provided
        locations = []
        user_groups = []
        
        if target_locations:
            locations = [loc.strip() for loc in target_locations.split(',') if loc.strip()]
        if target_user_groups:
            user_groups = [group.strip() for group in target_user_groups.split(',') if group.strip()]
        
        # Determine initial status based on dates
        now = datetime.utcnow()
        if start_dt <= now <= end_dt:
            initial_status = AdStatusEnum.active
        elif start_dt > now:
            initial_status = AdStatusEnum.scheduled
        else:
            initial_status = AdStatusEnum.ended
        
        # Create advertisement
        ad = Advertisement(
            title=title,
            description=description,
            image_url=image_url,
            start_date=start_dt,
            end_date=end_dt,
            status=initial_status,
            target_type=AdTargetTypeEnum(target_type),
            target_locations=locations if locations else None,
            target_user_groups=user_groups if user_groups else None,
            created_by=current_admin.id
        )
        
        db.add(ad)
        db.commit()
        db.refresh(ad)
        
        return {
            "id": str(ad.id),
            "title": ad.title,
            "description": ad.description,
            "imageUrl": ad.image_url,
            "startDate": ad.start_date.isoformat(),
            "endDate": ad.end_date.isoformat(),
            "status": ad.status,
            "target": {
                "type": ad.target_type,
                "locations": ad.target_locations or [],
                "userGroups": ad.target_user_groups or []
            },
            "clicks": ad.clicks,
            "views": ad.views,
            "createdAt": ad.created_at.isoformat(),
            "updatedAt": ad.updated_at.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating advertisement: {str(e)}")

@router.put("/{ad_id}")
async def update_advertisement(
    ad_id: int,
    title: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    start_date: Optional[str] = Form(default=None),
    end_date: Optional[str] = Form(default=None),
    status: Optional[str] = Form(default=None),
    target_type: Optional[str] = Form(default=None),
    target_locations: Optional[str] = Form(default=None),
    target_user_groups: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin)
):
    """Update an advertisement"""
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    try:
        # Update fields if provided
        if title is not None:
            ad.title = title
        if description is not None:
            ad.description = description
        if start_date is not None:
            ad.start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date is not None:
            ad.end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        if status is not None:
            ad.status = AdStatusEnum(status)
        if target_type is not None:
            ad.target_type = AdTargetTypeEnum(target_type)
        
        # Update target locations/groups
        if target_locations is not None:
            locations = [loc.strip() for loc in target_locations.split(',') if loc.strip()]
            ad.target_locations = locations if locations else None
        if target_user_groups is not None:
            user_groups = [group.strip() for group in target_user_groups.split(',') if group.strip()]
            ad.target_user_groups = user_groups if user_groups else None
        
        # Handle file upload if provided
        if file and file.filename:
            # Delete old file if it exists
            if ad.image_url.startswith('/static/'):
                old_file_path = UPLOAD_DIR / ad.image_url.split('/')[-1]
                if old_file_path.exists():
                    old_file_path.unlink()
            
            # Save new file
            ad.image_url = save_uploaded_file(file)
        
        # Validate dates
        if ad.end_date <= ad.start_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        ad.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ad)
        
        return {
            "id": str(ad.id),
            "title": ad.title,
            "description": ad.description,
            "imageUrl": ad.image_url,
            "startDate": ad.start_date.isoformat(),
            "endDate": ad.end_date.isoformat(),
            "status": ad.status,
            "target": {
                "type": ad.target_type,
                "locations": ad.target_locations or [],
                "userGroups": ad.target_user_groups or []
            },
            "clicks": ad.clicks,
            "views": ad.views,
            "createdAt": ad.created_at.isoformat(),
            "updatedAt": ad.updated_at.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating advertisement: {str(e)}")

@router.delete("/{ad_id}")
async def delete_advertisement(
    ad_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin)
):
    """Delete an advertisement"""
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    # Delete associated file if it exists
    if ad.image_url.startswith('/static/'):
        file_path = UPLOAD_DIR / ad.image_url.split('/')[-1]
        if file_path.exists():
            file_path.unlink()
    
    db.delete(ad)
    db.commit()
    
    return {"message": "Advertisement deleted successfully"}

@router.get("/{ad_id}/analytics", response_model=AdAnalytics)
async def get_advertisement_analytics(
    ad_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin)
):
    """Get detailed analytics for a specific advertisement"""
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    # In a real implementation, you would track views/clicks with timestamps
    # For now, we'll return current values with mock daily/weekly breakdowns
    return AdAnalytics(
        ad_id=ad_id,
        views_today=int(ad.views * 0.1),  # Mock: 10% of total views today
        clicks_today=int(ad.clicks * 0.1),  # Mock: 10% of total clicks today
        views_this_week=int(ad.views * 0.3),  # Mock: 30% this week
        clicks_this_week=int(ad.clicks * 0.3),  # Mock: 30% this week
        views_this_month=ad.views,
        clicks_this_month=ad.clicks,
        ctr_today=(ad.clicks * 0.1 / max(ad.views * 0.1, 1) * 100) if ad.views > 0 else 0,
        ctr_this_week=(ad.clicks * 0.3 / max(ad.views * 0.3, 1) * 100) if ad.views > 0 else 0,
        ctr_this_month=(ad.clicks / max(ad.views, 1) * 100) if ad.views > 0 else 0
    )

@router.post("/{ad_id}/view")
async def track_ad_view(
    ad_id: int,
    db: Session = Depends(get_db)
):
    """Track an advertisement view (public endpoint for mobile app)"""
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    ad.views += 1
    db.commit()
    
    return {"message": "View tracked"}

@router.post("/{ad_id}/click")
async def track_ad_click(
    ad_id: int,
    db: Session = Depends(get_db)
):
    """Track an advertisement click (public endpoint for mobile app)"""
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    ad.clicks += 1
    db.commit()
    
    return {"message": "Click tracked"}

@router.post("/bulk-update-status")
async def bulk_update_status(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_super_admin)
):
    """Bulk update advertisement status based on current date"""
    now = datetime.utcnow()
    
    # Update scheduled ads to active
    scheduled_to_active = db.query(Advertisement).filter(
        and_(
            Advertisement.status == AdStatusEnum.scheduled,
            Advertisement.start_date <= now,
            Advertisement.end_date > now
        )
    ).update({Advertisement.status: AdStatusEnum.active})
    
    # Update active ads to ended
    active_to_ended = db.query(Advertisement).filter(
        and_(
            Advertisement.status == AdStatusEnum.active,
            Advertisement.end_date <= now
        )
    ).update({Advertisement.status: AdStatusEnum.ended})
    
    db.commit()
    
    return {
        "message": f"Updated {scheduled_to_active} scheduled ads to active, {active_to_ended} active ads to ended"
    }
