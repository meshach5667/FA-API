from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from datetime import datetime, date
from app.db.database import get_db
from app.models.group_activity import Group, GroupPost, GroupEvent, GroupMember, GroupPostLike, GroupPostComment
from app.schemas.group_activity import (
    GroupCreate, GroupOut, GroupUpdate,
    GroupPostCreate, GroupPostOut,
    GroupEventCreate, GroupEventOut,
    GroupMemberOut, GroupJoinRequest,
    GroupPostLikeOut, GroupPostLikeToggleResponse, GroupPostCommentCreate, GroupPostCommentOut
)
from app.api.deps import get_current_business, get_current_user

router = APIRouter()

# Group Management
@router.post("/", response_model=GroupOut)
def create_group(
    group_data: GroupCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Create a new group"""
    group = Group(
        business_id=current_business.id,
        **group_data.dict()
    )
    
    db.add(group)
    db.commit()
    db.refresh(group)
    return group

@router.get("/", response_model=List[GroupOut])
def get_groups(
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    category: Optional[str] = Query(None),
    is_private: Optional[bool] = Query(None),
    limit: int = Query(50, le=100)
):
    """Get groups for the current business with optional filters"""
    query = db.query(Group).filter(Group.business_id == current_business.id)
    
    if category:
        query = query.filter(Group.category == category)
    if is_private is not None:
        query = query.filter(Group.is_private == is_private)
    
    return query.order_by(desc(Group.created_at)).limit(limit).all()

@router.get("/{group_id}", response_model=GroupOut)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Get a specific group by ID"""
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return group

@router.put("/{group_id}", response_model=GroupOut)
def update_group(
    group_id: int,
    group_update: GroupUpdate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Update a group"""
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    for field, value in group_update.dict(exclude_unset=True).items():
        setattr(group, field, value)
    
    db.commit()
    db.refresh(group)
    return group

@router.delete("/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Delete a group"""
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    db.delete(group)
    db.commit()
    return {"message": "Group deleted successfully"}

# Group Membership
@router.post("/{group_id}/join")
def join_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    current_user = Depends(get_current_user)
):
    """Join a group"""
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if already a member
    existing_member = db.query(GroupMember).filter(
        and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        )
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="Already a member of this group")
    
    # Create membership
    membership = GroupMember(
        group_id=group_id,
        user_id=current_user.id,
        role="member",
        status="active" if not group.is_private else "pending"
    )
    
    db.add(membership)
    db.commit()
    
    status_message = "Joined group successfully" if not group.is_private else "Join request sent, awaiting approval"
    return {"message": status_message, "status": membership.status}

@router.delete("/{group_id}/leave")
def leave_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    current_user = Depends(get_current_user)
):
    """Leave a group"""
    membership = db.query(GroupMember).filter(
        and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        )
    ).first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="Not a member of this group")
    
    db.delete(membership)
    db.commit()
    return {"message": "Left group successfully"}

@router.get("/{group_id}/members", response_model=List[GroupMemberOut])
def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    status: Optional[str] = Query(None)
):
    """Get group members"""
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    query = db.query(GroupMember).filter(GroupMember.group_id == group_id)
    
    if status:
        query = query.filter(GroupMember.status == status)
    
    return query.all()

