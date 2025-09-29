# FIDPS ML Anomaly Detection Service Management Script
# PowerShell script for Windows

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "build", "clean")]
    [string]$Action = "start"
)

# Configuration
$SERVICE_NAME = "fidps-ml-anomaly-detection"
$COMPOSE_FILE = "../docker-compose.yml"
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ML_SERVICE_DIR = Join-Path $PROJECT_ROOT "ml-anomaly-detection"

# Colors for output
$GREEN = "`e[32m"
$RED = "`e[31m"
$YELLOW = "`e[33m"
$BLUE = "`e[34m"
$NC = "`e[0m" # No Color

function Write-ColorOutput {
    param([string]$Message, [string]$Color = $NC)
    Write-Host "${Color}${Message}${NC}"
}

function Check-Prerequisites {
    Write-ColorOutput "Checking prerequisites..." $BLUE
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-ColorOutput "✓ Docker found: $dockerVersion" $GREEN
    } catch {
        Write-ColorOutput "✗ Docker not found. Please install Docker Desktop." $RED
        exit 1
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-ColorOutput "✓ Docker Compose found: $composeVersion" $GREEN
    } catch {
        Write-ColorOutput "✗ Docker Compose not found. Please install Docker Compose." $RED
        exit 1
    }
    
    # Check if Docker is running
    try {
        docker info | Out-Null
        Write-ColorOutput "✓ Docker daemon is running" $GREEN
    } catch {
        Write-ColorOutput "✗ Docker daemon is not running. Please start Docker Desktop." $RED
        exit 1
    }
}

function Wait-ForService {
    param([string]$ServiceName, [string]$HealthEndpoint, [int]$MaxWaitTime = 300)
    
    Write-ColorOutput "Waiting for $ServiceName to be ready..." $YELLOW
    $waitTime = 0
    $interval = 5
    
    while ($waitTime -lt $MaxWaitTime) {
        try {
            $response = Invoke-WebRequest -Uri $HealthEndpoint -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "✓ $ServiceName is ready!" $GREEN
                return $true
            }
        } catch {
            # Service not ready yet
        }
        
        Start-Sleep $interval
        $waitTime += $interval
        Write-Host "." -NoNewline
    }
    
    Write-ColorOutput "`n✗ $ServiceName failed to start within $MaxWaitTime seconds" $RED
    return $false
}

function Check-DependentServices {
    Write-ColorOutput "Checking dependent services..." $BLUE
    
    $services = @(
        @{Name="Zookeeper"; Port=2181},
        @{Name="Kafka"; Port=9092},
        @{Name="PostgreSQL"; Port=5432},
        @{Name="MongoDB"; Port=27017},
        @{Name="Redis"; Port=6379}
    )
    
    foreach ($service in $services) {
        try {
            $connection = Test-NetConnection -ComputerName localhost -Port $service.Port -WarningAction SilentlyContinue
            if ($connection.TcpTestSucceeded) {
                Write-ColorOutput "✓ $($service.Name) is running on port $($service.Port)" $GREEN
            } else {
                Write-ColorOutput "✗ $($service.Name) is not running on port $($service.Port)" $RED
                Write-ColorOutput "Please start the FIDPS infrastructure services first." $YELLOW
                exit 1
            }
        } catch {
            Write-ColorOutput "✗ Failed to check $($service.Name) on port $($service.Port)" $RED
            exit 1
        }
    }
}

function Build-Service {
    Write-ColorOutput "Building ML Anomaly Detection service..." $BLUE
    
    Set-Location $PROJECT_ROOT
    
    try {
        docker-compose build ml-anomaly-detection
        Write-ColorOutput "✓ Service built successfully" $GREEN
    } catch {
        Write-ColorOutput "✗ Failed to build service" $RED
        exit 1
    }
}

