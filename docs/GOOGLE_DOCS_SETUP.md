# Google Docs Integration Setup

## Overview
The Google Docs integration requires a service account with proper permissions to create and manage documents.

## Setup Steps

### 1. Create a Service Account

```bash
# Create the service account
gcloud iam service-accounts create nj-voter-docs \
    --display-name="NJ Voter Docs Service" \
    --project=proj-roth

# Get the service account email
export SA_EMAIL="nj-voter-docs@proj-roth.iam.gserviceaccount.com"
```

### 2. Grant Required Permissions

```bash
# Grant necessary roles for Docs and Drive APIs
gcloud projects add-iam-policy-binding proj-roth \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/drive.file"

# Also grant Firestore access for document metadata
gcloud projects add-iam-policy-binding proj-roth \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/datastore.user"
```

### 3. Create and Download Service Account Key

```bash
# Create key file
gcloud iam service-accounts keys create \
    ~/proj-roth/service-account-key.json \
    --iam-account=${SA_EMAIL}

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/proj-roth/service-account-key.json
```

### 4. Enable Required APIs

```bash
# Enable Google Docs API
gcloud services enable docs.googleapis.com --project=proj-roth

# Enable Google Drive API  
gcloud services enable drive.googleapis.com --project=proj-roth
```

### 5. Update .env Files

Add to `backend/.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=/Users/gregorytusar/proj-roth/service-account-key.json
```

### 6. Share Documents with Users

Since the service account owns all documents, you may want to:
1. Share documents with specific users programmatically
2. Store document access permissions in Firestore
3. Implement sharing functionality in the UI

## Important Notes

- **Security**: Never commit the service account key to git. Add to `.gitignore`:
  ```
  service-account-key.json
  *-service-account*.json
  ```

- **Ownership**: All documents are owned by the service account, not individual users
- **Access Control**: Managed through Firestore metadata, not Google's permission system
- **Quotas**: Google Docs API has usage quotas - monitor in Cloud Console

## Troubleshooting

### "Insufficient authentication scopes" Error
- Ensure the service account key is properly configured
- Verify GOOGLE_APPLICATION_CREDENTIALS environment variable is set
- Check that APIs are enabled in Cloud Console

### "Permission denied" Error  
- Verify service account has proper IAM roles
- Check Firestore rules allow the service account to write

### Documents Not Visible to Users
- Documents are owned by service account, not visible in users' Google Drive
- Access through the application UI only
- Consider implementing a "share" feature if needed