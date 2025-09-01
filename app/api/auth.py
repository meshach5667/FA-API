from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.schemas.user import (
    UserCreate, UserLogin, UserUpdate, ForgetPasswordRequest,
    ResetPasswordRequest, UserProfile
)
from app.models.user import User
from app.db.database import get_db
from app.utils.email import send_reset_email  # Optional, mock for now
from sqlalchemy import func
from app.models.check_in import CheckIn
from app.models.check_out import CheckOut
from app.models.community import CommunityMember, Community
import re
from app.models.business import Business
from app.core.security import SECRET_KEY, ALGORITHM


SECRET_KEY = "fitaccesssupersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        print("No or invalid Authorization header")
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            print("No username in token payload")
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as e:
        print(f"JWT error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"User not found: {username}")
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_business(request: Request, db: Session = Depends(get_db)) -> Business:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    business = db.query(Business).filter(Business.email == email).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

def is_base64(sb):
    try:
        if isinstance(sb, str):
            # Remove data:image/...;base64, if present
            if "base64," in sb:
                sb = sb.split("base64,")[1]
            return re.fullmatch(r'[A-Za-z0-9+/=]+', sb) is not None
        return False
    except Exception:
        return False

@router.post("/signup", status_code=201)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    existing = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already taken")
    new_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
        balance=0.0,
        plan="Free",
        flex_credit=0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    """
    user = db.query(User).filter(
        (User.username == data.username_or_email) | (User.email == data.username_or_email)
    ).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.put("/profile/update")
def update_profile(update: UserUpdate, db: Session = Depends(get_db)):
    required_fields = ["username", "full_name", "email", "bio", "avatar"]
    missing_fields = [field for field in required_fields if not getattr(update, field, None)]
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required field(s): {', '.join(missing_fields)}"
        )

    # Validate avatar is base64 or URL
    avatar = update.avatar
    if avatar and not (avatar.startswith("http") or is_base64(avatar)):
        raise HTTPException(
            status_code=422,
            detail="Avatar must be a valid image URL or base64 string"
        )

    user = db.query(User).filter(User.username == update.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.full_name = update.full_name
    user.email = update.email
    user.phone = update.phone
    user.bio = update.bio
    user.avatar = update.avatar
    user.country = update.country or user.country
    user.state = update.state or user.state
    db.commit()
    return {"message": "Profile updated"}

@router.get("/profile", response_model=UserProfile)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Calculate total check-in time per center
    checkins = db.query(CheckIn).filter(CheckIn.user_id == current_user.id).all()
    checkouts = db.query(CheckOut).filter(CheckOut.user_id == current_user.id).all()
    checkin_map = {(c.center_id, c.id): c for c in checkins}
    checkout_map = {(c.center_id, c.checkin_id): c for c in checkouts}

    center_time = {}
    for (center_id, checkin_id), checkin in checkin_map.items():
        checkout = checkout_map.get((center_id, checkin_id))
        if checkout and checkout.checked_out_at and checkin.checked_in_at:
            minutes = int((checkout.checked_out_at - checkin.checked_in_at).total_seconds() // 60)
            if center_id not in center_time:
                center_time[center_id] = {"total_minutes": 0, "center_name": getattr(checkin, "center_name", str(center_id))}
            center_time[center_id]["total_minutes"] += max(minutes, 0)

    checkin_summary = [
        {"center_id": cid, "center_name": data["center_name"], "total_minutes": data["total_minutes"]}
        for cid, data in center_time.items()
    ]

    # Achievements: communities joined
    communities_joined = db.query(CommunityMember).filter(CommunityMember.user_id == current_user.id).count()

    # Account creation year/month
    created_year = current_user.created_at.year if current_user.created_at else None
    created_month = current_user.created_at.month if current_user.created_at else None

    return UserProfile(
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        bio=current_user.bio,
        country=current_user.country or "",
        state=current_user.state or "",
        balance=current_user.balance,
        plan=current_user.plan,
        flex_credit=current_user.flex_credit,
        checkin_summary=checkin_summary,
        achievements={"communities_joined": communities_joined},
        created_year=created_year,
        created_month=created_month,
        avatar=current_user.avatar
    )

@router.post("/password/forgot")
def forgot_password(request: ForgetPasswordRequest, db: Session = Depends(get_db)):
    """
    Send password reset link to user's email.
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Simulate email sending (replace with real email logic)
    print(f"Reset link sent to {user.email} (mock)")
    return {"message": "Password reset link sent"}

@router.post("/password/reset")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset user's password.
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    return {"message": "Password reset successful"}

