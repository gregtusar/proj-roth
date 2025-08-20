#!/usr/bin/env python3
"""
Check OAuth configuration and test the exact flow
"""
import os
import sys
from google.cloud import secretmanager

def check_oauth_config():
    """Check OAuth configuration details"""
    
    print("=" * 60)
    print("OAuth Configuration Check")
    print("=" * 60)
    
    project_id = "proj-roth"
    
    # Get secrets
    try:
        client = secretmanager.SecretManagerServiceClient()
        
        # Get Client ID
        name = f"projects/{project_id}/secrets/google-oauth-client-id/versions/latest"
        response = client.access_secret_version(request={"name": name})
        client_id = response.payload.data.decode("UTF-8")
        
        # Get Client Secret  
        name = f"projects/{project_id}/secrets/google-oauth-client-secret/versions/latest"
        response = client.access_secret_version(request={"name": name})
        client_secret = response.payload.data.decode("UTF-8")
        
        print(f"\n1. OAuth Client Details:")
        print(f"   Client ID: {client_id}")
        print(f"   Client Secret: {client_secret[:10]}... (hidden)")
        
    except Exception as e:
        print(f"Error getting secrets: {e}")
        return
    
    # Check what redirect URI would be used
    print(f"\n2. Redirect URI Configuration:")
    
    # Check environment
    port = os.getenv("PORT", "not set")
    print(f"   PORT env var: {port}")
    
    # Determine redirect URI based on auth.py logic
    default_uri = "https://nj-voter-chat-nwv4o72vjq-uc.a.run.app"
    if port != "8080":  # Local development
        default_uri = "http://localhost:8501"
    
    redirect_uri = os.getenv("OAUTH_REDIRECT_URI", default_uri)
    print(f"   Computed redirect URI: {redirect_uri}")
    print(f"   OAUTH_REDIRECT_URI env: {os.getenv('OAUTH_REDIRECT_URI', 'not set')}")
    
    # Generate auth URL
    print(f"\n3. OAuth Flow Test:")
    try:
        from google_auth_oauthlib.flow import Flow
        
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
        
        auth_url, state = flow.authorization_url(
            prompt="consent",
            access_type="offline",
            include_granted_scopes="true"
        )
        
        print(f"   ✅ Flow created successfully")
        print(f"   State: {state[:20]}...")
        print(f"\n   Full auth URL:")
        print(f"   {auth_url}")
        
        # Parse the auth URL to show parameters
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)
        
        print(f"\n4. OAuth URL Parameters:")
        print(f"   client_id: {params.get('client_id', ['not found'])[0][:50]}...")
        print(f"   redirect_uri: {params.get('redirect_uri', ['not found'])[0]}")
        print(f"   response_type: {params.get('response_type', ['not found'])[0]}")
        print(f"   scope: {params.get('scope', ['not found'])[0][:100]}...")
        
    except Exception as e:
        print(f"   ❌ Error creating flow: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 60)
    print("IMPORTANT: The redirect_uri shown above MUST be added to your")
    print("OAuth client's 'Authorized redirect URIs' in Google Cloud Console:")
    print("https://console.cloud.google.com/apis/credentials")
    print("=" * 60)

if __name__ == "__main__":
    check_oauth_config()