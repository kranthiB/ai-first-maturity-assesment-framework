#!/bin/bash

# Simple Docker Deployment Script for AFS Assessment Framework

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

case "$1" in
    build)
        log_info "Building Docker image..."
        docker-compose build
        ;;
    up|start)
        log_info "Starting application..."
        docker-compose up -d
        log_info "Application started at http://localhost:5001"
        ;;
    down|stop)
        log_info "Stopping application and removing volumes..."
        docker-compose down -v
        ;;
    logs)
        docker-compose logs -f
        ;;
    shell)
        log_info "Accessing application shell..."
        docker-compose exec app bash
        ;;
    setup)
        log_info "Setting up database..."
        docker-compose exec app python scripts/setup_database.py
        ;;
    *)
        echo "Usage: $0 {build|start|stop|logs|shell|setup}"
        echo "  build - Build the Docker image"
        echo "  start - Start the application"
        echo "  stop  - Stop the application"
        echo "  logs  - View application logs"
        echo "  shell - Access application shell"
        echo "  setup - Run database setup script"
        exit 1
        ;;
esac
