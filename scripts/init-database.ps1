# Initialize FIDPS Database Schema
# This script runs the SQL initialization files on PostgreSQL

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   FIDPS Database Initialization Script" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Check if PostgreSQL container is running
$postgresRunning = docker ps --filter "name=fidps-postgres" --format "{{.Names}}"
if (-not $postgresRunning) {
    Write-Host "ERROR: PostgreSQL container (fidps-postgres) is not running." -ForegroundColor Red
    Write-Host "Please start it with: docker-compose up -d postgres" -ForegroundColor Yellow
    exit 1
}

Write-Host "PostgreSQL container is running. Proceeding with initialization..." -ForegroundColor Green
Write-Host ""

# Wait for PostgreSQL to be ready
Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Run the initialization scripts
Write-Host "Running schema initialization scripts..." -ForegroundColor Cyan

# Script 1: Main tables
Write-Host "  [1/2] Creating main tables..." -ForegroundColor White
docker exec fidps-postgres psql -U fidps_user -d fidps_operational -f /docker-entrypoint-initdb.d/01_init_tables.sql

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Main tables created successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Error creating main tables" -ForegroundColor Red
}

# Script 2: API tables
Write-Host "  [2/2] Creating API tables..." -ForegroundColor White
docker exec fidps-postgres psql -U fidps_user -d fidps_operational -f /docker-entrypoint-initdb.d/02_api_tables.sql

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ API tables created successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Error creating API tables" -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Database Initialization Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Verify tables were created
Write-Host "Verifying database tables..." -ForegroundColor Cyan
$tableCheck = docker exec fidps-postgres psql -U fidps_user -d fidps_operational -c "\dt"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Database tables:" -ForegroundColor White
    Write-Host $tableCheck
    Write-Host ""
    Write-Host "✓ Database is ready for use!" -ForegroundColor Green
} else {
    Write-Host "⚠ Could not verify tables" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start all services: docker-compose up -d" -ForegroundColor White
Write-Host "  2. Check logs: docker-compose logs -f" -ForegroundColor White
Write-Host "  3. Access dashboard: http://localhost" -ForegroundColor White
Write-Host ""

