from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate
from geopy.distance import geodesic

class NotificationService:
    def create_nearby_gym_notification(self, db: Session, user_id: int, gym):
        notification = Notification(
            user_id=user_id,
            title="New Gym Nearby!",
            message=f"{gym.name} is now available in your area. Distance: {gym.distance:.1f}km",
            type=NotificationType.NEARBY_GYM,
            link=f"/gyms/{gym.id}"
        )
        db.add(notification)
        db.commit()
        return notification

    def create_subscription_notification(self, db: Session, user_id: int, subscription_type: str):
        notification = Notification(
            user_id=user_id,
            title="Subscription Update",
            message=f"Your {subscription_type} subscription has been activated",
            type=NotificationType.SUBSCRIPTION
        )
        db.add(notification)
        db.commit()
        return notification

    def create_reward_notification(self, db: Session, user_id: int, points: int):
        notification = Notification(
            user_id=user_id,
            title="New Reward Points!",
            message=f"You've earned {points} reward points",
            type=NotificationType.REWARD,
            link="/rewards"
        )
        db.add(notification)
        db.commit()
        return notification

    def create_booking_notification(self, db: Session, user_id: int, activity_name: str, time: str):
        notification = Notification(
            user_id=user_id,
            title="Booking Confirmed",
            message=f"Your booking for {activity_name} at {time} is confirmed",
            type=NotificationType.BOOKING
        )
        db.add(notification)
        db.commit()
        return notification