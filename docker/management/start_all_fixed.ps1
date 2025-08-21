# SWAIF Platform - Deploy Complete Stack
param([switch]$Force)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'UTF8'

function Write-Header {
    Write-Host ""
    Write-Host "===============================================================================" -ForegroundColor Green
    Write-Host "                        SWAIF PLATFORM - DEPLOY STACK                         " -ForegroundColor Green
    Write-Host "===============================================================================" -ForegroundColor Green
    Write-Host ""
}

function Start-Service {
    param($ServiceName, $Path)
    
    Write-Host ">> Starting $ServiceName..." -ForegroundColor Yellow
    
    if (Test-Path $Path) {
        Push-Location $Path
        
        try {
            Write-Host "   Checking existing containers..." -ForegroundColor Gray
            docker compose down 2>$null
            
            Write-Host "   Bringing up services..." -ForegroundColor Gray
            docker compose up -d
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✓ $ServiceName started successfully!" -ForegroundColor Green
                Pop-Location
                return $true
            } else {
                Write-Host "   ✗ Error starting $ServiceName" -ForegroundColor Red
                Pop-Location
                return $false
            }
        } catch {
            Write-Host "   ✗ Error: $_" -ForegroundColor Red
            Pop-Location
            return $false
        }
    } else {
        Write-Host "   ✗ Folder not found: $Path" -ForegroundColor Red
        return $false
    }
}

Write-Header

Write-Host "STARTING SEQUENTIAL SERVICE DEPLOYMENT..." -ForegroundColor Cyan
Write-Host ""

# Define startup order
$services = @(
    @{Name="Evolution API (WhatsApp + DB + Redis)"; Path=".\evoapi"},
    @{Name="N8N Workflows (Automation + DB + Redis)"; Path=".\n8n"}
)

$results = @()
$originalLocation = Get-Location

foreach ($service in $services) {
    Set-Location $originalLocation
    $result = Start-Service -ServiceName $service["Name"] -Path $service["Path"]
    $results += @{Service=$service["Name"]; Success=$result}
    Write-Host ""
    Start-Sleep -Seconds 3
}

Set-Location $originalLocation

Write-Host ""
Write-Host "DEPLOYMENT SUMMARY:" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Gray

foreach ($result in $results) {
    if ($result["Success"]) {
        Write-Host "  ✓ $($result["Service"])" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($result["Service"])" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "CHECKING CONTAINER STATUS..." -ForegroundColor Yellow

try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    if ($containers) {
        Write-Host $containers -ForegroundColor White
    } else {
        Write-Host "No active containers found." -ForegroundColor Red
    }
} catch {
    Write-Host "Error checking containers: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "SERVICE ACCESS:" -ForegroundColor Cyan
Write-Host "==============" -ForegroundColor Gray
Write-Host "  - Evolution API: http://localhost:8080" -ForegroundColor White
Write-Host "  - N8N Workflows: http://localhost:5678" -ForegroundColor White
Write-Host ""
Write-Host "SWAIF STACK READY FOR USE!" -ForegroundColor Green
