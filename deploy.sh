#!/bin/bash

# DevSecrin Deployment Script
# This script helps deploy DevSecrin to a production environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="devsecrin"
DOCKER_IMAGE="devsecrin:latest"
BACKUP_DIR="/opt/devsecrin/backups"
DEPLOY_DIR="/opt/devsecrin"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Create backup
create_backup() {
    log_info "Creating backup..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    BACKUP_FILE="$BACKUP_DIR/devsecrin_$(date +%Y%m%d_%H%M%S).sql"
    
    if docker-compose exec -T postgres pg_dump -U devsecrin devsecrin > "$BACKUP_FILE"; then
        log_info "Database backup created: $BACKUP_FILE"
    else
        log_warn "Database backup failed"
    fi
    
    # Backup configuration
    if [ -f "$DEPLOY_DIR/.env" ]; then
        cp "$DEPLOY_DIR/.env" "$BACKUP_DIR/.env.$(date +%Y%m%d_%H%M%S)"
        log_info "Configuration backup created"
    fi
    
    # Backup vector database
    if [ -d "$DEPLOY_DIR/chroma_store" ]; then
        tar -czf "$BACKUP_DIR/chroma_store_$(date +%Y%m%d_%H%M%S).tar.gz" -C "$DEPLOY_DIR" chroma_store
        log_info "Vector database backup created"
    fi
}

# Deploy application
deploy() {
    log_info "Starting deployment..."
    
    # Navigate to deploy directory
    cd "$DEPLOY_DIR"
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose pull
    
    # Stop services
    log_info "Stopping services..."
    docker-compose down
    
    # Start services
    log_info "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check health
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_info "Deployment successful - API is healthy"
    else
        log_error "Deployment failed - API health check failed"
        exit 1
    fi
    
    if curl -f http://localhost:3000 &> /dev/null; then
        log_info "Frontend is accessible"
    else
        log_warn "Frontend health check failed"
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    if docker-compose exec -T devsecrin python packages/dbup/runner.py; then
        log_info "Database migrations completed"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

# Update AI models
update_models() {
    log_info "Updating AI models..."
    
    # Pull latest model
    if docker-compose exec -T ollama ollama pull deepseek-r1:1.5b; then
        log_info "AI model updated"
    else
        log_warn "AI model update failed"
    fi
}

# Clean up old backups (keep last 7 days)
cleanup_backups() {
    log_info "Cleaning up old backups..."
    
    find "$BACKUP_DIR" -name "*.sql" -type f -mtime +7 -delete
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +7 -delete
    find "$BACKUP_DIR" -name ".env.*" -type f -mtime +7 -delete
    
    log_info "Backup cleanup completed"
}

# Show system status
show_status() {
    log_info "System Status:"
    echo "======================================"
    docker-compose ps
    echo "======================================"
    
    log_info "Service URLs:"
    echo "- Frontend: http://localhost:3000"
    echo "- API: http://localhost:8000"
    echo "- API Docs: http://localhost:8000/docs"
    echo "- Health Check: http://localhost:8000/health"
    
    log_info "System Resources:"
    docker stats --no-stream
}

# Main deployment function
main() {
    log_info "Starting DevSecrin deployment..."
    
    check_root
    check_prerequisites
    create_backup
    deploy
    run_migrations
    update_models
    cleanup_backups
    show_status
    
    log_info "Deployment completed successfully!"
    log_info "Access your application at http://localhost:3000"
}

# Script usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --backup-only     Only create backup"
    echo "  --no-backup       Skip backup creation"
    echo "  --status          Show current system status"
    echo "  --help            Show this help message"
}

# Parse command line arguments
case "$1" in
    --backup-only)
        check_prerequisites
        create_backup
        ;;
    --no-backup)
        check_root
        check_prerequisites
        deploy
        run_migrations
        update_models
        show_status
        ;;
    --status)
        show_status
        ;;
    --help)
        usage
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        usage
        exit 1
        ;;
esac