# Group Posts
@router.post("/{group_id}/posts", response_model=GroupPostOut)
def create_group_post(
    group_id: int,
    post_data: GroupPostCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Create a new group post (for business users)"""
    # Check if the group belongs to the current business
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found or doesn't belong to your business")
    
    # Create post with business user as author (using negative ID to distinguish from regular users)
    post = GroupPost(
        group_id=group_id,
        user_id=-current_business.id,  # Use negative business ID as user_id
        content=post_data.content,
        post_type=post_data.post_type
    )
    
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@router.get("/{group_id}/posts", response_model=List[GroupPostOut])
def get_group_posts(
    group_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    limit: int = Query(20, le=50)
):
    """Get posts from a group"""
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return db.query(GroupPost).filter(
        GroupPost.group_id == group_id
    ).order_by(desc(GroupPost.created_at)).limit(limit).all()

@router.delete("/{group_id}/posts/{post_id}")
def delete_group_post(
    group_id: int,
    post_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Delete a group post (for business users)"""
    # Check if group exists and belongs to business
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get the post
    post = db.query(GroupPost).filter(
        and_(
            GroupPost.id == post_id,
            GroupPost.group_id == group_id
        )
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Business owners can delete any post in their group
    # Or check if it's a business-created post (negative user_id)
    if post.user_id != -current_business.id and post.user_id > 0:
        # This is a regular user post, business can still delete it since they own the group
        pass
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}

# Group Post Likes
@router.post("/{group_id}/posts/{post_id}/like", response_model=GroupPostLikeToggleResponse)
def toggle_post_like(
    group_id: int,
    post_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Toggle like on a group post"""
    # Check if group exists and belongs to business
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get the post
    post = db.query(GroupPost).filter(
        and_(
            GroupPost.id == post_id,
            GroupPost.group_id == group_id
        )
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Use negative business ID as user ID for business users
    business_user_id = -current_business.id
    
    # Check if already liked
    existing_like = db.query(GroupPostLike).filter(
        and_(
            GroupPostLike.post_id == post_id,
            GroupPostLike.user_id == business_user_id
        )
    ).first()
    
    if existing_like:
        # Unlike - remove the like
        db.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1)
        db.commit()
        return GroupPostLikeToggleResponse(
            message="Post unliked", 
            liked=False
        )
    else:
        # Like - add the like
        new_like = GroupPostLike(
            post_id=post_id,
            user_id=business_user_id
        )
        db.add(new_like)
        post.likes_count += 1
        db.commit()
        db.refresh(new_like)
        return GroupPostLikeToggleResponse(
            message="Post liked", 
            liked=True,
            like_id=new_like.id
        )

@router.get("/{group_id}/posts/{post_id}/likes", response_model=List[GroupPostLikeOut])
def get_post_likes(
    group_id: int,
    post_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    limit: int = Query(50, le=100)
):
    """Get likes for a post"""
    # Check if group exists and belongs to business
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get the post
    post = db.query(GroupPost).filter(
        and_(
            GroupPost.id == post_id,
            GroupPost.group_id == group_id
        )
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return db.query(GroupPostLike).filter(
        GroupPostLike.post_id == post_id
    ).order_by(desc(GroupPostLike.created_at)).limit(limit).all()

# Group Post Comments
@router.post("/{group_id}/posts/{post_id}/comments", response_model=GroupPostCommentOut)
def create_post_comment(
    group_id: int,
    post_id: int,
    comment_data: GroupPostCommentCreate,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Create a comment on a group post"""
    # Check if group exists and belongs to business
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get the post
    post = db.query(GroupPost).filter(
        and_(
            GroupPost.id == post_id,
            GroupPost.group_id == group_id
        )
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Create comment with business user as author
    comment = GroupPostComment(
        post_id=post_id,
        user_id=-current_business.id,  # Use negative business ID as user_id
        content=comment_data.content
    )
    
    db.add(comment)
    post.comments_count += 1
    db.commit()
    db.refresh(comment)
    return comment

@router.get("/{group_id}/posts/{post_id}/comments", response_model=List[GroupPostCommentOut])
def get_post_comments(
    group_id: int,
    post_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business),
    limit: int = Query(50, le=100)
):
    """Get comments for a post"""
    # Check if group exists and belongs to business
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get the post
    post = db.query(GroupPost).filter(
        and_(
            GroupPost.id == post_id,
            GroupPost.group_id == group_id
        )
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return db.query(GroupPostComment).filter(
        GroupPostComment.post_id == post_id
    ).order_by(GroupPostComment.created_at).limit(limit).all()

@router.delete("/{group_id}/posts/{post_id}/comments/{comment_id}")
def delete_post_comment(
    group_id: int,
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_business = Depends(get_current_business)
):
    """Delete a comment on a group post"""
    # Check if group exists and belongs to business
    group = db.query(Group).filter(
        and_(
            Group.id == group_id,
            Group.business_id == current_business.id
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get the comment
    comment = db.query(GroupPostComment).filter(
        and_(
            GroupPostComment.id == comment_id,
            GroupPostComment.post_id == post_id
        )
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Business owners can delete any comment in their group
    # Or check if it's their own comment
    if comment.user_id != -current_business.id and comment.user_id > 0:
        # This is a regular user comment, business can still delete it since they own the group
        pass
    
    # Update post comment count
    post = db.query(GroupPost).filter(GroupPost.id == post_id).first()
    if post:
        post.comments_count = max(0, post.comments_count - 1)
    
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}
