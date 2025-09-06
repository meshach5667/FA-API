from fastapi import APIRouter, Depends, Query, HTTPException, Request, UploadFile, File, Form, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.center import Center
from app.schemas.center import CenterOut, CenterCreate, CenterRating, CenterComment
from app.models.user import User
from app.db.database import get_db
from app.api.auth import get_current_user
# from geopy.distance import geodesic  # Temporarily commented out
import shutil
import os

router = APIRouter()

@router.get("/", response_model=List[CenterOut])
def explore_centers(
    request: Request,
    latitude: float = Query(..., description="User's current latitude"),
    longitude: float = Query(..., description="User's current longitude"),
    center_type: Optional[str] = Query(None, description="Filter by center type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Show centers/facilities close to the user using their state and current location.
    Optional filter by center type.
    """
    # Get all centers in user's state
    centers_query = db.query(Center).filter(Center.state == current_user.state)
    if center_type:
        centers_query = centers_query.filter(Center.center_type == center_type)
    centers = centers_query.all()

    user_location = (latitude, longitude)
    results = []
    for center in centers:
        center_location = (center.latitude, center.longitude)
        # distance_km = geodesic(user_location, center_location).km
        # Simple distance calculation as fallback (not accurate but works)
        distance_km = ((center.latitude - latitude) ** 2 + (center.longitude - longitude) ** 2) ** 0.5 * 111
        if distance_km <= 20:  # Show centers within 20km radius, adjust as needed
            results.append(CenterOut(
                id=center.id,
                name=center.name,
                address=center.address,
                state=center.state,
                latitude=center.latitude,
                longitude=center.longitude,
                center_type=center.center_type,
                distance_km=round(distance_km, 2)
            ))
    # Sort by distance
    results.sort(key=lambda x: x.distance_km)
    return results

@router.post("/upload", response_model=CenterOut)
async def upload_center(
    name: str = Form(...),
    address: str = Form(...),
    state: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    services: str = Form(...),  # JSON stringified list
    description: str = Form(...),
    booking_schedule: str = Form(...),
    cac_number: str = Form(...),
    bank_name: str = Form(...),
    account_number: str = Form(...),
    account_name: str = Form(...),
    credit_required: int = Form(...),  # <-- Add this line
    images: List[UploadFile] = File(..., description="Exactly 3 images"),
    db: Session = Depends(get_db)
):
    """
    Upload a new center/facility.
    """
    if len(images) != 3:
        raise HTTPException(status_code=400, detail="Exactly 3 images are required.")

    image_paths = []
    for image in images:
        file_location = f"static/centers/{image.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_paths.append(file_location)

    import json
    services_list = json.loads(services) if isinstance(services, str) else services

    center = Center(
        name=name,
        address=address,
        state=state,
        latitude=latitude,
        longitude=longitude,
        images=image_paths,
        services=services_list,
        description=description,
        booking_schedule=booking_schedule,
        cac_number=cac_number,
        bank_name=bank_name,
        account_number=account_number,
        account_name=account_name,
        credit_required=credit_required,  # <-- Store it in the model
        rating=0.0,
        comments=[]
    )
    db.add(center)
    db.commit()
    db.refresh(center)
    return CenterOut(
        id=center.id,
        name=center.name,
        address=center.address,
        state=center.state,
        latitude=center.latitude,
        longitude=center.longitude,
        images=center.images,
        services=center.services,
        description=center.description,
        booking_schedule=center.booking_schedule,
        credit_required=center.credit_required,  # <-- Return it in the response
        rating=center.rating,
        comments=center.comments
    )

@router.post("/{center_id}/rate")
def rate_center(
    center_id: int,
    rating_data: CenterRating,
    db: Session = Depends(get_db)
):
    """
    Rate a center/facility.
    """
    center = db.query(Center).filter(Center.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")
    # Update average rating
    total_rating = center.rating * center.rating_count
    center.rating_count += 1
    center.rating = (total_rating + rating_data.rating) / center.rating_count
    db.commit()
    return {"message": "Rating submitted", "new_rating": center.rating}

@router.post("/{center_id}/comment")
def comment_center(
    center_id: int,
    comment_data: CenterComment,
    db: Session = Depends(get_db)
):
    """
    Add a comment to a center/facility.
    """
    center = db.query(Center).filter(Center.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")
    comments = center.comments or []
    comments.append(comment_data.comment)
    center.comments = comments
    db.commit()
    return {"message": "Comment added"}

@router.get("/{center_id}/feedback")
def get_center_feedback(
    center_id: int = Path(..., description="ID of the center"),
    db: Session = Depends(get_db)
):
    """
    Get all comments and the average rating for a center/facility.
    """
    center = db.query(Center).filter(Center.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")
    return {
        "center_id": center.id,
        "average_rating": center.rating,
        "rating_count": getattr(center, "rating_count", 0),
        "comments": center.comments or []
    }