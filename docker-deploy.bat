@echo off
REM Simple Docker Deployment Script for Windows

setlocal enabledelayedexpansion

REM Usage: docker-deploy.bat [build|start|stop|logs|shell|setup]

if "%1"=="build" (
    echo [INFO] Building Docker image...
    docker-compose build
    exit /b
)

if "%1"=="start" (
    echo [INFO] Starting application...
    docker-compose up -d
    echo [INFO] Application started at http://localhost:5000
    exit /b
)

if "%1"=="stop" (
    echo [INFO] Stopping application and removing volumes...
    docker-compose down -v
    exit /b
)

if "%1"=="logs" (
    docker-compose logs -f
    exit /b
)

if "%1"=="shell" (
    echo [INFO] Accessing application shell...
    docker-compose exec app cmd
    exit /b
)

if "%1"=="setup" (
    echo [INFO] Setting up database...
    docker-compose exec app python scripts/setup_database.py
    exit /b
)

REM Help message
if "%1"=="" (
    echo Usage: docker-deploy.bat [build^|start^|stop^|logs^|shell^|setup]
    echo   build - Build the Docker image
    echo   start - Start the application
    echo   stop  - Stop the application and remove volumes
    echo   logs  - View application logs
    echo   shell - Access application shell
    echo   setup - Run database setup script
    exit /b
)

echo [ERROR] Unknown command: %1
exit /b 1
