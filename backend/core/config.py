from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Try to load secrets from Google Secret Manager
def load_secret(secret_id: str, default: str = "") -> str:
    """Load a secret from Google Secret Manager."""
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        print(f"Warning: Could not load secret {secret_id}: {e}")
        return default

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
    
    # Firestore is used exclusively for chat storage
    USE_FIRESTORE_FOR_CHAT: bool = True
    
    # Authentication
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours (1440 minutes)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days for refresh token
    
    # Google OAuth - Load from Secret Manager
    GOOGLE_CLIENT_ID: str = load_secret("google-oauth-client-id", "")
    GOOGLE_CLIENT_SECRET: str = load_secret("google-oauth-client-secret", "")
    
    # Redis (for session management and caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
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

def get_settings() -> Settings:
    """Get application settings."""
    return settings