#!/bin/bash
set -e

echo "==================================="
echo "OAuth Display Name Fix for Greywolf Analytics"
echo "==================================="
echo ""
echo "This script will guide you through fixing the OAuth display name issue."
echo ""

PROJECT_ID="proj-roth"

echo "STEP 1: Manual Actions Required in Google Cloud Console"
echo "--------------------------------------------------------"
echo ""
echo "1. First, let's check if there's an IAP brand (this might be overriding your OAuth consent screen):"
echo "   Go to: https://console.cloud.google.com/security/iap?project=$PROJECT_ID"
echo "   - If you see any configuration there, note it down"
echo ""
echo "2. Now go to the OAuth consent screen:"
echo "   https://console.cloud.google.com/apis/credentials/consent?project=$PROJECT_ID"
echo ""
echo "3. Check the 'User Type':"
echo "   - If it says 'Internal', only your org users can see it"
echo "   - If it says 'External', it's public"
echo ""
echo "4. Click 'EDIT APP' and go through EVERY page:"
echo "   Page 1 - OAuth consent screen:"
echo "   - App name: Greywolf Analytics"
echo "   - User support email: (your email)"
echo "   - App logo: (optional, but might help)"
echo "   - Application home page: https://nj-voter-chat-app-nwv4o72vjq-uc.a.run.app"
echo "   - Application privacy policy: (can leave blank)"
echo "   - Application terms of service: (can leave blank)"
echo "   - Authorized domains: Add 'run.app' if not there"
echo "   - Developer contact: (your email)"
echo "   Click 'SAVE AND CONTINUE'"
echo ""
echo "   Page 2 - Scopes:"
echo "   - Should show: email, profile, openid"
echo "   Click 'SAVE AND CONTINUE'"
echo ""
echo "   Page 3 - Test users (if in Testing mode):"
echo "   - Add your email if not there"
echo "   Click 'SAVE AND CONTINUE'"
echo ""
echo "   Page 4 - Summary:"
echo "   - Verify 'App name' shows 'Greywolf Analytics'"
echo "   Click 'BACK TO DASHBOARD'"
echo ""
read -p "Press Enter after completing the above steps..."

echo ""
echo "STEP 2: Creating a Fresh OAuth 2.0 Client ID"
echo "--------------------------------------------"
echo ""
echo "Since the display name isn't updating, let's create a brand new OAuth client:"
echo ""
echo "1. Go to: https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
echo "2. Click '+ CREATE CREDENTIALS' -> 'OAuth client ID'"
echo "3. Configure as follows:"
echo "   - Application type: Web application"
echo "   - Name: Greywolf Analytics Web Client"
echo "   - Authorized JavaScript origins:"
echo "     * https://nj-voter-chat-app-nwv4o72vjq-uc.a.run.app"
echo "     * http://localhost:3000"
echo "   - Authorized redirect URIs:"
echo "     * https://nj-voter-chat-app-nwv4o72vjq-uc.a.run.app/login"
echo "     * http://localhost:3000/login"
echo "4. Click 'CREATE'"
echo "5. Copy the Client ID and Client Secret"
echo ""
read -p "Enter the new Client ID: " NEW_CLIENT_ID
read -p "Enter the new Client Secret: " NEW_CLIENT_SECRET

echo ""
echo "STEP 3: Updating Secrets"
echo "------------------------"
echo "Updating Google Secret Manager..."

echo -n "$NEW_CLIENT_ID" | gcloud secrets versions add google-oauth-client-id --data-file=- --project=$PROJECT_ID
echo -n "$NEW_CLIENT_SECRET" | gcloud secrets versions add google-oauth-client-secret --data-file=- --project=$PROJECT_ID

echo "✓ Secrets updated"

echo ""
echo "STEP 4: Updating Frontend Configuration"
echo "---------------------------------------"

# Update .env files
cat > frontend/.env <<EOF
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=http://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=$NEW_CLIENT_ID
EOF

cat > frontend/.env.production <<EOF
REACT_APP_API_URL=
REACT_APP_GOOGLE_CLIENT_ID=$NEW_CLIENT_ID
REACT_APP_MAPBOX_TOKEN=pk.eyJ1IjoiZ3R1c2FyIiwiYSI6ImNrd3duaWRmdDFwem8ydnFmdXc3aXc2dnYifQ.FI96_jN-gA2K0gzQMJKO-w
EOF

echo "✓ Frontend environment files updated"

echo ""
echo "STEP 5: Rebuilding and Deploying"
echo "---------------------------------"
echo "This will rebuild the frontend with the new Client ID and deploy everything"
echo ""
read -p "Ready to deploy? (y/n): " DEPLOY_CONFIRM

if [[ $DEPLOY_CONFIRM == "y" ]]; then
    cd frontend
    echo "Building frontend..."
    npm run build
    cd ..
    
    echo "Deploying to Cloud Run..."
    PROJECT_ID=$PROJECT_ID REGION=us-central1 bash scripts/deploy_nj_voter_chat.sh
    
    echo ""
    echo "✓ Deployment complete!"
    echo ""
    echo "IMPORTANT: Wait 2-3 minutes for the changes to propagate, then:"
    echo "1. Open an incognito/private browser window"
    echo "2. Go to: https://nj-voter-chat-app-nwv4o72vjq-uc.a.run.app"
    echo "3. Click 'Sign in with Google'"
    echo "4. It should now show 'Greywolf Analytics'"
else
    echo "Skipped deployment. Run this when ready:"
    echo "  cd frontend && npm run build && cd .."
    echo "  PROJECT_ID=$PROJECT_ID REGION=us-central1 bash scripts/deploy_nj_voter_chat.sh"
fi

echo ""
echo "==================================="
echo "If it STILL shows the URL instead of 'Greywolf Analytics':"
echo "1. The project might have an IAP OAuth brand overriding settings"
echo "2. Try deleting the OLD OAuth client (keep the new one)"
echo "3. Check if your Google Workspace has restrictions"
echo "4. Contact Google Cloud Support - this might be a console bug"
echo "==================================="