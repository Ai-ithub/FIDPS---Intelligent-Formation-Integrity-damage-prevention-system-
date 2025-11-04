# Script to download Chart.js for offline dashboard use
# Run this script in PowerShell: .\download-chartjs.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Chart.js Downloader for Offline Dashboard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$chartJsUrl = "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"
$outputFile = "chart.umd.min.js"

# Check if file already exists
if (Test-Path $outputFile) {
    Write-Host "Warning: $outputFile already exists!" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (Y/N)"
    if ($overwrite -ne "Y" -and $overwrite -ne "y") {
        Write-Host "Download cancelled." -ForegroundColor Red
        exit
    }
}

Write-Host "Downloading Chart.js from CDN..." -ForegroundColor Green
Write-Host "URL: $chartJsUrl" -ForegroundColor Gray
Write-Host ""

try {
    # Download the file
    Invoke-WebRequest -Uri $chartJsUrl -OutFile $outputFile -UseBasicParsing
    
    if (Test-Path $outputFile) {
        $fileSize = (Get-Item $outputFile).Length / 1KB
        Write-Host ""
        Write-Host "✅ Success!" -ForegroundColor Green
        Write-Host "Chart.js downloaded successfully!" -ForegroundColor Green
        Write-Host "File: $outputFile" -ForegroundColor Gray
        Write-Host "Size: $([math]::Round($fileSize, 2)) KB" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Now you can run dashboard-html-demo.html offline!" -ForegroundColor Cyan
        Write-Host "Just double-click on dashboard-html-demo.html" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Error: File was not downloaded!" -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "❌ Error downloading Chart.js:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check your internet connection and try again." -ForegroundColor Yellow
    Write-Host "Or manually download from: $chartJsUrl" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
