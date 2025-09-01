from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import httpx
from google.auth.transport import requests
from google.oauth2 import id_token

from core.config import settings
from services.bigquery_user_service import get_bigquery_user_service
from services.oauth_token_service import OAuthTokenService

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class GoogleAuthRequest(BaseModel):
    googleToken: str
    redirectUri: Optional[str] = None

class AuthResponse(BaseModel):
    user: dict
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Try to fetch full user data from BigQuery
        user_service = get_bigquery_user_service()
        user_data = await user_service.get_user_by_id(user_id)
        
        if user_data:
            return user_data
        else:
            # Fallback to basic info from JWT
            return {"id": user_id, "email": payload.get("email")}
    except JWTError:
        raise credentials_exception

@router.post("/google/callback", response_model=AuthResponse)
async def google_auth_callback(request: GoogleAuthRequest):
    """
    Handle Google OAuth callback and exchange code for tokens
    """
    try:
        # Use the provided redirect URI or default to localhost for development
        redirect_uri = request.redirectUri or "http://localhost:8000/login"
        
        print(f"Received auth code: {request.googleToken[:20]}..." if len(request.googleToken) > 20 else request.googleToken)
        print(f"Using client_id: {settings.GOOGLE_CLIENT_ID}")
        print(f"Using redirect_uri: {redirect_uri}")
        
        # Exchange authorization code for tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": request.googleToken,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                }
            )
            
            print(f"Google token exchange response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Google token exchange error: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Failed to exchange authorization code: {response.text}"
                )
            
            token_data = response.json()
            id_token_str = token_data.get("id_token")
            
            # Verify and decode the ID token
            idinfo = id_token.verify_oauth2_token(
                id_token_str, 
                requests.Request(), 
                settings.GOOGLE_CLIENT_ID
            )
            
            # Extract user information from Google
            google_user_data = {
                "sub": idinfo.get("sub"),
                "email": idinfo.get("email"),
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture"),
                "googleId": idinfo.get("sub"),
                "given_name": idinfo.get("given_name"),
                "family_name": idinfo.get("family_name"),
                # Store Google OAuth tokens for Docs/Drive access
                "google_access_token": token_data.get("access_token"),
                "google_refresh_token": token_data.get("refresh_token"),
                "google_token_expires_at": datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
            }
            
            # Save/update user in BigQuery and get internal user_id
            user_service = get_bigquery_user_service()
            user = await user_service.save_or_update_user(google_user_data)
            
            # Store OAuth tokens separately in Firestore
            if token_data.get("access_token"):
                oauth_service = OAuthTokenService()
                await oauth_service.store_tokens(
                    user_id=user["user_id"],
                    tokens={
                        'access_token': token_data.get("access_token"),
                        'refresh_token': token_data.get("refresh_token"),
                        'expires_at': datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600)),
                        'scopes': ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/documents']
                    }
                )
            
            # Create JWT tokens with internal user_id
            access_token = create_access_token(
                data={"sub": user["user_id"], "email": user["email"]},  # Use internal user_id
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            refresh_token = create_refresh_token(
                data={"sub": user["user_id"], "email": user["email"]}  # Use internal user_id
            )
            
            return AuthResponse(
                user=user,
                access_token=access_token,
                refresh_token=refresh_token
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_access_token(request: RefreshRequest):
    """
    Refresh access token using refresh token
    """
    try:
        payload = jwt.decode(
            request.refresh_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": user_id, "email": email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Fetch user from BigQuery
        user_service = get_bigquery_user_service()
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            # Fallback if user not found
            user = {
                "id": user_id,
                "email": email
            }
        
        return AuthResponse(
            user=user,
            access_token=access_token,
            refresh_token=request.refresh_token
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (client should remove tokens)
    """
    # TODO: Add token to blacklist if using Redis
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user