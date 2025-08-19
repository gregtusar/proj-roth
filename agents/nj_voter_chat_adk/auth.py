"""
Google OAuth authentication module for NJ Voter Chat
"""
import os
import streamlit as st
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import uuid
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.cloud import bigquery
import logging

logger = logging.getLogger(__name__)

class GoogleAuthenticator:
    """Handle Google OAuth authentication and user management"""
    
    def __init__(self):
        self.client_id = self._get_client_id()
        self.client_secret = self._get_client_secret()
        # Use the actual Cloud Run URL or localhost for development
        default_uri = "https://nj-voter-chat-nwv4o72vjq-uc.a.run.app"
        if os.getenv("PORT") != "8080":  # Local development
            default_uri = "http://localhost:8501"
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI", default_uri)
        self.bigquery_client = bigquery.Client(project="proj-roth")
        self.jwt_secret = self._get_jwt_secret()
        self.token_expiry_days = 7
        
    def _get_client_id(self) -> str:
        """Get Google OAuth client ID from environment or Secret Manager"""
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        if not client_id:
            try:
                from agents.nj_voter_chat_adk.secret_manager import SecretManagerClient
                sm_client = SecretManagerClient()
                client_id = sm_client.get_secret("google-oauth-client-id")
            except Exception as e:
                logger.warning(f"Could not retrieve OAuth client ID: {e}")
        return client_id or ""
    
    def _get_client_secret(self) -> str:
        """Get Google OAuth client secret from environment or Secret Manager"""
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        if not client_secret:
            try:
                from agents.nj_voter_chat_adk.secret_manager import SecretManagerClient
                sm_client = SecretManagerClient()
                client_secret = sm_client.get_secret("google-oauth-client-secret")
            except Exception as e:
                logger.warning(f"Could not retrieve OAuth client secret: {e}")
        return client_secret or ""
    
    def _get_jwt_secret(self) -> str:
        """Get JWT secret for token signing"""
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            try:
                from agents.nj_voter_chat_adk.secret_manager import SecretManagerClient
                sm_client = SecretManagerClient()
                jwt_secret = sm_client.get_secret("jwt-secret-key")
            except Exception as e:
                logger.warning(f"Could not retrieve JWT secret: {e}")
                # Generate a random secret if none exists
                jwt_secret = str(uuid.uuid4())
        return jwt_secret
    
    def get_google_auth_url(self) -> str:
        """Generate Google OAuth authorization URL"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
            redirect_uri=self.redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(
            prompt="consent",
            access_type="offline",
            include_granted_scopes="true"
        )
        return auth_url
    
    def handle_callback(self, code: str) -> Optional[Dict[str, Any]]:
        """Handle OAuth callback and extract user info"""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                ],
                redirect_uri=self.redirect_uri
            )
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Verify the token and get user info
            request = requests.Request()
            id_info = id_token.verify_oauth2_token(
                credentials.id_token, request, self.client_id
            )
            
            return {
                "google_id": id_info.get("sub"),
                "email": id_info.get("email"),
                "full_name": id_info.get("name"),
                "given_name": id_info.get("given_name"),
                "family_name": id_info.get("family_name"),
                "picture_url": id_info.get("picture"),
                "locale": id_info.get("locale"),
            }
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            return None
    
    def check_user_authorized(self, email: str) -> bool:
        """Check if user email is in authorized users table"""
        try:
            query = """
                SELECT email, is_active
                FROM `proj-roth.voter_data.authorized_users`
                WHERE email = @email AND is_active = TRUE
                LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("email", "STRING", email)
                ]
            )
            results = self.bigquery_client.query(query, job_config=job_config).result()
            return len(list(results)) > 0
        except Exception as e:
            logger.error(f"Error checking user authorization: {e}")
            return False
    
    def create_or_update_user(self, user_info: Dict[str, Any]) -> Optional[str]:
        """Create or update user in database, return user_id"""
        try:
            # Check if user exists
            check_query = """
                SELECT user_id, email
                FROM `proj-roth.voter_data.authorized_users`
                WHERE email = @email
                LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("email", "STRING", user_info["email"])
                ]
            )
            results = list(self.bigquery_client.query(check_query, job_config=job_config).result())
            
            if results:
                # Update existing user
                user_id = results[0].user_id
                update_query = """
                    UPDATE `proj-roth.voter_data.authorized_users`
                    SET 
                        last_login = CURRENT_TIMESTAMP(),
                        login_count = login_count + 1,
                        google_id = @google_id,
                        full_name = @full_name,
                        given_name = @given_name,
                        family_name = @family_name,
                        picture_url = @picture_url,
                        locale = @locale
                    WHERE email = @email
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("email", "STRING", user_info["email"]),
                        bigquery.ScalarQueryParameter("google_id", "STRING", user_info.get("google_id", "")),
                        bigquery.ScalarQueryParameter("full_name", "STRING", user_info.get("full_name", "")),
                        bigquery.ScalarQueryParameter("given_name", "STRING", user_info.get("given_name", "")),
                        bigquery.ScalarQueryParameter("family_name", "STRING", user_info.get("family_name", "")),
                        bigquery.ScalarQueryParameter("picture_url", "STRING", user_info.get("picture_url", "")),
                        bigquery.ScalarQueryParameter("locale", "STRING", user_info.get("locale", "")),
                    ]
                )
                self.bigquery_client.query(update_query, job_config=job_config).result()
                return user_id
            else:
                # User not in authorized list
                logger.warning(f"User {user_info['email']} attempted login but is not authorized")
                return None
                
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            return None
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """Create JWT access token for authenticated user"""
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.utcnow() + timedelta(days=self.token_expiry_days),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT access token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.info("Access token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid access token: {e}")
            return None
    
    def logout(self):
        """Clear authentication from session"""
        if "access_token" in st.session_state:
            del st.session_state["access_token"]
        if "user_info" in st.session_state:
            del st.session_state["user_info"]
        if "authenticated" in st.session_state:
            del st.session_state["authenticated"]


def require_auth(func):
    """Decorator to require authentication for Streamlit pages"""
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authenticated", False):
            st.error("Please log in to access this page")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def check_authentication() -> bool:
    """Check if user is authenticated with valid token"""
    if "access_token" not in st.session_state:
        return False
    
    auth = GoogleAuthenticator()
    user_data = auth.verify_access_token(st.session_state["access_token"])
    
    if user_data:
        st.session_state["authenticated"] = True
        st.session_state["user_info"] = user_data
        return True
    else:
        # Token invalid or expired
        st.session_state["authenticated"] = False
        if "access_token" in st.session_state:
            del st.session_state["access_token"]
        return False