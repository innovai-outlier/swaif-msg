# SWAIF Platform - Stop Complete Stack
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'UTF8'

function Write-Header {
    Write-Host ""
    Write-Host "===============================================================================" -ForegroundColor Red
    Write-Host "                        SWAIF PLATFORM - STOP STACK                           " -ForegroundColor Red
    Write-Host "===============================================================================" -ForegroundColor Red
    Write-Host ""
}

function Stop-Service {
    param($ServiceName, $Path)
    
    Write-Host ">> Stopping $ServiceName..." -ForegroundColor Yellow
    
    if (Test-Path $Path) {
        Push-Location $Path
        
        try {
            docker compose down
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✓ $ServiceName stopped successfully!" -ForegroundColor Green
                Pop-Location
                return $true
            } else {
                Write-Host "   ✗ Error stopping $ServiceName" -ForegroundColor Red
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

Write-Host "STOPPING ALL SERVICES..." -ForegroundColor Cyan
Write-Host ""

# Reverse shutdown order (application -> API)
$services = @(
    @{Name="N8N Workflows"; Path=".\n8n"},
    @{Name="Evolution API"; Path=".\evoapi"}
)

$results = @()
$originalLocation = Get-Location

foreach ($service in $services) {
    Set-Location $originalLocation
    $result = Stop-Service -ServiceName $service.Name -Path $service.Path
    $results += @{Service=$service.Name; Success=$result}
    Write-Host ""
    Start-Sleep -Seconds 2
}

Set-Location $originalLocation

Write-Host ""
Write-Host "SHUTDOWN SUMMARY:" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor Gray

foreach ($result in $results) {
    if ($result.Success) {
        Write-Host "  ✓ $($result.Service)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($result.Service)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "CHECKING REMAINING CONTAINERS..." -ForegroundColor Yellow

try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}"
    if ($containers -and $containers.Trim() -ne "" -and $containers -notmatch "^NAMES") {
        Write-Host "Containers still active:" -ForegroundColor Yellow
        Write-Host $containers -ForegroundColor White
    } else {
        Write-Host "✓ All containers have been stopped successfully!" -ForegroundColor Green
    }
} catch {
    Write-Host "Error checking containers: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "SWAIF STACK STOPPED!" -ForegroundColor Green
