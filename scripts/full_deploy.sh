#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Full Build and Deploy Process${NC}"
echo "================================================"

# Configuration
PROJECT_ID=${PROJECT_ID:-proj-roth}
REGION=${REGION:-us-central1}
SERVICE_NAME="nj-voter-chat-app"
FRONTEND_DIR="frontend"
BACKEND_DIR="backend"

# Function to update frontend version
update_frontend_version() {
    echo -e "\n${YELLOW}📦 Updating frontend version...${NC}"
    
    # Get current version from package.json
    CURRENT_VERSION=$(grep '"version"' $FRONTEND_DIR/package.json | sed -E 's/.*"version": "([^"]+)".*/\1/')
    echo "Current version: $CURRENT_VERSION"
    
    # Parse version components
    IFS='.' read -r major minor patch <<< "$CURRENT_VERSION"
    
    # Increment patch version
    new_patch=$((patch + 1))
    NEW_VERSION="$major.$minor.$new_patch"
    
    echo "New version: $NEW_VERSION"
    
    # Update package.json
    sed -i '' "s/\"version\": \"$CURRENT_VERSION\"/\"version\": \"$NEW_VERSION\"/" $FRONTEND_DIR/package.json
    
    # Commit version update
    git add $FRONTEND_DIR/package.json
    git commit -m "Bump frontend version to $NEW_VERSION" || echo "No version changes to commit"
    
    echo -e "${GREEN}✓ Frontend version updated to $NEW_VERSION${NC}"
}

