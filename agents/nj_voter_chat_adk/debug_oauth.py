#!/usr/bin/env python3
"""
Debug script to test OAuth authentication step by step
"""
import os
import sys
import traceback

# Fix path to ensure we import the correct local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
# Insert at the beginning to take precedence
sys.path.insert(0, project_root)
sys.path.insert(0, current_dir)

from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

def test_oauth_flow():
    """Test OAuth flow with detailed debugging"""
    
    print("=" * 60)
    print("OAuth Debug Test")
    print("=" * 60)
    
    # Step 1: Load secrets
    print("\n1. Loading OAuth secrets...")
    try:
        # Import directly without the agents prefix to avoid conflicts
        from .secret_manager import SecretManagerClient
        sm_client = SecretManagerClient()
        
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        if not client_id:
            client_id = sm_client.get_secret("google-oauth-client-id")
        
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        if not client_secret:
            client_secret = sm_client.get_secret("google-oauth-client-secret")
        
        print(f"   Client ID: {client_id[:30]}..." if client_id else "   Client ID: NOT FOUND")
        print(f"   Client Secret: {'*' * 10} (hidden)" if client_secret else "   Client Secret: NOT FOUND")
        
        if not client_id or not client_secret:
            print("\n❌ FAILED: OAuth credentials not found")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: Error loading secrets: {e}")
        print(traceback.format_exc())
        return False
    
    # Step 2: Test creating Flow
    print("\n2. Creating OAuth Flow...")
    try:
        redirect_uri = "https://nj-voter-chat-nwv4o72vjq-uc.a.run.app"
        print(f"   Redirect URI: {redirect_uri}")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
            redirect_uri=redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(
            prompt="consent",
            access_type="offline",
            include_granted_scopes="true"
        )
        
        print(f"   ✅ Flow created successfully")
        print(f"   Auth URL (first 100 chars): {auth_url[:100]}...")
        
    except Exception as e:
        print(f"\n❌ FAILED: Error creating OAuth flow: {e}")
        print(traceback.format_exc())
        return False
    
    # Step 3: Test token verification setup
    print("\n3. Testing token verification setup...")
    try:
        request = requests.Request()
        print("   ✅ Request object created successfully")
        
        # We can't actually verify a token without a real one, but we can check the setup
        print(f"   Client ID for verification: {client_id[:30]}...")
        
    except Exception as e:
        print(f"\n❌ FAILED: Error setting up token verification: {e}")
        print(traceback.format_exc())
        return False
    
    print("\n" + "=" * 60)
    print("✅ All OAuth components are configured correctly!")
    print("=" * 60)
    print("\nThe issue might be:")
    print("1. The authorization code has expired (they're only valid for a few minutes)")
    print("2. The code is being used twice (they're single-use)")
    print("3. Network/firewall issues preventing token exchange")
    print("4. The OAuth client configuration in Google Cloud Console")
    print("\nNext steps:")
    print("1. Try logging in again with a fresh auth flow")
    print("2. Check Cloud Run logs: gcloud run logs read nj-voter-chat --limit=50")
    print("3. Verify OAuth client settings in Google Cloud Console")
    
    return True

if __name__ == "__main__":
    success = test_oauth_flow()
    sys.exit(0 if success else 1)