#!/usr/bin/env python3
"""
Script to create a shared Google Drive folder for the service account.
This needs to be run with YOUR personal Google account credentials, not the service account.
"""

import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    """Create a shared folder and share it with the service account."""
    
    SERVICE_ACCOUNT_EMAIL = "nj-voter-docs@proj-roth.iam.gserviceaccount.com"
    
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # First, you need to create OAuth 2.0 credentials for a desktop app
            # in the Google Cloud Console and download the credentials.json file
            print("\n" + "="*60)
            print("IMPORTANT: OAuth Setup Required")
            print("="*60)
            print("\nSince browser OAuth is blocked for sensitive scopes,")
            print("we'll use the gcloud CLI to create the folder instead.")
            print("\nPlease follow these steps manually:\n")
            print("1. Go to https://drive.google.com")
            print("2. Create a new folder called 'NJ Voter Documents'")
            print(f"3. Right-click the folder and share it with: {SERVICE_ACCOUNT_EMAIL}")
            print("4. Give the service account 'Editor' permissions")
            print("5. Copy the folder ID from the URL (the part after /folders/)")
            print("   Example: If URL is https://drive.google.com/drive/folders/1ABC123xyz")
            print("   Then folder ID is: 1ABC123xyz")
            print("\n" + "="*60)
            
            folder_id = input("\nEnter the folder ID after completing the above steps: ").strip()
            
            if folder_id:
                # Save the folder ID to a config file
                config_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'google_drive_config.json')
                import json
                with open(config_path, 'w') as f:
                    json.dump({
                        'shared_folder_id': folder_id,
                        'service_account_email': SERVICE_ACCOUNT_EMAIL
                    }, f, indent=2)
                print(f"\n✅ Configuration saved to: {config_path}")
                print(f"Folder ID: {folder_id}")
                print("\nThe service account can now create documents in this folder!")
            return

    # Build the Drive service
    service = build('drive', 'v3', credentials=creds)
    
    # Create a folder
    file_metadata = {
        'name': 'NJ Voter Documents',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    folder = service.files().create(body=file_metadata, fields='id').execute()
    folder_id = folder.get('id')
    print(f'Created folder with ID: {folder_id}')
    
    # Share the folder with the service account
    def share_folder(folder_id, email):
        permission = {
            'type': 'user',
            'role': 'writer',  # or 'owner' if you want full control
            'emailAddress': email
        }
        
        try:
            service.permissions().create(
                fileId=folder_id,
                body=permission,
                fields='id',
            ).execute()
            print(f'Shared folder with {email}')
        except Exception as e:
            print(f'Error sharing folder: {e}')
    
    share_folder(folder_id, SERVICE_ACCOUNT_EMAIL)
    
    # Save the folder ID to a config file
    config_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'google_drive_config.json')
    import json
    with open(config_path, 'w') as f:
        json.dump({
            'shared_folder_id': folder_id,
            'service_account_email': SERVICE_ACCOUNT_EMAIL
        }, f, indent=2)
    
    print(f"\n✅ Configuration saved to: {config_path}")
    print(f"Folder ID: {folder_id}")
    print("\nThe service account can now create documents in this folder!")

if __name__ == '__main__':
    main()