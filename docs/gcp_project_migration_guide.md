# GCP Project Migration Guide: proj-roth to New Project

## Overview
This guide documents the complete process for migrating from `proj-roth` to a new GCP project with a different ID and potentially different organization/domain.

## Current Resources in proj-roth

### 1. BigQuery Datasets
- `voter_data` dataset with multiple tables:
  - `voters` (~622k records with geocoding)
  - `donations` (matched donation records)
  - `street_party_summary` (derived analytics)
  - `raw_donations` (source donation data)

### 2. Cloud Run Services
- `nj-voter-chat-app` (main application)
- Custom domain: gwanalytica.ai

### 3. Secret Manager Secrets
- `google-maps-api-key`
- `google-oauth-client-id`
- `google-oauth-client-secret`
- `api-key` (Google Search)
- `search-engine-id`

### 4. Cloud Storage Buckets
- `nj7voterfile` (voter file CSVs)
- Artifact Registry for Docker images

### 5. Cloud Build
- Build triggers and history
- Docker images in Artifact Registry

### 6. IAM & Service Accounts
- Default service accounts
- Custom service accounts for application

### 7. APIs Enabled
- BigQuery API
- Cloud Run API
- Secret Manager API
- Cloud Build API
- Maps API
- Various others

## Migration Strategy

### Phase 1: Preparation (Day 1)

#### 1.1 Create New Project
```bash
# Create new project (replace with your desired ID)
gcloud projects create greywolf-analytics-prod \
  --name="Greywolf Analytics" \
  --organization=YOUR_ORG_ID  # Optional

# Set as current project
gcloud config set project greywolf-analytics-prod

# Link billing account
gcloud billing projects link greywolf-analytics-prod \
  --billing-account=YOUR_BILLING_ACCOUNT_ID
```

#### 1.2 Enable Required APIs
```bash
# Enable all necessary APIs
gcloud services enable \
  bigquery.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  maps-backend.googleapis.com \
  storage-api.googleapis.com \
  compute.googleapis.com
```

#### 1.3 Create Service Accounts
```bash
# Create application service account
gcloud iam service-accounts create voter-app-sa \
  --display-name="Voter Application Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding greywolf-analytics-prod \
  --member="serviceAccount:voter-app-sa@greywolf-analytics-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"
```

### Phase 2: Data Migration (Day 2)

#### 2.1 Export BigQuery Data
```bash
# Export each table to Cloud Storage
bq extract \
  --destination_format=AVRO \
  --compression=SNAPPY \
  proj-roth:voter_data.voters \
  gs://proj-roth-migration/voters/*.avro

bq extract \
  --destination_format=AVRO \
  proj-roth:voter_data.donations \
  gs://proj-roth-migration/donations/*.avro

bq extract \
  --destination_format=AVRO \
  proj-roth:voter_data.street_party_summary \
  gs://proj-roth-migration/street_party/*.avro

bq extract \
  --destination_format=AVRO \
  proj-roth:voter_data.raw_donations \
  gs://proj-roth-migration/raw_donations/*.avro
```

#### 2.2 Create Datasets in New Project
```bash
# Switch to new project
gcloud config set project greywolf-analytics-prod

# Create dataset
bq mk --dataset \
  --location=US \
  --description="Voter registration and analysis data" \
  greywolf-analytics-prod:voter_data
```

#### 2.3 Import Data to New Project
```bash
# Load each table
bq load \
  --source_format=AVRO \
  greywolf-analytics-prod:voter_data.voters \
  gs://proj-roth-migration/voters/*.avro

bq load \
  --source_format=AVRO \
  greywolf-analytics-prod:voter_data.donations \
  gs://proj-roth-migration/donations/*.avro

# Repeat for other tables
```

### Phase 3: Application Migration (Day 3)

#### 3.1 Migrate Secrets
```bash
# Export secrets from old project
gcloud secrets versions access latest \
  --secret="google-maps-api-key" \
  --project=proj-roth > /tmp/maps-key.txt

# Create in new project
gcloud secrets create google-maps-api-key \
  --data-file=/tmp/maps-key.txt \
  --project=greywolf-analytics-prod

# Repeat for all secrets
```

#### 3.2 Update Application Configuration
Update all references to `proj-roth` in your codebase:

1. **backend/core/config.py**
   ```python
   PROJECT_ID = "greywolf-analytics-prod"  # Changed from proj-roth
   ```

