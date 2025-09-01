from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.models.activity import Activity
from app.models.activity_meta import ActivityLike, ActivityComment, ActivityJoin
from app.schemas.activity import ActivityCreate, ActivityOut, ActivityCommentCreate, ActivityCommentOut
from app.api.deps import get_current_business
from app.api.auth import get_current_user   # <-- ADD THIS
from app.models.business import Business
from app.models.user import User            # <-- AND THIS

router = APIRouter()

@router.post("/", response_model=ActivityOut)
def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)  # Only businesses can create
):
    # Parse the date string to a Python date object
    try:
        activity_date = datetime.strptime(activity.date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    new_activity = Activity(
        business_id=current_business.id,  # Set from the authenticated business
        name=activity.name,
        date=activity_date,  # Use the parsed date object
        time=activity.time,
        location=activity.location,
        description=activity.description,
        center_id=activity.center_id,
        activity_type=activity.activity_type,
        capacity=activity.capacity,
        instructor=activity.instructor,
        duration=activity.duration,
        price=activity.price,
    )
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity

# List all activities (public)
@router.get("/", response_model=list[ActivityOut])
def list_activities(db: Session = Depends(get_db)):
    return db.query(Activity).filter(Activity.is_active == True).all()

# List business-specific activities
@router.get("/my-activities", response_model=list[ActivityOut])
def list_my_activities(
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    return db.query(Activity).filter(Activity.business_id == current_business.id).all()

# List activities for a specific business
@router.get("/business/{business_id}", response_model=list[ActivityOut])
def list_business_activities(
    business_id: int,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    # Ensure the business can only access their own activities
    if current_business.id != business_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return db.query(Activity).filter(Activity.business_id == business_id).all()

# Get current business activities
@router.get("/my-activities", response_model=list[ActivityOut])
def get_my_activities(
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    return db.query(Activity).filter(Activity.business_id == current_business.id).all()

# Get activity details by ID
@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity_details(
    activity_id: int,
    db: Session = Depends(get_db)
):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

# Update activity
@router.put("/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: int,
    activity_update: ActivityCreate,  # Reuse the create schema for updates
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.business_id == current_business.id
    ).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found or access denied")
    
    # Parse the date string to a Python date object
    try:
        activity_date = datetime.strptime(activity_update.date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Update fields
    activity.name = activity_update.name
    activity.description = activity_update.description
    activity.date = activity_date
    activity.time = activity_update.time
    activity.location = activity_update.location
    activity.center_id = activity_update.center_id
    activity.activity_type = activity_update.activity_type
    activity.capacity = activity_update.capacity
    activity.instructor = activity_update.instructor
    activity.duration = activity_update.duration
    activity.price = activity_update.price
    
    db.commit()
    db.refresh(activity)
    return activity

# Delete activity
@router.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.business_id == current_business.id
    ).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found or access denied")
    
    db.delete(activity)
    db.commit()
    return {"message": "Activity deleted successfully"}

# Like an activity
@router.post("/{activity_id}/like")
def like_activity(activity_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    like = db.query(ActivityLike).filter_by(activity_id=activity_id, user_id=current_user.id).first()
    if like:
        raise HTTPException(status_code=400, detail="Already liked")
    db.add(ActivityLike(activity_id=activity_id, user_id=current_user.id))
    db.commit()
    return {"message": "Liked"}

# Comment on an activity
@router.post("/{activity_id}/comment", response_model=ActivityCommentOut)
def comment_activity(activity_id: int, comment: ActivityCommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_comment = ActivityComment(activity_id=activity_id, user_id=current_user.id, comment=comment.comment)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

# Get comments on an activity
@router.get("/{activity_id}/comments", response_model=list[ActivityCommentOut])
def get_activity_comments(
    activity_id: int,
    db: Session = Depends(get_db)
):
    return db.query(ActivityComment).filter(ActivityComment.activity_id == activity_id).all()

# Join an activity
@router.post("/{activity_id}/join")
def join_activity(activity_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    join = db.query(ActivityJoin).filter_by(activity_id=activity_id, user_id=current_user.id).first()
    if join:
        raise HTTPException(status_code=400, detail="Already joined")
    db.add(ActivityJoin(activity_id=activity_id, user_id=current_user.id))
    # increment join_count
    activity = db.query(Activity).filter_by(id=activity_id).first()
    if activity:
        activity.join_count += 1
    db.commit()
    return {"message": "Joined"}

# Get likes count on an activity
@router.get("/{activity_id}/likes/count")
def get_activity_likes_count(
    activity_id: int,
    db: Session = Depends(get_db)
):
    count = db.query(ActivityLike).filter(ActivityLike.activity_id == activity_id).count()
    return {"likes": count}

# Get a specific activity with full details
@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db)
):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

# Update an existing activity (only by the business that created it)
@router.put("/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: int,
    activity_update: ActivityCreate,  # Reuse create schema for updates
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.business_id == current_business.id
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found or not authorized to edit")
    
    # Parse the date if provided
    if activity_update.date:
        try:
            activity_date = datetime.strptime(activity_update.date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        activity.date = activity_date
    
    # Update other fields
    for field, value in activity_update.dict(exclude={'date'}).items():
        if value is not None:
            setattr(activity, field, value)
    
    db.commit()
    db.refresh(activity)
    return activity

# Delete an activity (only by the business that created it)
@router.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.business_id == current_business.id
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found or not authorized to delete")
    
    db.delete(activity)
    db.commit()
    return {"message": "Activity deleted successfully"}

# Generate QR code for activity
@router.get("/{activity_id}/qr-code")
def generate_activity_qr_code(
    activity_id: int,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
):
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.business_id == current_business.id
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found or not authorized")
    
    # Generate QR code URL (you can implement actual QR code generation here)
    activity_url = f"https://fitaccess.app/activities/{activity_id}"
    qr_data = {
        "activity_id": activity_id,
        "activity_name": activity.name,
        "business_id": current_business.id,
        "url": activity_url,
        "qr_text": f"Join {activity.name} at {activity.location} on {activity.date} at {activity.time}"
    }
    
    return qr_data

# Get members who joined an activity
@router.get("/{activity_id}/members")
def get_activity_members(
    activity_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Get all joins for this activity with user details
        joins = db.query(ActivityJoin).filter(
            ActivityJoin.activity_id == activity_id
        ).all()
        
        members = []
        for join in joins:
            # Get user details for each join
            user = db.query(User).filter(User.id == join.user_id).first()
            if user:
                members.append({
                    "id": str(user.id),
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "joined_date": join.joined_at.isoformat() if hasattr(join, 'joined_at') and join.joined_at else join.created_at.isoformat() if hasattr(join, 'created_at') else None,
                    "avatar": None  # Add avatar URL if available
                })
        
        return {"members": members, "total": len(members)}
    except Exception as e:
        print(f"Error fetching activity members: {e}")
        # Return empty list if there's an error
        return {"members": [], "total": 0}