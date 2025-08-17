# Enhanced Cloud Run Deployment Guide

## Overview

The `enhanced_deploy_nj_voter_chat.sh` script provides an improved deployment experience for the NJ Voter Chat application to Google Cloud Run. It builds upon the existing `deploy_nj_voter_chat.sh` script with additional features for production deployments.

## Key Features

### 🚀 Enhanced Deployment Options
- **Dry Run Mode**: Test deployments without making changes
- **Environment-Specific Deployments**: Support for staging, production, etc.
- **Skip Build Option**: Deploy existing images without rebuilding
- **Configurable Resource Limits**: CPU, memory, instance scaling

### 🛡️ Safety & Reliability
- **Health Checks**: Automatic post-deployment validation
- **Automatic Rollback**: Revert to previous version on failure
- **Prerequisites Validation**: Check dependencies before deployment
- **Configuration Validation**: Verify GCP project and service account access

### 📊 Better Monitoring
- **Colored Output**: Easy-to-read deployment logs
- **Progress Tracking**: Clear status updates throughout deployment
- **Comprehensive Error Messages**: Detailed failure information

## Quick Start

### Basic Deployment
```bash
# Deploy with default settings
./scripts/enhanced_deploy_nj_voter_chat.sh
```

### Test Before Deploying
```bash
# Dry run to see what would be deployed
DRY_RUN=true ./scripts/enhanced_deploy_nj_voter_chat.sh
```

### Environment-Specific Deployment
```bash
# Deploy to staging with reduced resources
ENVIRONMENT=staging MIN_INSTANCES=1 MAX_INSTANCES=3 MEMORY=1Gi \
./scripts/enhanced_deploy_nj_voter_chat.sh
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_ID` | `proj-roth` | GCP Project ID |
| `REGION` | `us-central1` | GCP Region |
| `ENVIRONMENT` | `production` | Deployment environment |
| `SERVICE_NAME` | `nj-voter-chat` | Cloud Run service name |
| `MIN_INSTANCES` | `0` | Minimum number of instances |
| `MAX_INSTANCES` | `10` | Maximum number of instances |
| `MEMORY` | `2Gi` | Memory allocation per instance |
| `CPU` | `1` | CPU allocation per instance |
| `TIMEOUT` | `300` | Request timeout in seconds |

### Deployment Options

| Option | Default | Description |
|--------|---------|-------------|
| `DRY_RUN` | `false` | Show deployment plan without executing |
| `SKIP_BUILD` | `false` | Use existing image, skip building |
| `ENABLE_HEALTH_CHECK` | `true` | Perform post-deployment health check |
| `ROLLBACK_ON_FAILURE` | `true` | Auto-rollback on deployment failure |

## Usage Examples

### Production Deployment
```bash
# Full production deployment with health checks
ENVIRONMENT=production MIN_INSTANCES=2 MAX_INSTANCES=20 \
./scripts/enhanced_deploy_nj_voter_chat.sh
```

### Staging Deployment
```bash
# Staging deployment with minimal resources
ENVIRONMENT=staging MIN_INSTANCES=0 MAX_INSTANCES=3 MEMORY=1Gi CPU=0.5 \
./scripts/enhanced_deploy_nj_voter_chat.sh
```

### Quick Update (Skip Build)
```bash
# Deploy existing image with new configuration
SKIP_BUILD=true MIN_INSTANCES=3 \
./scripts/enhanced_deploy_nj_voter_chat.sh
```

### Development Testing
```bash
# Test deployment without making changes
DRY_RUN=true ENVIRONMENT=development \
./scripts/enhanced_deploy_nj_voter_chat.sh
```

## Safety Features

### Automatic Rollback
If a deployment fails health checks, the script can automatically rollback to the previous working revision:

```bash
# Deploy with rollback protection (default)
ROLLBACK_ON_FAILURE=true ./scripts/enhanced_deploy_nj_voter_chat.sh
```

### Health Checks
The script performs HTTP health checks on the deployed service:

```bash
# Deploy with health checks (default)
ENABLE_HEALTH_CHECK=true ./scripts/enhanced_deploy_nj_voter_chat.sh

# Skip health checks for faster deployment
ENABLE_HEALTH_CHECK=false ./scripts/enhanced_deploy_nj_voter_chat.sh
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Ensure you're logged in
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Project Access Issues**
   ```bash
   # Verify project access
   gcloud projects describe proj-roth
   ```

3. **Service Account Issues**
   ```bash
   # Check service account exists
   gcloud iam service-accounts describe agent-runner@proj-roth.iam.gserviceaccount.com
   ```

### Debug Mode
For detailed troubleshooting, run with verbose output:

```bash
# Enable debug output
set -x
./scripts/enhanced_deploy_nj_voter_chat.sh
```

## Migration from Original Script

The enhanced script is fully compatible with the original `deploy_nj_voter_chat.sh`. Key differences:

| Feature | Original | Enhanced |
|---------|----------|----------|
| Error Handling | Basic | Comprehensive |
| Health Checks | None | Built-in |
| Rollback | Manual | Automatic |
| Dry Run | No | Yes |
| Environment Support | Limited | Full |
| Resource Configuration | Fixed | Configurable |

## Best Practices

1. **Always test with dry run first**:
   ```bash
   DRY_RUN=true ./scripts/enhanced_deploy_nj_voter_chat.sh
   ```

2. **Use environment-specific configurations**:
   ```bash
   # Create environment-specific scripts
   cp scripts/enhanced_deploy_nj_voter_chat.sh scripts/deploy_staging.sh
   # Edit deploy_staging.sh with staging defaults
   ```

3. **Monitor deployments**:
   ```bash
   # Watch logs during deployment
   gcloud run services logs tail nj-voter-chat --region=us-central1
   ```

4. **Keep rollback capability**:
   ```bash
   # Always deploy with rollback enabled for production
   ROLLBACK_ON_FAILURE=true ENVIRONMENT=production ./scripts/enhanced_deploy_nj_voter_chat.sh
   ```

## Integration with CI/CD

The enhanced script is designed for CI/CD integration:

```yaml
# Example GitHub Actions step
- name: Deploy to Cloud Run
  env:
    ENVIRONMENT: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
    MIN_INSTANCES: ${{ github.ref == 'refs/heads/main' && '2' || '0' }}
  run: ./scripts/enhanced_deploy_nj_voter_chat.sh
```

## Support

For issues with the enhanced deployment script:

1. Check the troubleshooting section above
2. Run with `DRY_RUN=true` to validate configuration
3. Review the deployment logs for specific error messages
4. Ensure all prerequisites are met (gcloud auth, project access, etc.)
