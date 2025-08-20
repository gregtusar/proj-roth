#!/usr/bin/env python3
"""
Fix the OAuth client secret in Secret Manager
"""
import json
from google.cloud import secretmanager

def fix_oauth_secret():
    """Extract and update the OAuth client secret"""
    
    project_id = "proj-roth"
    client = secretmanager.SecretManagerServiceClient()
    
    # Get the current secret
    secret_name = f"projects/{project_id}/secrets/google-oauth-client-secret/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    current_value = response.payload.data.decode("UTF-8")
    
    print("Current secret value (first 100 chars):")
    print(current_value[:100])
    
    # Check if it's JSON
    if current_value.startswith('{"web":'):
        print("\nDetected JSON format. Extracting client_secret...")
        
        # Clean up the value
        current_value = current_value.rstrip('%').strip()
        
        try:
            oauth_config = json.loads(current_value)
            actual_secret = oauth_config['web']['client_secret']
            
            print(f"Extracted client_secret: {actual_secret[:10]}...")
            
            # Ask for confirmation
            print("\nThe actual client secret is:")
            print(f"  {actual_secret}")
            print("\nTo update the secret with just this value, run:")
            print(f"echo -n '{actual_secret}' | gcloud secrets versions add google-oauth-client-secret --data-file=- --project={project_id}")
            
            return actual_secret
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print("Raw value length:", len(current_value))
            print("Last 50 chars:", current_value[-50:])
    else:
        print("Secret is already in correct format (not JSON)")
        print(f"Value: {current_value[:10]}...")
    
    return None

if __name__ == "__main__":
    fix_oauth_secret()