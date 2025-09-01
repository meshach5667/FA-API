from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.community import Community, CommunityMessage, CommunityLike, CommunityComment, CommunityMember
from app.schemas.community import (
    CommunityCreate, CommunityOut, CommunityMessageCreate, CommunityMessageOut,
    CommunityCommentCreate, CommunityCommentOut, CommunityJoinOut
)
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()

# Only centers can create communities
@router.post("/", response_model=CommunityOut)
def create_community(
    community: CommunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Optionally: check if current_user is center owner/admin
    new_community = Community(
        center_id=current_user.id,  # or current_user.center_id if you have that
        name=community.name,
        description=community.description,
        category=community.category,
        image=community.image,
        members=0
    )
    db.add(new_community)
    db.commit()
    db.refresh(new_community)
    return CommunityOut(**new_community.__dict__, isJoined=False)

@router.get("/", response_model=list[CommunityOut])
def list_communities(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    communities = db.query(Community).all()
    # You can add logic to check if user is joined
    return [CommunityOut(**c.__dict__, isJoined=False) for c in communities]

# Only centers can send messages
@router.post("/message", response_model=CommunityMessageOut)
def send_message(
    message: CommunityMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_msg = CommunityMessage(
        community_id=message.community_id,
        center_id=current_user.id,  # or current_user.center_id
        message=message.message,
        image=message.image
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

@router.get("/{community_id}/messages", response_model=list[CommunityMessageOut])
def get_community_messages(community_id: int, db: Session = Depends(get_db)):
    return db.query(CommunityMessage).filter(CommunityMessage.community_id == community_id).all()

# Users can like a message
@router.post("/message/{message_id}/like")
def like_message(message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    like = db.query(CommunityLike).filter_by(message_id=message_id, user_id=current_user.id).first()
    if like:
        raise HTTPException(status_code=400, detail="Already liked")
    db.add(CommunityLike(message_id=message_id, user_id=current_user.id))
    db.commit()
    return {"message": "Liked"}

# Users can comment on a message
@router.post("/message/{message_id}/comment", response_model=CommunityCommentOut)
def comment_message(message_id: int, comment: CommunityCommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_comment = CommunityComment(message_id=message_id, user_id=current_user.id, comment=comment.comment)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

@router.get("/message/{message_id}/comments", response_model=list[CommunityCommentOut])
def get_message_comments(message_id: int, db: Session = Depends(get_db)):
    return db.query(CommunityComment).filter(CommunityComment.message_id == message_id).all()

@router.post("/{community_id}/join", response_model=CommunityJoinOut)
def join_community(
    community_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exists = db.query(CommunityMember).filter_by(community_id=community_id, user_id=current_user.id).first()
    if exists:
        raise HTTPException(status_code=400, detail="Already joined")
    db.add(CommunityMember(community_id=community_id, user_id=current_user.id))
    # increment members count
    community = db.query(Community).filter_by(id=community_id).first()
    if community:
        community.members += 1
    db.commit()
    members = db.query(CommunityMember).filter_by(community_id=community_id).count()
    return CommunityJoinOut(joined=True, members=members)

@router.post("/{community_id}/leave", response_model=CommunityJoinOut)
def leave_community(
    community_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    member = db.query(CommunityMember).filter_by(community_id=community_id, user_id=current_user.id).first()
    if not member:
        raise HTTPException(status_code=400, detail="Not a member")
    db.delete(member)
    # decrement members count
    community = db.query(Community).filter_by(id=community_id).first()
    if community and community.members > 0:
        community.members -= 1
    db.commit()
    members = db.query(CommunityMember).filter_by(community_id=community_id).count()
    return CommunityJoinOut(joined=False, members=members)

@router.get("/{community_id}/is_joined", response_model=CommunityJoinOut)
def is_joined_community(
    community_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    joined = db.query(CommunityMember).filter_by(community_id=community_id, user_id=current_user.id).first() is not None
    members = db.query(CommunityMember).filter_by(community_id=community_id).count()
    return CommunityJoinOut(joined=joined, members=members)