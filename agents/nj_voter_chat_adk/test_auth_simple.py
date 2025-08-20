#!/usr/bin/env python3
"""
Simple test to check OAuth configuration without import conflicts
"""
import os
from google.cloud import secretmanager

def test_secrets():
    """Test if OAuth secrets are accessible"""
    
    print("=" * 60)
    print("OAuth Configuration Test")
    print("=" * 60)
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
    print(f"\nProject ID: {project_id}")
    
    # Test Secret Manager access
    print("\n1. Testing Secret Manager access...")
    try:
        client = secretmanager.SecretManagerServiceClient()
        
        # Test each secret
        secrets_to_test = [
            ("google-oauth-client-id", "OAuth Client ID"),
            ("google-oauth-client-secret", "OAuth Client Secret"),
            ("jwt-secret-key", "JWT Secret Key")
        ]
        
        for secret_name, display_name in secrets_to_test:
            try:
                name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                secret_value = response.payload.data.decode("UTF-8")
                
                if secret_value:
                    if "client-id" in secret_name:
                        print(f"   ✅ {display_name}: {secret_value[:30]}...")
                    else:
                        print(f"   ✅ {display_name}: {'*' * 10} (hidden)")
                else:
                    print(f"   ❌ {display_name}: Empty value")
                    
            except Exception as e:
                print(f"   ❌ {display_name}: {str(e)[:100]}")
                
    except Exception as e:
        print(f"   ❌ Cannot access Secret Manager: {e}")
        return False
    
    # Test environment variables
    print("\n2. Testing environment variables...")
    env_vars = [
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "OAUTH_REDIRECT_URI"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if "CREDENTIALS" in var:
                print(f"   ✅ {var}: {value[:50]}...")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ⚠️  {var}: Not set")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    import sys
    success = test_secrets()
    sys.exit(0 if success else 1)