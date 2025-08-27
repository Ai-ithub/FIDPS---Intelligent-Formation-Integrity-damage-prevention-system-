# FIDPS Data Validation Service Startup Script (PowerShell)
# This script starts the Flink data validation service on Windows

param(
    [switch]$Build,
    [switch]$Logs,
    [switch]$Stop,
    [switch]$Status,
    [string]$Environment = "development"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Configuration
$SERVICE_NAME = "fidps-flink-validation"
$COMPOSE_FILE = "..\..\docker-compose.yml"
$PROJECT_NAME = "fidps"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    switch ($Color) {
        "Red" { Write-Host $Message -ForegroundColor Red }
        "Green" { Write-Host $Message -ForegroundColor Green }
        "Yellow" { Write-Host $Message -ForegroundColor Yellow }
        "Blue" { Write-Host $Message -ForegroundColor Blue }
        "Cyan" { Write-Host $Message -ForegroundColor Cyan }
        "Magenta" { Write-Host $Message -ForegroundColor Magenta }
        default { Write-Host $Message }
    }
}

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to check service status
function Get-ServiceStatus {
    try {
        $status = docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps $SERVICE_NAME --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
        return $status
    }
    catch {
        return "Service not found or error occurred"
    }
}

# Function to wait for service to be ready
function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$MaxAttempts = 30,
        [int]$DelaySeconds = 5
    )
    
    Write-ColorOutput "Waiting for $ServiceName to be ready at $Url..." "Yellow"
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "✓ $ServiceName is ready" "Green"
                return $true
            }
        }
        catch {
            # Service not ready yet
        }
        
        Write-ColorOutput "Waiting for $ServiceName... (attempt $i/$MaxAttempts)" "Yellow"
        Start-Sleep -Seconds $DelaySeconds
    }
    
    Write-ColorOutput "✗ $ServiceName failed to start after $MaxAttempts attempts" "Red"
    return $false
}

