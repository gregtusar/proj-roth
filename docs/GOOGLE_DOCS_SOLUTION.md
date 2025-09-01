# Google Docs Integration - Solution

## The Problem
Service accounts have severe limitations with Google Docs:
1. **No storage quota** - Service accounts can't create documents in their own Drive
2. **No Workspace access** - Can't directly create Google Docs without a Workspace domain
3. **Permission issues** - Even with proper IAM roles, Docs API requires user context

## Recommended Solutions

### Option 1: Use User's OAuth Token (Recommended)
Instead of using the service account, use the logged-in user's Google OAuth token to create documents in their own Drive.

**Pros:**
- Documents are owned by the actual user
- No storage limitations
- Natural permissions model
- Documents appear in user's Drive

**Cons:**
- Requires additional OAuth scopes during login
- Need to handle token refresh

### Option 2: Use Cloud Storage + Export
Store documents in Cloud Storage and export to Google Docs format when needed.

**Pros:**
- Simple implementation
- No quota issues
- Full control over documents

**Cons:**
- Not "real" Google Docs until exported
- Limited collaboration features

### Option 3: Use Firestore for Storage
Store document content directly in Firestore with a rich text editor in the UI.

**Pros:**
- Simplest implementation
- No external dependencies
- Fast and reliable

**Cons:**
- Not Google Docs at all
- Need to build editing UI

## Implementation for Option 1

1. Update OAuth scopes during login to include:
   - `https://www.googleapis.com/auth/drive.file`
   - `https://www.googleapis.com/auth/documents`

2. Store user's OAuth tokens securely

3. Use user's token to create documents:
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Use user's OAuth credentials
creds = Credentials(
    token=user_access_token,
    refresh_token=user_refresh_token,
    token_uri='https://oauth2.googleapis.com/token',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scopes=['https://www.googleapis.com/auth/drive.file', 
            'https://www.googleapis.com/auth/documents']
)

# Create document with user's credentials
docs_service = build('docs', 'v1', credentials=creds)
doc = docs_service.documents().create(body={'title': 'My Document'}).execute()
```

4. Optionally move to shared folder for organization

## Current Status
The service account approach won't work due to storage quota limitations. We need to either:
1. Implement user OAuth token approach
2. Switch to a different storage solution
3. Set up Google Workspace with domain-wide delegation (enterprise only)