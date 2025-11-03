# FIDPS Dashboard Startup Script
# این اسکریپت dashboard را اجرا می‌کند

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FIDPS Dashboard Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for Node.js
Write-Host "Checking for Node.js..." -ForegroundColor Yellow
$nodeVersion = Get-Command node -ErrorAction SilentlyContinue

if (-not $nodeVersion) {
    Write-Host "❌ Node.js not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Node.js first:" -ForegroundColor Yellow
    Write-Host "1. Visit: https://nodejs.org" -ForegroundColor White
    Write-Host "2. Download LTS version (18.x or 20.x)" -ForegroundColor White
    Write-Host "3. Install and restart PowerShell" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use Docker instead:" -ForegroundColor Yellow
    Write-Host "  docker-compose up frontend-react" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✅ Node.js found: $(node --version)" -ForegroundColor Green
Write-Host "✅ npm found: $(npm --version)" -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "frontend-react")) {
    Write-Host "❌ Error: frontend-react directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

# Change to frontend-react directory
Set-Location frontend-react
Write-Host "Changed to frontend-react directory" -ForegroundColor Green
Write-Host ""

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    Write-Host "This may take a few minutes..." -ForegroundColor Gray
    Write-Host ""
    
    npm install --legacy-peer-deps
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies!" -ForegroundColor Red
        Write-Host "Try running: npm install --legacy-peer-deps manually" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
    Write-Host ""
}

# Check if backend is running
Write-Host "Checking backend API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ Backend API is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend API not responding (http://localhost:8000)" -ForegroundColor Yellow
    Write-Host "   Dashboard will still start, but API calls may fail." -ForegroundColor Gray
    Write-Host "   To start backend: docker-compose up api-dashboard" -ForegroundColor Gray
}
Write-Host ""

# Start the dev server
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Dashboard..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dashboard will be available at:" -ForegroundColor Yellow
Write-Host "  http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

npm run dev

