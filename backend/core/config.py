from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "NJ Voter Chat API"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://nj-voter-chat.web.app",
    ]
    
    # Google Cloud
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
    GOOGLE_CLOUD_REGION: str = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # Redis (for session management)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Firestore (for data persistence)
    FIRESTORE_COLLECTION_USERS: str = "users"
    FIRESTORE_COLLECTION_CHATS: str = "chats"
    FIRESTORE_COLLECTION_LISTS: str = "lists"
    
    # ADK Agent Path
    ADK_AGENT_PATH: str = "../agents/nj_voter_chat_adk"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()