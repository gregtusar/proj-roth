# Setup New OAuth Client for Greywolf Analytica

If the OAuth consent screen continues to show the URL instead of "Greywolf Analytica", follow these steps to create a new OAuth client:

## Step 1: Create New OAuth 2.0 Client ID

1. Go to: https://console.cloud.google.com/apis/credentials?project=proj-roth
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Configure as follows:
   - **Application type**: Web application
   - **Name**: Greywolf Analytica OAuth Client
   - **Authorized JavaScript origins**:
     - `https://nj-voter-chat-app-nwv4o72vjq-uc.a.run.app`
     - `http://localhost:3000`
   - **Authorized redirect URIs**:
     - `https://nj-voter-chat-app-nwv4o72vjq-uc.a.run.app/login`
     - `http://localhost:3000/login`
4. Click "CREATE"
5. Copy the new Client ID and Client Secret

## Step 2: Update Secrets in Google Secret Manager

```bash
# Update the client ID secret
echo -n "YOUR_NEW_CLIENT_ID" | gcloud secrets versions add google-oauth-client-id --data-file=-

# Update the client secret
echo -n "YOUR_NEW_CLIENT_SECRET" | gcloud secrets versions add google-oauth-client-secret --data-file=-
```

## Step 3: Update Frontend Environment

1. Update `/Users/gregorytusar/proj-roth/frontend/.env`:
```
REACT_APP_GOOGLE_CLIENT_ID=YOUR_NEW_CLIENT_ID
```

2. Update `/Users/gregorytusar/proj-roth/frontend/.env.production`:
```
REACT_APP_GOOGLE_CLIENT_ID=YOUR_NEW_CLIENT_ID
```

## Step 4: Rebuild and Deploy

```bash
# From project root
cd /Users/gregorytusar/proj-roth

# Rebuild frontend (important for new client ID)
cd frontend
npm run build
cd ..

# Deploy to Cloud Run
PROJECT_ID=proj-roth REGION=us-central1 bash scripts/deploy_nj_voter_chat.sh
```

## Step 5: Verify OAuth Consent Screen

Before creating the new client, ensure the OAuth consent screen is properly configured:

1. Go to: https://console.cloud.google.com/apis/credentials/consent?project=proj-roth
2. Click "EDIT APP"
3. Ensure these are set:
   - **App name**: Greywolf Analytica
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Save all changes

## Troubleshooting

If the display name still shows the URL:
1. The OAuth consent screen might be in "Internal" mode - check the User Type
2. Clear ALL Google cookies or use a completely different browser
3. The project might have multiple OAuth brands - check IAP settings
4. Wait 5-10 minutes for changes to propagate

## Current OAuth Client
Current Client ID: 169579073940-vp8lqqc0n1bpi74nlonqeqhmqo201r1d.apps.googleusercontent.com