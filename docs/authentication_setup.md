# Google OAuth Authentication Setup

This document describes the authentication system added to the NJ Voter Chat application.

## Overview

The application now requires users to authenticate with their Google account before accessing the voter data analysis system. Only users whose email addresses are pre-authorized in the database can access the system.

## Components

### 1. Authentication Module (`auth.py`)
- Handles Google OAuth flow
- Manages JWT tokens (7-day expiry)
- Verifies user authorization against BigQuery table
- Updates user login statistics

### 2. Login Page (`login.py`)
- Displays branded login screen with logo
- "Continue with Google" button
- Handles OAuth callbacks
- Redirects to main app on successful authentication

### 3. Modified Main App (`app_streamlit.py`)
- Checks authentication before allowing access
- Displays user info and avatar in top-right
- Provides logout button in sidebar
- Redirects to login if not authenticated

### 4. User Database Table
- Table: `proj-roth.voter_data.authorized_users`
- Stores authorized user emails and profiles
- Tracks login count and last login time
- Supports role-based access (viewer, analyst, admin)

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r agents/nj_voter_chat_adk/requirements.txt
```

### 2. Configure Google OAuth

Run the setup script:
```bash
cd agents/nj_voter_chat_adk
./setup_oauth.sh
```

Or manually:

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create an OAuth 2.0 Client ID
3. Set application type to "Web application"
4. Add authorized redirect URIs:
   - `http://localhost:8501` (for local development)
   - `https://YOUR-CLOUD-RUN-URL` (for production)
5. Store credentials in Secret Manager:
   - `google-oauth-client-id`
   - `google-oauth-client-secret`
   - `jwt-secret-key`

### 3. Create User Table

Run the SQL schema:
```bash
bq query --use_legacy_sql=false < config/user_table_schema.sql
```

### 4. Add Authorized Users

Add users to the `authorized_users` table:
```sql
INSERT INTO `proj-roth.voter_data.authorized_users` (
    user_id,
    email,
    full_name,
    is_active,
    role
) VALUES (
    GENERATE_UUID(),
    'user@example.com',
    'User Name',
    TRUE,
    'viewer'
);
```

## Environment Variables

For local development:
```bash
export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
export JWT_SECRET_KEY="your-jwt-secret"
export OAUTH_REDIRECT_URI="http://localhost:8501"
```

## User Roles

- **viewer**: Can query and view data
- **analyst**: Can perform advanced analysis
- **admin**: Full system access and user management

## Security Features

- JWT tokens expire after 7 days
- Only pre-authorized emails can access
- All user activity is logged
- Secure token storage in session state
- OAuth state validation
- HTTPS-only in production

## Testing

1. Start the application:
```bash
streamlit run agents/nj_voter_chat_adk/app_streamlit.py
```

2. You should be redirected to the login page
3. Click "Continue with Google"
4. Authenticate with a Google account
5. If authorized, you'll be redirected to the main chat interface
6. User info appears in top-right corner
7. Logout button available in sidebar

## Deployment Considerations

For Cloud Run deployment:
1. Update redirect URI to production URL
2. Ensure Secret Manager permissions are configured
3. Update environment variables in deployment script
4. Test OAuth flow with production URL

## Troubleshooting

### "Access denied" error
- Ensure user email is in `authorized_users` table
- Check that `is_active` is TRUE for the user

### OAuth redirect errors
- Verify redirect URI matches exactly in OAuth config
- Check that all URIs are added to Google OAuth settings

### Token expiry issues
- Tokens expire after 7 days by design
- Users need to re-authenticate after expiry
- Can adjust `token_expiry_days` in `auth.py` if needed