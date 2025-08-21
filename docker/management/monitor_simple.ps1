# SWAIF Platform - Simple Service Monitor
param(
    [int]$RefreshInterval = 10,
    [switch]$Compact
)

# UTF-8 Configuration
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'UTF8'

# Header function
function Show-Header {
    Clear-Host
    Write-Host ""
    Write-Host "=" * 79 -ForegroundColor Cyan
    Write-Host " SWAIF PLATFORM - REAL-TIME SERVICE MONITOR".PadLeft(52) -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host "=" * 79 -ForegroundColor Cyan
    Write-Host ""
}

# Service status check
function Get-ServiceStatus {
    param([string]$ContainerName)
    
    try {
        $result = docker ps --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}" | Select-Object -Skip 1
        if ($result) {
            return "Running"
        } else {
            return "Stopped"
        }
    } catch {
        return "Error"
    }
}

# Service health check
function Test-ServiceHealth {
    param([string]$ContainerName)
    
    switch ($ContainerName) {
        "postgres_swaif" {
            try {
                $result = docker exec postgres_swaif pg_isready -U postgres -d evolution 2>$null
                return ($LASTEXITCODE -eq 0)
            } catch {
                return $false
            }
        }
        "redis_swaif" {
            try {
                $result = docker exec redis_swaif redis-cli ping 2>$null
                return ($result -eq "PONG")
            } catch {
                return $false
            }
        }
        default {
            try {
                $status = Get-ServiceStatus -ContainerName $ContainerName
                return ($status -eq "Running")
            } catch {
                return $false
            }
        }
    }
}

# Main monitoring loop
function Start-Monitor {
    $services = @(
        @{Name="postgres"; Container="postgres_swaif"},
        @{Name="redis"; Container="redis_swaif"},
        @{Name="evolution"; Container="evolution_swaif"},
        @{Name="n8n"; Container="n8n_swaif"},
        @{Name="minio"; Container="minio_swaif"},
        @{Name="adminjs"; Container="adminjs_swaif"}
    )
    
    while ($true) {
        Show-Header
        
        Write-Host " Service Status Report - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Yellow
        Write-Host ""
        Write-Host " Service".PadRight(15) + "Status".PadRight(12) + "Health".PadRight(12) + "Container" -ForegroundColor Gray
        Write-Host " " + "-" * 70 -ForegroundColor Gray
        
        foreach ($service in $services) {
            $status = Get-ServiceStatus -ContainerName $service.Container
            $health = Test-ServiceHealth -ContainerName $service.Container
            
            $statusColor = if ($status -eq "Running") { "Green" } else { "Red" }
            $healthColor = if ($health) { "Green" } else { "Red" }
            $healthText = if ($health) { "Healthy" } else { "Unhealthy" }
            
            Write-Host " $($service.Name)".PadRight(15) -NoNewline
            Write-Host $status.PadRight(12) -ForegroundColor $statusColor -NoNewline
            Write-Host $healthText.PadRight(12) -ForegroundColor $healthColor -NoNewline
            Write-Host $service.Container
        }
        
        Write-Host ""
        Write-Host " Commands:" -ForegroundColor Yellow
        Write-Host "   [Q] Quit    [R] Refresh Now    [S] Service Details" -ForegroundColor Gray
        Write-Host ""
        Write-Host " Auto-refresh in $RefreshInterval seconds..." -ForegroundColor Gray
        
        # Wait for input or timeout
        $timeout = $RefreshInterval * 1000
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        
        while ($sw.ElapsedMilliseconds -lt $timeout) {
            if ([Console]::KeyAvailable) {
                $key = [Console]::ReadKey($true)
                switch ($key.KeyChar.ToString().ToUpper()) {
                    'Q' { 
                        Write-Host ""
                        Write-Host " Monitor stopped." -ForegroundColor Yellow
                        return 
                    }
                    'R' { 
                        break 
                    }
                    'S' {
                        Show-ServiceDetails
                        break
                    }
                }
                break
            }
            Start-Sleep -Milliseconds 100
        }
        $sw.Stop()
    }
}

function Show-ServiceDetails {
    Clear-Host
    Write-Host ""
    Write-Host "=" * 79 -ForegroundColor Cyan
    Write-Host " SERVICE DETAILS".PadLeft(47) -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host "=" * 79 -ForegroundColor Cyan
    Write-Host ""
    
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host $containers
    
    Write-Host ""
    Write-Host " Press any key to return to monitor..." -ForegroundColor Gray
    [Console]::ReadKey($true) | Out-Null
}

# Start the monitor
Show-Header
Write-Host " Starting SWAIF Platform Monitor..." -ForegroundColor Green
Write-Host " Press Ctrl+C or 'Q' to quit" -ForegroundColor Gray
Write-Host ""
Start-Sleep -Seconds 2

try {
    Start-Monitor
} catch {
    Write-Host ""
    Write-Host " Monitor error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host " Press any key to exit..." -ForegroundColor Gray
    [Console]::ReadKey($true) | Out-Null
}
