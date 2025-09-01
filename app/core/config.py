from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MAIL_FROM: str = "noreply@example.com"
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = "user"
    MAIL_PASSWORD: str = "password"
    EMAIL_USER: str = "user"
    EMAIL_PASSWORD: str = "password"
    MAIL_SSL_TLS: bool = False
    MAIL_STARTTLS: bool = True
    USE_CREDENTIALS: bool = True

settings = Settings()