function Start-Service {
    Write-ColorOutput "Starting ML Anomaly Detection service..." $BLUE
    
    Set-Location $PROJECT_ROOT
    
    # Create necessary directories
    $directories = @(
        "ml-anomaly-detection/logs",
        "ml-anomaly-detection/models",
        "ml-anomaly-detection/data",
        "ml-anomaly-detection/cache"
    )
    
    foreach ($dir in $directories) {
        $fullPath = Join-Path $PROJECT_ROOT $dir
        if (!(Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-ColorOutput "Created directory: $dir" $GREEN
        }
    }
    
    try {
        docker-compose up -d ml-anomaly-detection
        Write-ColorOutput "✓ Service started successfully" $GREEN
        
        # Wait for service to be ready
        if (Wait-ForService "ML Anomaly Detection" "http://localhost:8080/health" 120) {
            Write-ColorOutput "" $NC
            Write-ColorOutput "=== FIDPS ML Anomaly Detection Service Started ===" $GREEN
            Write-ColorOutput "Service Status: http://localhost:8080/health" $BLUE
            Write-ColorOutput "Metrics Endpoint: http://localhost:9090/metrics" $BLUE
            Write-ColorOutput "API Documentation: http://localhost:8080/docs" $BLUE
            Write-ColorOutput "" $NC
        }
    } catch {
        Write-ColorOutput "✗ Failed to start service" $RED
        exit 1
    }
}

function Stop-Service {
    Write-ColorOutput "Stopping ML Anomaly Detection service..." $BLUE
    
    Set-Location $PROJECT_ROOT
    
    try {
        docker-compose stop ml-anomaly-detection
        Write-ColorOutput "✓ Service stopped successfully" $GREEN
    } catch {
        Write-ColorOutput "✗ Failed to stop service" $RED
        exit 1
    }
}

function Restart-Service {
    Write-ColorOutput "Restarting ML Anomaly Detection service..." $BLUE
    Stop-Service
    Start-Sleep 5
    Start-Service
}

function Get-ServiceStatus {
    Write-ColorOutput "Checking ML Anomaly Detection service status..." $BLUE
    
    Set-Location $PROJECT_ROOT
    
    try {
        $status = docker-compose ps ml-anomaly-detection
        Write-Output $status
        
        # Check health endpoint
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "✓ Service is healthy" $GREEN
            }
        } catch {
            Write-ColorOutput "✗ Service health check failed" $RED
        }
    } catch {
        Write-ColorOutput "✗ Failed to get service status" $RED
        exit 1
    }
}

function Show-Logs {
    Write-ColorOutput "Showing ML Anomaly Detection service logs..." $BLUE
    
    Set-Location $PROJECT_ROOT
    
    try {
        docker-compose logs -f ml-anomaly-detection
    } catch {
        Write-ColorOutput "✗ Failed to show logs" $RED
        exit 1
    }
}

function Clean-Service {
    Write-ColorOutput "Cleaning ML Anomaly Detection service..." $BLUE
    
    Set-Location $PROJECT_ROOT
    
    try {
        docker-compose down ml-anomaly-detection
        docker-compose rm -f ml-anomaly-detection
        docker rmi fidps_ml-anomaly-detection -f 2>$null
        Write-ColorOutput "✓ Service cleaned successfully" $GREEN
    } catch {
        Write-ColorOutput "✗ Failed to clean service" $RED
        exit 1
    }
}

# Main execution
Write-ColorOutput "FIDPS ML Anomaly Detection Service Manager" $BLUE
Write-ColorOutput "============================================" $BLUE

switch ($Action.ToLower()) {
    "build" {
        Check-Prerequisites
        Build-Service
    }
    "start" {
        Check-Prerequisites
        Check-DependentServices
        Start-Service
    }
    "stop" {
        Check-Prerequisites
        Stop-Service
    }
    "restart" {
        Check-Prerequisites
        Check-DependentServices
        Restart-Service
    }
    "status" {
        Check-Prerequisites
        Get-ServiceStatus
    }
    "logs" {
        Check-Prerequisites
        Show-Logs
    }
    "clean" {
        Check-Prerequisites
        Clean-Service
    }
    default {
        Write-ColorOutput "Usage: .\start-ml-service.ps1 [start|stop|restart|status|logs|build|clean]" $YELLOW
        Write-ColorOutput "" $NC
        Write-ColorOutput "Commands:" $BLUE
        Write-ColorOutput "  start   - Start the ML anomaly detection service" $NC
        Write-ColorOutput "  stop    - Stop the ML anomaly detection service" $NC
        Write-ColorOutput "  restart - Restart the ML anomaly detection service" $NC
        Write-ColorOutput "  status  - Show service status" $NC
        Write-ColorOutput "  logs    - Show service logs" $NC
        Write-ColorOutput "  build   - Build the service image" $NC
        Write-ColorOutput "  clean   - Clean up service containers and images" $NC
        exit 1
    }
}

Write-ColorOutput "Operation completed." $GREEN