# Function to create Kafka topics
function New-KafkaTopics {
    Write-ColorOutput "Creating Kafka topics for data validation..." "Blue"
    
    $topics = @(
        "data-validation-results",
        "data-quality-metrics",
        "validation-alerts",
        "validation-errors"
    )
    
    foreach ($topic in $topics) {
        Write-ColorOutput "Creating topic: $topic" "Cyan"
        try {
            docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec kafka kafka-topics.sh --create `
                --topic $topic `
                --bootstrap-server localhost:9092 `
                --partitions 3 `
                --replication-factor 1 `
                --if-not-exists `
                --config cleanup.policy=delete `
                --config retention.ms=604800000
        }
        catch {
            Write-ColorOutput "Topic $topic might already exist or Kafka is not ready" "Yellow"
        }
    }
}

# Function to show service logs
function Show-ServiceLogs {
    Write-ColorOutput "Showing logs for $SERVICE_NAME..." "Blue"
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f $SERVICE_NAME
}

# Function to stop service
function Stop-ValidationService {
    Write-ColorOutput "Stopping FIDPS Data Validation Service..." "Yellow"
    
    try {
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME stop $SERVICE_NAME
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME rm -f $SERVICE_NAME
        Write-ColorOutput "✓ Service stopped successfully" "Green"
    }
    catch {
        Write-ColorOutput "✗ Error stopping service: $($_.Exception.Message)" "Red"
        exit 1
    }
}

# Function to build service
function Build-ValidationService {
    Write-ColorOutput "Building FIDPS Data Validation Service..." "Blue"
    
    try {
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME build $SERVICE_NAME
        Write-ColorOutput "✓ Service built successfully" "Green"
    }
    catch {
        Write-ColorOutput "✗ Error building service: $($_.Exception.Message)" "Red"
        exit 1
    }
}

# Function to start validation service
function Start-ValidationService {
    Write-ColorOutput "Starting FIDPS Data Validation Service..." "Blue"
    Write-ColorOutput "=========================================" "Blue"
    
    # Check Docker
    if (-not (Test-DockerRunning)) {
        Write-ColorOutput "✗ Docker is not running. Please start Docker Desktop." "Red"
        exit 1
    }
    
    Write-ColorOutput "✓ Docker is running" "Green"
    
    # Check if dependencies are running
    Write-ColorOutput "Checking dependencies..." "Yellow"
    
    $dependencies = @(
        @{Name="Zookeeper"; Service="zookeeper"; Url="http://localhost:2181"},
        @{Name="Kafka"; Service="kafka"; Url="http://localhost:9092"},
        @{Name="PostgreSQL"; Service="postgres"; Url="http://localhost:5432"},
        @{Name="MongoDB"; Service="mongo"; Url="http://localhost:27017"},
        @{Name="Redis"; Service="redis"; Url="http://localhost:6379"}
    )
    
    foreach ($dep in $dependencies) {
        $status = docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps $dep.Service --format "{{.Status}}"
        if ($status -notlike "*Up*") {
            Write-ColorOutput "Starting dependency: $($dep.Name)" "Yellow"
            docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d $dep.Service
            Start-Sleep -Seconds 10
        } else {
            Write-ColorOutput "✓ $($dep.Name) is already running" "Green"
        }
    }
    
    # Start the validation service
    Write-ColorOutput "Starting Flink Data Validation service..." "Blue"
    
    try {
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d $SERVICE_NAME
        
        # Wait for service to be ready
        if (Wait-ForService "Flink JobManager" "http://localhost:8081/overview") {
            # Create Kafka topics
            Start-Sleep -Seconds 10
            New-KafkaTopics
            
            # Show service status
            Write-ColorOutput "`nService Status:" "Green"
            Get-ServiceStatus
            
            Write-ColorOutput "`n✓ FIDPS Data Validation Service started successfully!" "Green"
            Write-ColorOutput "`nAccess URLs:" "Cyan"
            Write-ColorOutput "  • Flink Web UI: http://localhost:8081" "White"
            Write-ColorOutput "  • Prometheus Metrics: http://localhost:9249/metrics" "White"
            Write-ColorOutput "`nUseful Commands:" "Cyan"
            Write-ColorOutput "  • View logs: .\start-validation-service.ps1 -Logs" "White"
            Write-ColorOutput "  • Check status: .\start-validation-service.ps1 -Status" "White"
            Write-ColorOutput "  • Stop service: .\start-validation-service.ps1 -Stop" "White"
            Write-ColorOutput "  • Rebuild service: .\start-validation-service.ps1 -Build" "White"
        } else {
            Write-ColorOutput "✗ Service failed to start properly" "Red"
            exit 1
        }
    }
    catch {
        Write-ColorOutput "✗ Error starting service: $($_.Exception.Message)" "Red"
        exit 1
    }
}

# Main script logic
Write-ColorOutput "FIDPS Data Validation Service Manager" "Magenta"
Write-ColorOutput "====================================" "Magenta"

try {
    # Change to script directory
    Set-Location $PSScriptRoot
    
    if ($Stop) {
        Stop-ValidationService
    }
    elseif ($Build) {
        Build-ValidationService
    }
    elseif ($Logs) {
        Show-ServiceLogs
    }
    elseif ($Status) {
        Write-ColorOutput "Service Status:" "Blue"
        Get-ServiceStatus
        
        # Check if Flink UI is accessible
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8081/overview" -Method GET -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "✓ Flink Web UI is accessible at http://localhost:8081" "Green"
            }
        }
        catch {
            Write-ColorOutput "✗ Flink Web UI is not accessible" "Red"
        }
        
        # Check metrics endpoint
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:9249/metrics" -Method GET -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "✓ Prometheus metrics are accessible at http://localhost:9249/metrics" "Green"
            }
        }
        catch {
            Write-ColorOutput "✗ Prometheus metrics are not accessible" "Red"
        }
    }
    else {
        Start-ValidationService
    }
}
catch {
    Write-ColorOutput "✗ An error occurred: $($_.Exception.Message)" "Red"
    exit 1
}

Write-ColorOutput "`nDone!" "Green"