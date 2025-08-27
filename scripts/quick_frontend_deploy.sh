#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}⚡ Quick Frontend Deploy${NC}"
echo "========================"
echo "This rebuilds just the frontend and redeploys with minimal Docker rebuild"
echo ""

# Configuration
PROJECT_ID=${PROJECT_ID:-proj-roth}
REGION=${REGION:-us-central1}
SERVICE_NAME="nj-voter-chat-app"
FRONTEND_DIR="frontend"

# Function to update frontend version
update_frontend_version() {
    echo -e "\n${YELLOW}📦 Updating frontend version...${NC}"
    
    cd $FRONTEND_DIR
    
    # Get current version from package.json
    CURRENT_VERSION=$(grep '"version"' package.json | sed -E 's/.*"version": "([^"]+)".*/\1/')
    echo "Current version: $CURRENT_VERSION"
    
    # Parse version components
    IFS='.' read -r major minor patch <<< "$CURRENT_VERSION"
    
    # Increment patch version
    new_patch=$((patch + 1))
    NEW_VERSION="$major.$minor.$new_patch"
    
    echo "New version: $NEW_VERSION"
    
    # Update package.json
    sed -i '' "s/\"version\": \"$CURRENT_VERSION\"/\"version\": \"$NEW_VERSION\"/" package.json
    
    cd ..
    
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
    echo "Running npm build..."
    npm run build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend build successful${NC}"
        
        # Show build info
        echo -e "\nBuild artifacts:"
        ls -lh build/static/js/*.js 2>/dev/null | head -3
        
        # Show total build size
        BUILD_SIZE=$(du -sh build | cut -f1)
        echo -e "Total build size: ${BUILD_SIZE}"
    else
        echo -e "${RED}✗ Frontend build failed${NC}"
        exit 1
    fi
    
    cd ..
}

# Function for minimal Docker rebuild
quick_docker_build() {
    echo -e "\n${YELLOW}🐳 Quick Docker rebuild (frontend only)...${NC}"
    
    # Create a timestamp tag
    TIMESTAMP=$(date +%s)
    GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "no-git")
    IMAGE_TAG="fe-${GIT_HASH}-${TIMESTAMP}"
    IMAGE_URL="us-central1-docker.pkg.dev/${PROJECT_ID}/nj-voter-chat-app/nj-voter-chat-app"
    
    echo "Building image: ${IMAGE_URL}:${IMAGE_TAG}"
    echo "Note: This uses Docker layer caching for faster builds"
    
    # Submit build to Cloud Build
    # Note: Removed --cache-from as it's not supported by gcloud builds submit
    gcloud builds submit \
        --tag "${IMAGE_URL}:${IMAGE_TAG}" \
        --project ${PROJECT_ID} \
        --timeout=10m \
        .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Docker image built successfully${NC}"
        
        # Tag as latest
        gcloud container images add-tag \
            "${IMAGE_URL}:${IMAGE_TAG}" \
            "${IMAGE_URL}:latest" \
            --quiet
            
        echo "Tagged as: ${IMAGE_URL}:latest"
    else
        echo -e "${RED}✗ Docker build failed${NC}"
        exit 1
    fi
    
    echo "IMAGE_TAG=${IMAGE_TAG}" > .last_frontend_build
    echo "IMAGE_URL=${IMAGE_URL}" >> .last_frontend_build
}

# Function to deploy
deploy_frontend() {
    echo -e "\n${YELLOW}☁️  Deploying to Cloud Run...${NC}"
    
    if [ -f .last_frontend_build ]; then
        source .last_frontend_build
    else
        echo -e "${RED}✗ No build information found${NC}"
        exit 1
    fi
    
    echo "Deploying ${IMAGE_URL}:latest..."
    
    # Deploy with minimal configuration (faster)
    gcloud run deploy ${SERVICE_NAME} \
        --image "${IMAGE_URL}:latest" \
        --platform managed \
        --region ${REGION} \
        --project ${PROJECT_ID} \
        --no-traffic
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Deployment successful${NC}"
        
        # Now route traffic to the new revision
        echo "Routing traffic to new revision..."
        gcloud run services update-traffic ${SERVICE_NAME} \
            --to-latest \
            --platform managed \
            --region ${REGION} \
            --project ${PROJECT_ID}
    else
        echo -e "${RED}✗ Deployment failed${NC}"
        exit 1
    fi
}

# Function to show deployment info
show_info() {
    echo -e "\n${GREEN}================================================${NC}"
    echo -e "${GREEN}✅ Frontend Deploy Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
        --platform managed \
        --region ${REGION} \
        --project ${PROJECT_ID} \
        --format 'value(status.url)' 2>/dev/null)
    
    if [ ! -z "$SERVICE_URL" ]; then
        echo -e "\n🌐 Service URL: ${SERVICE_URL}"
    fi
    
    # Show latest revision
    LATEST_REVISION=$(gcloud run services describe ${SERVICE_NAME} \
        --platform managed \
        --region ${REGION} \
        --project ${PROJECT_ID} \
        --format 'value(status.latestReadyRevisionName)' 2>/dev/null)
    
    if [ ! -z "$LATEST_REVISION" ]; then
        echo -e "📌 Latest revision: ${LATEST_REVISION}"
    fi
    
    echo -e "\n💡 Tip: Changes should be live within 30-60 seconds"
}

# Main execution
main() {
    # Check prerequisites
    command -v gcloud >/dev/null 2>&1 || { echo -e "${RED}gcloud CLI is required but not installed.${NC}" >&2; exit 1; }
    command -v npm >/dev/null 2>&1 || { echo -e "${RED}npm is required but not installed.${NC}" >&2; exit 1; }
    
    # Parse arguments
    SKIP_VERSION=false
    BUILD_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-version)
                SKIP_VERSION=true
                shift
                ;;
            --build-only)
                BUILD_ONLY=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --skip-version   Skip version bump"
                echo "  --build-only     Only build frontend, don't deploy"
                echo "  --help          Show this help"
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                exit 1
                ;;
        esac
    done
    
    # Run steps
    if [ "$SKIP_VERSION" = false ]; then
        update_frontend_version
    fi
    
    build_frontend
    
    if [ "$BUILD_ONLY" = false ]; then
        quick_docker_build
        deploy_frontend
        show_info
    else
        echo -e "\n${YELLOW}Build only mode - skipping deployment${NC}"
        echo "Frontend build artifacts are in: frontend/build/"
    fi
}

# Run main
main "$@"