2. **frontend/.env.production**
   ```
   REACT_APP_PROJECT_ID=greywolf-analytics-prod
   ```

3. **CLAUDE.md**
   - Update all project references

4. **All SQL queries and scripts**
   ```sql
   -- Change all references from:
   FROM `proj-roth.voter_data.voters`
   -- To:
   FROM `greywolf-analytics-prod.voter_data.voters`
   ```

#### 3.3 Build and Deploy Application
```bash
# Build new image
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/greywolf-analytics-prod/nj-voter-chat-app/nj-voter-chat-app:latest \
  --project greywolf-analytics-prod

# Deploy to Cloud Run
gcloud run deploy nj-voter-chat-app \
  --image us-central1-docker.pkg.dev/greywolf-analytics-prod/nj-voter-chat-app/nj-voter-chat-app:latest \
  --region us-central1 \
  --project greywolf-analytics-prod \
  --platform managed \
  --memory 4Gi \
  --cpu 2 \
  --timeout 600 \
  --max-instances 10 \
  --min-instances 0 \
  --session-affinity \
  --allow-unauthenticated \
  --set-secrets="GOOGLE_MAPS_API_KEY=google-maps-api-key:latest"
```

### Phase 4: Domain Migration (Day 4)

#### 4.1 Update Domain Mapping
```bash
# Remove domain mapping from old project
gcloud run domain-mappings delete \
  --domain=gwanalytica.ai \
  --region=us-central1 \
  --project=proj-roth

# Add to new project
gcloud run domain-mappings create \
  --service=nj-voter-chat-app \
  --domain=gwanalytica.ai \
  --region=us-central1 \
  --project=greywolf-analytics-prod
```

#### 4.2 Update DNS Records
Update your DNS provider to point to the new Cloud Run service IP.

### Phase 5: Validation (Day 5)

#### 5.1 Data Validation
```sql
-- Compare row counts
SELECT
  'old' as source,
  COUNT(*) as voter_count
FROM `proj-roth.voter_data.voters`
UNION ALL
SELECT
  'new' as source,
  COUNT(*) as voter_count
FROM `greywolf-analytics-prod.voter_data.voters`;
```

#### 5.2 Application Testing
- Test all chat functionality
- Verify BigQuery queries work
- Check geocoding services
- Test WebSocket connections
- Verify OAuth authentication

### Phase 6: Cutover (Day 6)

1. **Stop writes to old project**
2. **Final data sync if needed**
3. **Switch DNS to new project**
4. **Monitor for 24 hours**
5. **Keep old project for 30 days as backup**

## Rollback Plan

If issues arise:
1. Switch DNS back to old Cloud Run URL
2. Revert application config changes
3. Restore from BigQuery backups

## Post-Migration Cleanup (Day 30)

After confirming stability:
```bash
# Delete old project (DANGER - NO UNDO!)
gcloud projects delete proj-roth
```

## Cost Considerations

- **BigQuery Storage**: ~$20/month for 622k records
- **Cloud Run**: Usage-based, likely <$50/month
- **Data Transfer**: One-time cost ~$10-20 for migration
- **Keep both projects**: Double costs during transition

## Alternative: Organization Transfer

If you just want to move to a different organization/domain but keep the project ID:

```bash
# Move project to different organization
gcloud projects move proj-roth \
  --organization=NEW_ORG_ID
```

This is simpler but keeps the `proj-roth` ID in all URLs.

## Checklist

### Pre-Migration
- [ ] Backup all data
- [ ] Document all current configurations
- [ ] List all API keys and secrets
- [ ] Identify all hardcoded project IDs
- [ ] Plan maintenance window

### During Migration
- [ ] Create new project
- [ ] Enable APIs
- [ ] Migrate BigQuery data
- [ ] Migrate secrets
- [ ] Update application code
- [ ] Deploy application
- [ ] Update domain mapping
- [ ] Test thoroughly

### Post-Migration
- [ ] Monitor for 24-48 hours
- [ ] Update documentation
- [ ] Update CLAUDE.md
- [ ] Notify team members
- [ ] Schedule old project deletion

## Scripts Location

Create these helper scripts:
- `scripts/migration/export_bigquery.sh`
- `scripts/migration/import_bigquery.sh`
- `scripts/migration/migrate_secrets.sh`
- `scripts/migration/update_project_refs.sh`
- `scripts/migration/validate_migration.sh`

## Support Contacts

- GCP Support: If you have a support plan
- Team Lead: For approval of migration
- DNS Admin: For domain updates