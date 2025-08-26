# FIDPS System Startup Script
# This script starts all FIDPS services in the correct order

Write-Host "Starting FIDPS - Intelligent Formation Integrity & Damage Prevention System" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if docker-compose is available
Write-Host "Checking Docker Compose..." -ForegroundColor Yellow
try {
    docker-compose version | Out-Null
    Write-Host "✓ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose is not available. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "Creating data directories..." -ForegroundColor Yellow
$directories = @(
    "data/csv/input",
    "data/csv/processed",
    "data/csv/error",
    "data/postgres",
    "data/mongo",
    "data/minio",
    "data/redis",
    "data/kafka",
    "data/zookeeper",
    "data/prometheus",
    "data/grafana",
    "logs/kafka",
    "logs/connect",
    "logs/postgres",
    "logs/mongo",
    "logs/application"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ Created directory: $dir" -ForegroundColor Green
    }
}

# Copy sample CSV data if exists
if (Test-Path "real_time_data.csv") {
    Copy-Item "real_time_data.csv" "data/csv/input/" -Force
    Write-Host "✓ Copied sample real-time data to input directory" -ForegroundColor Green
}

if (Test-Path "historical_data.csv") {
    Copy-Item "historical_data.csv" "data/csv/input/" -Force
    Write-Host "✓ Copied sample historical data to input directory" -ForegroundColor Green
}

# Start infrastructure services first
Write-Host "Starting infrastructure services..." -ForegroundColor Yellow
docker-compose up -d zookeeper postgres mongo minio redis

# Wait for infrastructure to be ready
Write-Host "Waiting for infrastructure services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check PostgreSQL readiness
Write-Host "Checking PostgreSQL readiness..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
do {
    $attempt++
    try {
        docker exec fidps-postgres pg_isready -U fidps_user -d fidps_operational | Out-Null
        Write-Host "✓ PostgreSQL is ready" -ForegroundColor Green
        break
    } catch {
        if ($attempt -eq $maxAttempts) {
            Write-Host "✗ PostgreSQL failed to start after $maxAttempts attempts" -ForegroundColor Red
            exit 1
        }
        Write-Host "Waiting for PostgreSQL... (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
} while ($attempt -lt $maxAttempts)

# Check MongoDB readiness
Write-Host "Checking MongoDB readiness..." -ForegroundColor Yellow
$attempt = 0
do {
    $attempt++
    try {
        docker exec fidps-mongo mongosh --eval "db.adminCommand('ping')" | Out-Null
        Write-Host "✓ MongoDB is ready" -ForegroundColor Green
        break
    } catch {
        if ($attempt -eq $maxAttempts) {
            Write-Host "✗ MongoDB failed to start after $maxAttempts attempts" -ForegroundColor Red
            exit 1
        }
        Write-Host "Waiting for MongoDB... (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
} while ($attempt -lt $maxAttempts)

# Start Kafka services
Write-Host "Starting Kafka services..." -ForegroundColor Yellow
docker-compose up -d kafka
Start-Sleep -Seconds 20

# Check Kafka readiness
Write-Host "Checking Kafka readiness..." -ForegroundColor Yellow
$attempt = 0
do {
    $attempt++
    try {
        docker exec fidps-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 | Out-Null
        Write-Host "✓ Kafka is ready" -ForegroundColor Green
        break
    } catch {
        if ($attempt -eq $maxAttempts) {
            Write-Host "✗ Kafka failed to start after $maxAttempts attempts" -ForegroundColor Red
            exit 1
        }
        Write-Host "Waiting for Kafka... (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
} while ($attempt -lt $maxAttempts)

# Start Kafka Connect
Write-Host "Starting Kafka Connect..." -ForegroundColor Yellow
docker-compose up -d kafka-connect
Start-Sleep -Seconds 30

# Start monitoring services
Write-Host "Starting monitoring services..." -ForegroundColor Yellow
docker-compose up -d prometheus grafana

# Start UI services
Write-Host "Starting UI services..." -ForegroundColor Yellow
docker-compose up -d kafka-ui

# Wait for all services to be fully ready
Write-Host "Waiting for all services to be fully ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Create Kafka topics
Write-Host "Creating Kafka topics..." -ForegroundColor Yellow
$topics = @(
    "witsml-raw-data",
    "csv-mwd-lwd-data",
    "mwd-lwd-data",
    "anomaly-events",
    "ml-predictions",
    "simulation-results",
    "alerts",
    "witsml-dlq",
    "csv-dlq",
    "postgres-sink-dlq"
)

foreach ($topic in $topics) {
    try {
        docker exec fidps-kafka kafka-topics --create --topic $topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
        Write-Host "✓ Created topic: $topic" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Topic $topic might already exist or failed to create" -ForegroundColor Yellow
    }
}

# Deploy Kafka Connect connectors
Write-Host "Deploying Kafka Connect connectors..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if Kafka Connect is ready
$attempt = 0
do {
    $attempt++
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8083/connectors" -Method GET
        Write-Host "✓ Kafka Connect is ready" -ForegroundColor Green
        break
    } catch {
        if ($attempt -eq 20) {
            Write-Host "✗ Kafka Connect failed to start after 20 attempts" -ForegroundColor Red
            Write-Host "Continuing without connector deployment..." -ForegroundColor Yellow
            break
        }
        Write-Host "Waiting for Kafka Connect... (attempt $attempt/20)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
} while ($attempt -lt 20)

# Deploy connectors if Kafka Connect is ready
if ($attempt -lt 20) {
    $connectors = @(
        "connectors/csv-source-connector.json",
        "connectors/postgres-sink-connector.json"
    )
    
    foreach ($connector in $connectors) {
        if (Test-Path $connector) {
            try {
                $connectorConfig = Get-Content $connector | ConvertFrom-Json
                $response = Invoke-RestMethod -Uri "http://localhost:8083/connectors" -Method POST -Body ($connectorConfig | ConvertTo-Json -Depth 10) -ContentType "application/json"
                Write-Host "✓ Deployed connector: $($connectorConfig.name)" -ForegroundColor Green
            } catch {
                Write-Host "⚠ Failed to deploy connector from $connector" -ForegroundColor Yellow
                Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}

# Start ML Anomaly Detection Service
Write-Host "Starting ML Anomaly Detection service..." -ForegroundColor Yellow
docker-compose up -d ml-anomaly-detection

# Wait for ML service to be ready
Write-Host "Waiting for ML Anomaly Detection service..." -ForegroundColor Yellow
$mlReady = $false
$mlWaitTime = 0
while (-not $mlReady -and $mlWaitTime -lt 180) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $mlReady = $true
            Write-Host "✓ ML Anomaly Detection service is ready!" -ForegroundColor Green
        }
    } catch {
        Start-Sleep 5
        $mlWaitTime += 5
        Write-Host "." -NoNewline
    }
}

if (-not $mlReady) {
    Write-Host "`n⚠ ML Anomaly Detection service may not be fully ready" -ForegroundColor Yellow
}

# Start API Dashboard Service
Write-Host "Starting API Dashboard service..." -ForegroundColor Yellow
docker-compose up -d api-dashboard

# Wait for Dashboard service to be ready
Write-Host "Waiting for API Dashboard service..." -ForegroundColor Yellow
$dashboardReady = $false
$dashboardWaitTime = 0
while (-not $dashboardReady -and $dashboardWaitTime -lt 120) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $dashboardReady = $true
            Write-Host "✓ API Dashboard service is ready!" -ForegroundColor Green
        }
    } catch {
        Start-Sleep 5
        $dashboardWaitTime += 5
        Write-Host "." -NoNewline
    }
}

