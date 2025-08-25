from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "NJ Voter Chat API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "https://gwanalytica.ai",
        "https://nj-voter-chat.web.app",
        "https://nj-voter-chat-app-nwv4o72vjq-uc.a.run.app",
        "https://nj-voter-chat-app-169579073940.us-central1.run.app",
    ]
    
    # Google Cloud
    GOOGLE_CLOUD_PROJECT: str = "proj-roth"
    GOOGLE_CLOUD_REGION: str = "us-central1"
    
    # Database Selection for Chat
    USE_FIRESTORE_FOR_CHAT: bool = True  # Use GCP Firestore (recommended)
    USE_MONGODB_FOR_CHAT: bool = False  # Use MongoDB if available
    MONGODB_URI: Optional[str] = None  # MongoDB connection string if using MongoDB
    
    # Authentication
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # Redis (for session management)
    REDIS_URL: str = "redis://localhost:6379"
    
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