from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS
)

async def send_reset_email(email_to: EmailStr, token: str, business_name: str):
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email_to],
        body=f"""
        Hi {business_name},
        
        You have requested to reset your password. Please click the link below to reset your password:
        
        {reset_link}
        
        If you did not request this, please ignore this email.
        
        The link will expire in 24 hours.
        """,
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
