#!/usr/bin/env bash
set -euo pipefail


RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

PROJECT_ID="${PROJECT_ID:-proj-roth}"
REGION="${REGION:-us-central1}"
REPO_NAME="${REPO_NAME:-nj-voter-chat}"
IMAGE_NAME="${IMAGE_NAME:-nj-voter-chat}"
SERVICE_NAME="${SERVICE_NAME:-nj-voter-chat}"
SA_EMAIL="${SA_EMAIL:-agent-runner@${PROJECT_ID}.iam.gserviceaccount.com}"
ENVIRONMENT="${ENVIRONMENT:-production}"
MIN_INSTANCES="${MIN_INSTANCES:-0}"
MAX_INSTANCES="${MAX_INSTANCES:-10}"
MEMORY="${MEMORY:-2Gi}"
CPU="${CPU:-1}"
TIMEOUT="${TIMEOUT:-300}"

DRY_RUN="${DRY_RUN:-false}"
SKIP_BUILD="${SKIP_BUILD:-false}"
ENABLE_HEALTH_CHECK="${ENABLE_HEALTH_CHECK:-true}"
ROLLBACK_ON_FAILURE="${ROLLBACK_ON_FAILURE:-true}"

show_help() {
    cat << EOF
Enhanced Cloud Run Deployment Script for NJ Voter Chat

Usage: $0 [OPTIONS]

Environment Variables:
  PROJECT_ID              GCP Project ID (default: proj-roth)
  REGION                  GCP Region (default: us-central1)
  REPO_NAME              Artifact Registry repo name (default: nj-voter-chat)
  IMAGE_NAME             Docker image name (default: nj-voter-chat)
  SERVICE_NAME           Cloud Run service name (default: nj-voter-chat)
  SA_EMAIL               Service account email (default: agent-runner@PROJECT_ID.iam.gserviceaccount.com)
  ENVIRONMENT            Deployment environment (default: production)
  MIN_INSTANCES          Minimum instances (default: 0)
  MAX_INSTANCES          Maximum instances (default: 10)
  MEMORY                 Memory allocation (default: 2Gi)
  CPU                    CPU allocation (default: 1)
  TIMEOUT                Request timeout in seconds (default: 300)

Options:
  DRY_RUN=true           Show what would be deployed without executing
  SKIP_BUILD=true        Skip building new image, use existing latest
  ENABLE_HEALTH_CHECK=false  Disable post-deployment health check
  ROLLBACK_ON_FAILURE=false Disable automatic rollback on deployment failure

Examples:
  ./enhanced_deploy_nj_voter_chat.sh

  DRY_RUN=true ./enhanced_deploy_nj_voter_chat.sh

  ENVIRONMENT=staging MIN_INSTANCES=1 MAX_INSTANCES=3 ./enhanced_deploy_nj_voter_chat.sh

  SKIP_BUILD=true ./enhanced_deploy_nj_voter_chat.sh

  -h, --help             Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

validate_prerequisites() {
    log_info "Validating prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "No active gcloud authentication found. Please run 'gcloud auth login'"
        exit 1
    fi
    
    if [[ ! -f "agents/nj_voter_chat_adk/Dockerfile" ]]; then
        log_error "Dockerfile not found at agents/nj_voter_chat_adk/Dockerfile"
        exit 1
    fi
    
    if [[ ! -f "agents/nj_voter_chat_adk/requirements.txt" ]]; then
        log_error "requirements.txt not found at agents/nj_voter_chat_adk/requirements.txt"
        exit 1
    fi
    
    log_success "Prerequisites validated"
}

validate_configuration() {
    log_info "Validating configuration..."
    
    if ! gcloud projects describe "${PROJECT_ID}" &> /dev/null; then
        log_error "Project ${PROJECT_ID} not found or not accessible"
        exit 1
    fi
    
    if ! gcloud compute regions describe "${REGION}" &> /dev/null; then
        log_error "Region ${REGION} is not valid"
        exit 1
    fi
    
    if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &> /dev/null; then
        log_warning "Service account ${SA_EMAIL} not found. Deployment may fail if it doesn't exist."
    fi
    
    log_success "Configuration validated"
}

show_configuration() {
    log_info "Deployment Configuration:"
    echo "  Project ID:      ${PROJECT_ID}"
    echo "  Region:          ${REGION}"
    echo "  Environment:     ${ENVIRONMENT}"
    echo "  Service Name:    ${SERVICE_NAME}"
    echo "  Image Name:      ${IMAGE_NAME}"
    echo "  Repository:      ${REPO_NAME}"
    echo "  Service Account: ${SA_EMAIL}"
    echo "  Min Instances:   ${MIN_INSTANCES}"
    echo "  Max Instances:   ${MAX_INSTANCES}"
    echo "  Memory:          ${MEMORY}"
    echo "  CPU:             ${CPU}"
    echo "  Timeout:         ${TIMEOUT}s"
    echo "  Dry Run:         ${DRY_RUN}"
    echo "  Skip Build:      ${SKIP_BUILD}"
    echo ""
}

setup_gcp() {
    log_info "Setting up GCP configuration..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would set project to ${PROJECT_ID} and region to ${REGION}"
        return
    fi
    
    gcloud config set project "${PROJECT_ID}"
    gcloud config set run/region "${REGION}"
    
    log_success "GCP configuration set"
}

enable_services() {
    log_info "Enabling required GCP services..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would enable: run.googleapis.com, cloudbuild.googleapis.com, artifactregistry.googleapis.com"
        return
    fi
    
    gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
    
    log_success "Required services enabled"
}

setup_artifact_registry() {
    log_info "Setting up Artifact Registry..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would create repository ${REPO_NAME} in ${REGION} if it doesn't exist"
        return
    fi
    
    if gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" >/dev/null 2>&1; then
        log_info "Artifact Registry repository already exists"
    else
        log_info "Creating Artifact Registry repository..."
        if gcloud artifacts repositories create "${REPO_NAME}" \
            --repository-format=docker \
            --location="${REGION}" \
            --description="NJ Voter Chat images for ${ENVIRONMENT}" >/dev/null 2>&1; then
            log_success "Artifact Registry repository created"
        else
            if gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" >/dev/null 2>&1; then
                log_warning "Repository creation failed but repository exists (likely created by another process) - continuing"
            else
                log_error "Failed to create Artifact Registry repository and it doesn't exist"
                exit 1
            fi
        fi
    fi
    
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" -q
    
    log_success "Artifact Registry configured"
}

build_and_push_image() {
    local image_uri="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
    local tagged_image_uri="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"
    
    if [[ "${SKIP_BUILD}" == "true" ]]; then
        log_info "Skipping image build (SKIP_BUILD=true)"
        echo "${image_uri}"
        return
    fi
    
    log_info "Building and pushing Docker image..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would build image with tag: ${image_uri}"
        log_info "[DRY RUN] Would also tag as: ${tagged_image_uri}"
        echo "${image_uri}"
        return
    fi
    
    gcloud builds submit \
        --tag "${image_uri}" \
        --tag "${tagged_image_uri}" \
        --file agents/nj_voter_chat_adk/Dockerfile .
    
    log_success "Image built and pushed: ${image_uri}"
    log_info "Also tagged as: ${tagged_image_uri}"
    
    echo "${image_uri}"
}

get_current_revision() {
    if [[ "${DRY_RUN}" == "true" ]]; then
        echo "current-revision-placeholder"
        return
    fi
    
    gcloud run services describe "${SERVICE_NAME}" \
        --region "${REGION}" \
        --format='value(status.latestReadyRevisionName)' 2>/dev/null || echo ""
}

deploy_service() {
    local image_uri="$1"
    local current_revision="$2"
    
    log_info "Deploying to Cloud Run..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would deploy service ${SERVICE_NAME} with:"
        log_info "  Image: ${image_uri}"
        log_info "  Min instances: ${MIN_INSTANCES}"
        log_info "  Max instances: ${MAX_INSTANCES}"
        log_info "  Memory: ${MEMORY}"
        log_info "  CPU: ${CPU}"
        log_info "  Timeout: ${TIMEOUT}s"
        return
    fi
    
    gcloud run deploy "${SERVICE_NAME}" \
        --image "${image_uri}" \
        --allow-unauthenticated \
        --service-account "${SA_EMAIL}" \
        --region "${REGION}" \
        --min-instances "${MIN_INSTANCES}" \
        --max-instances "${MAX_INSTANCES}" \
        --memory "${MEMORY}" \
        --cpu "${CPU}" \
        --timeout "${TIMEOUT}" \
        --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION},ENVIRONMENT=${ENVIRONMENT}" \
        --labels "environment=${ENVIRONMENT},managed-by=enhanced-deploy-script" \
        --revision-suffix "${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"
    
    log_success "Service deployed successfully"
}

perform_health_check() {
    if [[ "${ENABLE_HEALTH_CHECK}" != "true" ]] || [[ "${DRY_RUN}" == "true" ]]; then
        if [[ "${DRY_RUN}" == "true" ]]; then
            log_info "[DRY RUN] Would perform health check on deployed service"
        else
            log_info "Health check disabled"
        fi
        return 0
    fi
    
    log_info "Performing health check..."
    
    local service_url
    service_url=$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)')
    
    if [[ -z "${service_url}" ]]; then
        log_error "Could not retrieve service URL"
        return 1
    fi
    
    log_info "Service URL: ${service_url}"
    
    sleep 10
    
    local max_retries=5
    local retry_count=0
    
    while [[ ${retry_count} -lt ${max_retries} ]]; do
        if curl -f -s "${service_url}" > /dev/null; then
            log_success "Health check passed"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        log_warning "Health check attempt ${retry_count}/${max_retries} failed, retrying in 10 seconds..."
        sleep 10
    done
    
    log_error "Health check failed after ${max_retries} attempts"
    return 1
}

