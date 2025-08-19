"""
Test script to verify OAuth secrets are accessible
"""
import streamlit as st
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.nj_voter_chat_adk.secret_manager import SecretManagerClient
from agents.nj_voter_chat_adk.auth import GoogleAuthenticator

st.set_page_config(page_title="OAuth Secret Test", page_icon="🔐")

st.title("OAuth Secret Configuration Test")

# Test environment variables
st.header("Environment Variables")
st.write(f"GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'NOT SET')}")
st.write(f"GOOGLE_CLOUD_REGION: {os.getenv('GOOGLE_CLOUD_REGION', 'NOT SET')}")
st.write(f"OAUTH_REDIRECT_URI: {os.getenv('OAUTH_REDIRECT_URI', 'NOT SET')}")

# Test Secret Manager directly
st.header("Secret Manager Direct Test")
try:
    sm_client = SecretManagerClient()
    
    # Try to get client ID
    client_id = sm_client.get_secret("google-oauth-client-id")
    if client_id:
        st.success(f"✅ Client ID retrieved: {client_id[:20]}...{client_id[-10:]}")
    else:
        st.error("❌ Client ID not retrieved (returned None)")
    
    # Try to get client secret
    client_secret = sm_client.get_secret("google-oauth-client-secret")
    if client_secret:
        st.success(f"✅ Client Secret retrieved: {'*' * 10}")
    else:
        st.error("❌ Client Secret not retrieved (returned None)")
        
    # Try to get JWT secret
    jwt_secret = sm_client.get_secret("jwt-secret-key")
    if jwt_secret:
        st.success(f"✅ JWT Secret retrieved: {'*' * 10}")
    else:
        st.error("❌ JWT Secret not retrieved (returned None)")
        
except Exception as e:
    st.error(f"Error accessing Secret Manager: {e}")
    import traceback
    st.code(traceback.format_exc())

# Test GoogleAuthenticator
st.header("GoogleAuthenticator Test")
try:
    auth = GoogleAuthenticator()
    st.write(f"Client ID in auth: {auth.client_id[:20] if auth.client_id else 'EMPTY'}...")
    st.write(f"Client Secret in auth: {'SET' if auth.client_secret else 'NOT SET'}")
    st.write(f"JWT Secret in auth: {'SET' if auth.jwt_secret else 'NOT SET'}")
    
    if auth.client_id and auth.client_secret:
        st.success("✅ OAuth credentials loaded successfully!")
        
        # Try to generate auth URL
        try:
            auth_url = auth.get_google_auth_url()
            st.write("OAuth URL generated successfully!")
            st.code(auth_url[:100] + "...")
        except Exception as e:
            st.error(f"Error generating OAuth URL: {e}")
    else:
        st.error("❌ OAuth credentials not loaded properly")
        
except Exception as e:
    st.error(f"Error initializing GoogleAuthenticator: {e}")
    import traceback
    st.code(traceback.format_exc())