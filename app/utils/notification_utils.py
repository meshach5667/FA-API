import requests
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# FCM Push Notification
FCM_SERVER_KEY = "YOUR_FCM_SERVER_KEY"

def send_push_notification(device_token: str, title: str, body: str):
    url = "https://fcm.googleapis.com/fcm/send"
    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": device_token,
        "notification": {
            "title": title,
            "body": body
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Email Notification
conf = ConnectionConfig(
    MAIL_USERNAME = "your@email.com",
    MAIL_PASSWORD = "password",
    MAIL_FROM = "your@email.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.yourserver.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True
)

async def send_email_notification(email_to, subject, body):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

# Reminder Notification
def send_reminder(user_id, message):
    print(f"Reminder for user {user_id}: {message}")