rollback_deployment() {
    local previous_revision="$1"
    
    if [[ -z "${previous_revision}" ]] || [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "Cannot rollback: no previous revision available or in dry run mode"
        return
    fi
    
    log_warning "Rolling back to previous revision: ${previous_revision}"
    
    gcloud run services update-traffic "${SERVICE_NAME}" \
        --to-revisions "${previous_revision}=100" \
        --region "${REGION}"
    
    log_success "Rollback completed"
}

main() {
    log_info "Starting enhanced Cloud Run deployment for NJ Voter Chat"
    echo ""
    
    show_configuration
    
    validate_prerequisites
    validate_configuration
    
    local current_revision
    current_revision=$(get_current_revision)
    if [[ -n "${current_revision}" ]]; then
        log_info "Current revision: ${current_revision}"
    else
        log_info "No existing deployment found"
    fi
    
    setup_gcp
    enable_services
    setup_artifact_registry
    
    local image_uri
    image_uri=$(build_and_push_image)
    
    if deploy_service "${image_uri}" "${current_revision}"; then
        log_success "Deployment completed successfully"
        
        if ! perform_health_check; then
            if [[ "${ROLLBACK_ON_FAILURE}" == "true" ]] && [[ -n "${current_revision}" ]]; then
                log_warning "Health check failed, initiating rollback..."
                rollback_deployment "${current_revision}"
                exit 1
            else
                log_error "Health check failed, but rollback is disabled"
                exit 1
            fi
        fi
        
        if [[ "${DRY_RUN}" != "true" ]]; then
            echo ""
            log_success "Deployment completed successfully!"
            echo "Service URL:"
            gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)'
        else
            log_info "[DRY RUN] Deployment simulation completed"
        fi
    else
        log_error "Deployment failed"
        if [[ "${ROLLBACK_ON_FAILURE}" == "true" ]] && [[ -n "${current_revision}" ]]; then
            rollback_deployment "${current_revision}"
        fi
        exit 1
    fi
}

main "$@"
