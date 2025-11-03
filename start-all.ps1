# FIDPS Complete System Startup Script
# This script starts ALL FIDPS services including the newly added ones

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  FIDPS - Intelligent Formation Integrity & Damage Prevention" -ForegroundColor Cyan
Write-Host "  Starting Complete System..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Stop any running containers
Write-Host "`nStopping any existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null

# Build and start all services
Write-Host "`nBuilding and starting all FIDPS services..." -ForegroundColor Yellow
Write-Host "This may take several minutes on first run..." -ForegroundColor Gray
Write-Host ""

# Start in phases for proper dependencies
Write-Host "Phase 1: Starting infrastructure services..." -ForegroundColor Cyan
docker-compose up -d zookeeper postgres mongodb redis minio

Write-Host "Waiting 30 seconds for databases to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 30

Write-Host "`nPhase 2: Starting Kafka..." -ForegroundColor Cyan
docker-compose up -d kafka

Write-Host "Waiting 20 seconds for Kafka to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 20

Write-Host "`nPhase 3: Starting monitoring and InfluxDB..." -ForegroundColor Cyan
docker-compose up -d prometheus grafana influxdb

Write-Host "Waiting 10 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 10

Write-Host "`nPhase 4: Starting Kafka Connect and InfluxDB Connector..." -ForegroundColor Cyan
docker-compose up -d kafka-connect influxdb-connector

Write-Host "Waiting 10 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 10

Write-Host "`nPhase 5: Starting ML and analytics services..." -ForegroundColor Cyan
docker-compose up -d ml-anomaly-detection flink-validation

Write-Host "Waiting 15 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 15

Write-Host "`nPhase 6: Starting RTO and PdM services..." -ForegroundColor Cyan
docker-compose up -d rto-service pdm-service

Write-Host "Waiting 15 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 15

Write-Host "`nPhase 7: Starting API and UI services..." -ForegroundColor Cyan
docker-compose up -d api-dashboard frontend-react kafka-ui

Write-Host "Waiting 20 seconds for final services to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 20

# Check services status
Write-Host "`nChecking services status..." -ForegroundColor Yellow
docker-compose ps

# Display summary
Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host "  FIDPS System Started Successfully!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "🌐 MAIN DASHBOARD:" -ForegroundColor Cyan
Write-Host "   • React Dashboard: http://localhost" -ForegroundColor White
Write-Host "   • API Dashboard: http://localhost:8000" -ForegroundColor White
Write-Host "   • API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

Write-Host "🔧 SERVICES:" -ForegroundColor Cyan
Write-Host "   • RTO Service: http://localhost:8002" -ForegroundColor White
Write-Host "   • RTO Docs: http://localhost:8002/docs" -ForegroundColor White
Write-Host "   • PdM Service: http://localhost:8003" -ForegroundColor White
Write-Host "   • PdM Docs: http://localhost:8003/docs" -ForegroundColor White
Write-Host "   • ML Service: http://localhost:8080" -ForegroundColor White
Write-Host "   • ML Docs: http://localhost:8080/docs" -ForegroundColor White
Write-Host ""

Write-Host "📊 MONITORING:" -ForegroundColor Cyan
Write-Host "   • Grafana: http://localhost:3000" -ForegroundColor White
Write-Host "   •   Username: admin" -ForegroundColor Gray
Write-Host "   •   Password: fidps_grafana_password_2024" -ForegroundColor Gray
Write-Host "   • Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "   • InfluxDB: http://localhost:8086" -ForegroundColor White
Write-Host "   • Kafka UI: http://localhost:8082" -ForegroundColor White
Write-Host ""

Write-Host "🗄️ INFRASTRUCTURE:" -ForegroundColor Cyan
Write-Host "   • PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "   •   Username: fidps_user" -ForegroundColor Gray
Write-Host "   •   Password: fidps_password" -ForegroundColor Gray
Write-Host "   • MongoDB: localhost:27017" -ForegroundColor White
Write-Host "   •   Username: root" -ForegroundColor Gray
Write-Host "   •   Password: fidps_mongo_password_2024" -ForegroundColor Gray
Write-Host "   • MinIO: http://localhost:9001" -ForegroundColor White
Write-Host "   • Redis: localhost:6379" -ForegroundColor White
Write-Host ""

Write-Host "📝 USEFUL COMMANDS:" -ForegroundColor Cyan
Write-Host "   • View logs: docker-compose logs -f [service-name]" -ForegroundColor White
Write-Host "   • Stop all: docker-compose down" -ForegroundColor White
Write-Host "   • Restart service: docker-compose restart [service-name]" -ForegroundColor White
Write-Host "   • Check status: docker-compose ps" -ForegroundColor White
Write-Host ""

Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""

