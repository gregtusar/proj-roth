# Deployment Verification Guide

After running the deployment script, verify the deployment:

## 1. Check the service URL
```bash
gcloud run services describe nj-voter-chat --region=us-central1 --format='value(status.url)'
```

## 2. Test the deployed application
```bash
curl -f "$(gcloud run services describe nj-voter-chat --region=us-central1 --format='value(status.url)')"
```

## 3. Check recent revisions
```bash
gcloud run revisions list --service=nj-voter-chat --region=us-central1
```

## 4. Verify traffic distribution
```bash
gcloud run services describe nj-voter-chat --region=us-central1 --format='table(status.traffic[].revisionName,status.traffic[].percent)'
```

## 5. Check deployment logs
```bash
gcloud run services logs tail nj-voter-chat --region=us-central1
```

## Troubleshooting

### If you see the old version:
1. Check if the latest revision is receiving 100% traffic
2. Verify the Docker image was rebuilt with a new tag
3. Ensure the deployment didn't use `SKIP_BUILD=true`

### If deployment fails:
1. Check gcloud authentication: `gcloud auth list`
2. Verify project access: `gcloud projects describe proj-roth`
3. Check service account permissions: `gcloud iam service-accounts describe agent-runner@proj-roth.iam.gserviceaccount.com`

### Force a fresh deployment:
```bash
# This ensures a completely new image is built and deployed
SKIP_BUILD=false ./scripts/enhanced_deploy_nj_voter_chat.sh
```
