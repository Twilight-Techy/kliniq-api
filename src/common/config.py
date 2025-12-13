import os
from typing import List
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Load environment variables from the correct .env file
os.environ["APP_ENV"] = "development"  # Default to development
env_file = ".env" if os.getenv("APP_ENV") == "development" else ".env.production"
load_dotenv(env_file)  # Load the .env file

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = True
    FRONTEND_URL: str
    SUPPORT_URL: str
    # DB_HOST: str
    # DB_PORT: int
    # DB_USER: str
    # DB_PASSWORD: str
    # DB_NAME: str
    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION_MINUTES: int
    ALLOWED_ORIGINS: List[str] = ["*"]
    LOG_LEVEL: str = "info"

    # Email settings
    EMAIL_SENDER: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    CONTACT_RECIPIENT: str

    # LLM / Modal settings
    MODAL_ENDPOINT_URL: str = ""  # Will be set after Modal deployment

    # Uncomment if you want to support comma-separated ALLOWED_ORIGINS strings
    @field_validator("ALLOWED_ORIGINS", mode="before")
    def split_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

settings = Settings()