# Function to build frontend
build_frontend() {
    echo -e "\n${YELLOW}🔨 Building frontend...${NC}"
    
    cd $FRONTEND_DIR
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ] || [ package.json -nt node_modules ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi
    
    # Build frontend
    npm run build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend build successful${NC}"
        
        # Show build info
        echo "Build output:"
        ls -lh build/static/js/*.js 2>/dev/null | head -3
    else
        echo -e "${RED}✗ Frontend build failed${NC}"
        exit 1
    fi
    
    cd ..
}

# Function to verify backend
verify_backend() {
    echo -e "\n${YELLOW}🐍 Verifying backend...${NC}"
    
    # Check if main.py exists
    if [ ! -f "$BACKEND_DIR/main.py" ]; then
        echo -e "${RED}✗ Backend main.py not found${NC}"
        exit 1
    fi
    
    # Verify Python syntax
    python -m py_compile $BACKEND_DIR/main.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backend Python syntax valid${NC}"
    else
        echo -e "${RED}✗ Backend Python syntax errors${NC}"
        exit 1
    fi
}

# Function to build Docker image
build_docker_image() {
    echo -e "\n${YELLOW}🐳 Building Docker image...${NC}"
    
    # Create a timestamp tag
    TIMESTAMP=$(date +%s)
    GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "no-git")
    IMAGE_TAG="${GIT_HASH}-${TIMESTAMP}"
    IMAGE_URL="us-central1-docker.pkg.dev/${PROJECT_ID}/nj-voter-chat-app/nj-voter-chat-app"
    
    echo "Building image: ${IMAGE_URL}:${IMAGE_TAG}"
    
    # Submit build to Cloud Build
    gcloud builds submit \
        --tag "${IMAGE_URL}:${IMAGE_TAG}" \
        --project ${PROJECT_ID} \
        --timeout=20m \
        .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Docker image built successfully${NC}"
        
        # Also tag as latest
        gcloud container images add-tag \
            "${IMAGE_URL}:${IMAGE_TAG}" \
            "${IMAGE_URL}:latest" \
            --quiet
            
        echo "Tagged as: ${IMAGE_URL}:latest"
    else
        echo -e "${RED}✗ Docker build failed${NC}"
        exit 1
    fi
    
    echo "IMAGE_TAG=${IMAGE_TAG}" > .last_build
    echo "IMAGE_URL=${IMAGE_URL}" >> .last_build
}

# Function to deploy to Cloud Run
deploy_to_cloud_run() {
    echo -e "\n${YELLOW}☁️  Deploying to Cloud Run...${NC}"
    
    # Read the last build info
    if [ -f .last_build ]; then
        source .last_build
    else
        echo -e "${RED}✗ No build information found${NC}"
        exit 1
    fi
    
    echo "Deploying ${IMAGE_URL}:latest to Cloud Run..."
    
    gcloud run deploy ${SERVICE_NAME} \
        --image "${IMAGE_URL}:latest" \
        --platform managed \
        --region ${REGION} \
        --project ${PROJECT_ID} \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --timeout 60 \
        --max-instances 10 \
        --min-instances 0
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Deployment successful${NC}"
    else
        echo -e "${RED}✗ Deployment failed${NC}"
        exit 1
    fi
}

# Function to verify deployment
verify_deployment() {
    echo -e "\n${YELLOW}🔍 Verifying deployment...${NC}"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
        --platform managed \
        --region ${REGION} \
        --project ${PROJECT_ID} \
        --format 'value(status.url)')
    
    echo "Service URL: ${SERVICE_URL}"
    
    # Get latest revision
    LATEST_REVISION=$(gcloud run services describe ${SERVICE_NAME} \
        --platform managed \
        --region ${REGION} \
        --project ${PROJECT_ID} \
        --format 'value(status.latestReadyRevisionName)')
    
    echo "Latest revision: ${LATEST_REVISION}"
    
    # Check if service is responding
    echo -e "\nChecking service health..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/health" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Service is healthy (HTTP ${HTTP_CODE})${NC}"
    else
        echo -e "${YELLOW}⚠ Service returned HTTP ${HTTP_CODE}${NC}"
        echo "Note: It may take a minute for the service to become fully available"
    fi
    
    # Show recent logs
    echo -e "\nRecent deployment logs:"
    gcloud run services logs read ${SERVICE_NAME} \
        --region ${REGION} \
        --project ${PROJECT_ID} \
        --limit 5 \
        --format "table(timestamp, severity, textPayload)" 2>/dev/null || echo "Unable to fetch logs"
}

# Function to show summary
show_summary() {
    echo -e "\n${GREEN}================================================${NC}"
    echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}================================================${NC}"
    
    if [ -f .last_build ]; then
        source .last_build
        echo -e "\n📋 Deployment Summary:"
        echo -e "  Project: ${PROJECT_ID}"
        echo -e "  Region: ${REGION}"
        echo -e "  Service: ${SERVICE_NAME}"
        echo -e "  Image Tag: ${IMAGE_TAG}"
        
        SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
            --platform managed \
            --region ${REGION} \
            --project ${PROJECT_ID} \
            --format 'value(status.url)' 2>/dev/null)
        
        if [ ! -z "$SERVICE_URL" ]; then
            echo -e "  URL: ${SERVICE_URL}"
        fi
    fi
}

# Main execution
main() {
    # Check prerequisites
    command -v gcloud >/dev/null 2>&1 || { echo -e "${RED}gcloud CLI is required but not installed.${NC}" >&2; exit 1; }
    command -v npm >/dev/null 2>&1 || { echo -e "${RED}npm is required but not installed.${NC}" >&2; exit 1; }
    command -v python >/dev/null 2>&1 || { echo -e "${RED}Python is required but not installed.${NC}" >&2; exit 1; }
    
    # Parse arguments
    SKIP_VERSION_UPDATE=false
    SKIP_FRONTEND=false
    SKIP_BACKEND=false
    SKIP_DEPLOY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-version)
                SKIP_VERSION_UPDATE=true
                shift
                ;;
            --skip-frontend)
                SKIP_FRONTEND=true
                shift
                ;;
            --skip-backend)
                SKIP_BACKEND=true
                shift
                ;;
            --skip-deploy)
                SKIP_DEPLOY=true
                shift
                ;;
            --frontend-only)
                echo "For frontend-only updates, use: scripts/quick_frontend_deploy.sh"
                echo "It's optimized for faster frontend deployments with Docker layer caching"
                exit 0
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --skip-version   Skip frontend version update"
                echo "  --skip-frontend  Skip frontend build"
                echo "  --skip-backend   Skip backend verification"
                echo "  --skip-deploy    Skip Cloud Run deployment (only build)"
                echo "  --frontend-only  Show info about frontend-only deployments"
                echo "  --help          Show this help message"
                echo ""
                echo "For faster frontend-only updates, use: scripts/quick_frontend_deploy.sh"
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                exit 1
                ;;
        esac
    done
    
    # Run steps
    if [ "$SKIP_VERSION_UPDATE" = false ] && [ "$SKIP_FRONTEND" = false ]; then
        update_frontend_version
    fi
    
    if [ "$SKIP_FRONTEND" = false ]; then
        build_frontend
    fi
    
    if [ "$SKIP_BACKEND" = false ]; then
        verify_backend
    fi
    
    build_docker_image
    
    if [ "$SKIP_DEPLOY" = false ]; then
        deploy_to_cloud_run
        verify_deployment
    fi
    
    show_summary
}

# Run main function
main "$@"