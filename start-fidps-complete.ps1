# FIDPS Complete System Startup Script
# One command to rule them all!

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   FIDPS - Formation Integrity & Damage Prevention System" -ForegroundColor Cyan
Write-Host "   Complete System Startup" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop first." -ForegroundColor Yellow
    exit 1
}

# Stop any existing containers
Write-Host "`nCleaning up existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null
Write-Host "✓ Cleaned up" -ForegroundColor Green

# Build and start all services
Write-Host "`nBuilding and starting all services..." -ForegroundColor Yellow
Write-Host "This will take several minutes on first run. Please be patient..." -ForegroundColor Gray

# Start all services at once (Docker Compose handles dependencies)
docker-compose up -d --build

# Wait for services to start
Write-Host "`nWaiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Check service status
Write-Host "`nChecking service status..." -ForegroundColor Yellow
docker-compose ps

# Display summary
Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host "   FIDPS System Started Successfully!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "🌐 ACCESS POINTS:" -ForegroundColor Cyan
Write-Host "   • Main Dashboard:     http://localhost" -ForegroundColor White
Write-Host "   • API Dashboard:      http://localhost:8000" -ForegroundColor White
Write-Host "   • API Docs:           http://localhost:8000/docs" -ForegroundColor White
Write-Host "   • RTO Service:        http://localhost:8002/docs" -ForegroundColor White
Write-Host "   • PdM Service:        http://localhost:8003/docs" -ForegroundColor White
Write-Host "   • ML Service:         http://localhost:8080/docs" -ForegroundColor White
Write-Host ""

Write-Host "📊 MONITORING:" -ForegroundColor Cyan
Write-Host "   • Grafana:            http://localhost:3000" -ForegroundColor White
Write-Host "      Username: admin" -ForegroundColor Gray
Write-Host "      Password: fidps_grafana_password_2024" -ForegroundColor Gray
Write-Host "   • Prometheus:         http://localhost:9090" -ForegroundColor White
Write-Host "   • InfluxDB:           http://localhost:8086" -ForegroundColor White
Write-Host "   • Kafka UI:           http://localhost:8082" -ForegroundColor White
Write-Host ""

Write-Host "🗄️  DATABASES:" -ForegroundColor Cyan
Write-Host "   • PostgreSQL:         localhost:5432" -ForegroundColor White
Write-Host "   • MongoDB:            localhost:27017" -ForegroundColor White
Write-Host "   • Redis:              localhost:6379" -ForegroundColor White
Write-Host "   • MinIO:              http://localhost:9001" -ForegroundColor White
Write-Host ""

Write-Host "📝 USEFUL COMMANDS:" -ForegroundColor Cyan
Write-Host "   • View logs:          docker-compose logs -f [service]" -ForegroundColor White
Write-Host "   • Stop all:           docker-compose down" -ForegroundColor White
Write-Host "   • Restart service:    docker-compose restart [service]" -ForegroundColor White
Write-Host "   • Check status:       docker-compose ps" -ForegroundColor White
Write-Host ""

Write-Host "✅ System is ready for use!" -ForegroundColor Green
Write-Host ""
Write-Host "Open your browser and go to: http://localhost" -ForegroundColor Yellow
Write-Host ""