if (-not $dashboardReady) {
    Write-Host "`n⚠ API Dashboard service may not be fully ready" -ForegroundColor Yellow
}

Write-Host "\n=== FIDPS System Started Successfully! ===" -ForegroundColor Green
Write-Host "\nMain Access URLs:" -ForegroundColor Cyan
Write-Host "• FIDPS Dashboard: http://localhost:8000" -ForegroundColor White
Write-Host "• Dashboard API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "• Kafka UI: http://localhost:8080" -ForegroundColor White
Write-Host "• Grafana Dashboard: http://localhost:3000 (admin/fidps_grafana_password_2024)" -ForegroundColor White
Write-Host "• Prometheus: http://localhost:9090" -ForegroundColor White

Write-Host "\nML Anomaly Detection Service:" -ForegroundColor Cyan
Write-Host "• ML API: http://localhost:8080" -ForegroundColor White
Write-Host "• ML API Documentation: http://localhost:8080/docs" -ForegroundColor White
Write-Host "• ML Health Check: http://localhost:8080/health" -ForegroundColor White
Write-Host "• ML Metrics: http://localhost:9090/metrics" -ForegroundColor White

Write-Host "\nDashboard API Endpoints:" -ForegroundColor Cyan
Write-Host "• Dashboard Health: http://localhost:8000/health" -ForegroundColor White
Write-Host "• Dashboard Metrics: http://localhost:8000/metrics" -ForegroundColor White
Write-Host "• Wells API: http://localhost:8000/api/v1/wells" -ForegroundColor White
Write-Host "• Anomalies API: http://localhost:8000/api/v1/anomalies/active" -ForegroundColor White
Write-Host "• System Status: http://localhost:8000/api/v1/system/status" -ForegroundColor White

Write-Host "\nWebSocket Endpoints:" -ForegroundColor Cyan
Write-Host "• Real-time Dashboard: ws://localhost:8000/ws/dashboard/{client_id}" -ForegroundColor White
Write-Host "• Well Data Stream: ws://localhost:8000/ws/well/{well_id}/{client_id}" -ForegroundColor White
Write-Host "• Anomaly Alerts: ws://localhost:8000/ws/anomalies/{client_id}" -ForegroundColor White

Write-Host "\nInfrastructure Services:" -ForegroundColor Cyan
Write-Host "• MinIO Console: http://localhost:9001 (fidps_admin/fidps_minio_password_2024)" -ForegroundColor White
Write-Host "• Kafka Connect: http://localhost:8083" -ForegroundColor White
Write-Host "• PostgreSQL: localhost:5432 (fidps_user/fidps_password_2024)" -ForegroundColor White
Write-Host "• MongoDB: localhost:27017 (root/fidps_mongo_password_2024)" -ForegroundColor White
Write-Host "• Redis: localhost:6379" -ForegroundColor White

Write-Host "\nSystem is ready for real-time drilling data processing, anomaly detection, and monitoring!" -ForegroundColor Green
Write-Host "\n" -ForegroundColor White
Write-Host "To stop the system, run: docker-compose down" -ForegroundColor Yellow
Write-Host "To view logs, run: docker-compose logs -f [service-name]" -ForegroundColor Yellow
Write-Host "To check service status, run: docker-compose ps" -ForegroundColor Yellow