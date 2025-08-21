# SWAIF Platform Manager
param([string]$Action = "menu")

# UTF-8 configuration to avoid strange characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'UTF8'

if (-not (Test-Path ".\management\service_manager.ps1")) {
    Write-Host "Error: Execute this script from the docker/ directory" -ForegroundColor Red
    exit 1
}

function Show-Header {
    Clear-Host
    Write-Host ""
    Write-Host "===============================================================================" -ForegroundColor Cyan
    Write-Host "                        SWAIF PLATFORM - DOCKER MANAGER                       " -ForegroundColor Cyan
    Write-Host "                           Advanced Modular Architecture                       " -ForegroundColor White
    Write-Host "===============================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Show-ProjectStructure {
    Write-Host "PROJECT STRUCTURE" -ForegroundColor Cyan
    Write-Host "=================" -ForegroundColor Gray
    Write-Host ""
    Write-Host "docker/" -ForegroundColor White
    Write-Host "  main.ps1              # Main interface (this file)" -ForegroundColor Magenta
    Write-Host "  evoapi/               # WhatsApp Evolution API" -ForegroundColor Yellow
    Write-Host "    docker-compose.yaml # Evolution API + PostgreSQL + Redis service" -ForegroundColor Blue
    Write-Host "    .env                # Evolution API configuration" -ForegroundColor Gray
    Write-Host "    from_git/           # Official Evolution API repository" -ForegroundColor Green
    Write-Host "  n8n/                  # Workflow Engine N8N" -ForegroundColor Cyan
    Write-Host "    docker-compose.yml  # N8N + PostgreSQL + Redis + Traefik service" -ForegroundColor Blue
    Write-Host "    .env                # N8N configuration" -ForegroundColor Gray
    Write-Host "    init-data.sh        # N8N database initialization script" -ForegroundColor White
    Write-Host "  management/           # Management scripts" -ForegroundColor Gray
    Write-Host "    service_manager.ps1 # Service manager" -ForegroundColor White
    Write-Host "    monitor_services.ps1# Real-time monitor" -ForegroundColor Cyan
    Write-Host "    start_all.ps1       # Complete deployment" -ForegroundColor Green
    Write-Host "    stop_all.ps1        # Coordinated shutdown" -ForegroundColor Red
    Write-Host ""
}

function Show-MainMenu {
    Write-Host "AVAILABLE ACTIONS:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  [1] Deploy Stack        # Start all containers" -ForegroundColor Green
    Write-Host "  [2] Monitor Dashboard   # Real-time monitoring" -ForegroundColor Cyan
    Write-Host "  [3] Web Access          # Open services in browser" -ForegroundColor Blue
    Write-Host "  [4] Quick Status        # Point-in-time check" -ForegroundColor White
    Write-Host "  [5] Stop Stack          # Shutdown all containers" -ForegroundColor Red
    Write-Host "  [6] System Check        # Pre-deployment verification" -ForegroundColor Magenta
    Write-Host "  [7] Complete Cleanup    # Remove all data (CAUTION!)" -ForegroundColor DarkRed
    Write-Host "  [8] Project Structure   # Show folder organization" -ForegroundColor Yellow
    Write-Host "  [0] Exit" -ForegroundColor Gray
    Write-Host ""
}

function Show-QuickStatus {
    Clear-Host
    Show-Header
    Write-Host "STACK QUICK STATUS" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Active Docker Containers:" -ForegroundColor Cyan
    try {
        $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
        if ($containers -and $containers.Count -gt 0) {
            # Split into lines and display formatted
            $lines = $containers -split "`r?`n" | Where-Object { $_.Trim() -ne "" }
            foreach ($line in $lines) {
                Write-Host "  $line" -ForegroundColor Green
            }
            Write-Host ""
        } else {
            Write-Host "  >> No containers running" -ForegroundColor Red
            Write-Host ""
        }
    } catch {
        Write-Host "  >> Error checking containers: $_" -ForegroundColor Red
        Write-Host ""
    }
    
    Write-Host "Service URLs:" -ForegroundColor Cyan
    Write-Host "  - Evolution API:      http://localhost:8080" -ForegroundColor White
    Write-Host "  - N8N Workflows:      http://localhost:5678" -ForegroundColor White  
    Write-Host "  - PostgreSQL (EvoAPI): localhost:5432" -ForegroundColor Gray
    Write-Host "  - Redis (EvoAPI):     localhost:6379" -ForegroundColor Gray
    Write-Host ""
}

function Open-WebServices {
    Clear-Host
    Show-Header
    Write-Host "AVAILABLE WEB SERVICES" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Select the service to open in browser:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [1] Evolution API       # WhatsApp API and management" -ForegroundColor Green
    Write-Host "      >> http://localhost:8080" -ForegroundColor White
    Write-Host ""
    Write-Host "  [2] N8N Workflows       # Automation and workflows" -ForegroundColor Blue
    Write-Host "      >> http://localhost:5678" -ForegroundColor White
    Write-Host ""
    Write-Host "  [3] Open All            # Opens all services" -ForegroundColor Yellow
    Write-Host "  [0] Back to Menu        # Return to main menu" -ForegroundColor Gray
    Write-Host ""
    
    $webChoice = Read-Host "Enter your choice (0-3)"
    
    switch ($webChoice) {
        "1" { 
            Start-Process "http://localhost:8080"
            Write-Host ""
            Write-Host ">> Evolution API opened in browser!" -ForegroundColor Green
        }
        "2" { 
            Start-Process "http://localhost:5678"
            Write-Host ""
            Write-Host ">> N8N Workflows opened in browser!" -ForegroundColor Green
        }
        "3" { 
            Start-Process "http://localhost:8080"
            Start-Sleep -Seconds 1
            Start-Process "http://localhost:5678"
            Write-Host ""
            Write-Host ">> All services opened in browser!" -ForegroundColor Green
        }
        "0" { return }
        default { 
            Write-Host ""
            Write-Host ">> Invalid option! Please try again." -ForegroundColor Red
            Start-Sleep -Seconds 1
            return Open-WebServices
        }
    }
    
    if ($webChoice -ne "0") {
        Write-Host ""
        Read-Host "Press Enter to continue..."
    }
}

function Start-InteractiveMenu {
    while ($true) {
        Show-Header
        Show-MainMenu
        
        $choice = Read-Host "Enter your choice (0-8)"
        
        switch ($choice) {
            "1" { 
                Write-Host ""
                Write-Host ">> Starting complete stack deployment..." -ForegroundColor Green
                & ".\management\start_all.ps1"
                Read-Host "Press Enter to continue..."
            }
            "2" { 
                Write-Host ""
                Write-Host ">> Opening services monitor..." -ForegroundColor Cyan
                & ".\management\monitor_services.ps1"
            }
            "3" { 
                Open-WebServices
            }
            "4" { 
                Show-QuickStatus
                Read-Host "Press Enter to continue..."
            }
            "5" { 
                Write-Host ""
                Write-Host ">> Stopping all services..." -ForegroundColor Red
                & ".\management\stop_all.ps1"
                Read-Host "Press Enter to continue..."
            }
            "6" {
                Write-Host ""
                Write-Host ">> Running pre-deployment verification..." -ForegroundColor Yellow
                & ".\management\pre_deployment_check.ps1"
                Read-Host "Press Enter to continue..."
            }
            "7" {
                Write-Host ""
                Write-Host ">> CAUTION: This action removes ALL data!" -ForegroundColor Red
                $confirm = Read-Host "Type 'CONFIRM' to proceed with complete cleanup"
                if ($confirm -eq "CONFIRM") {
                    & ".\management\complete_cleanup.ps1" -Confirm
                } else {
                    Write-Host ">> Operation cancelled." -ForegroundColor Yellow
                }
                Read-Host "Press Enter to continue..."
            }
            "8" {
                Clear-Host
                Show-Header
                Show-ProjectStructure
                Read-Host "Press Enter to continue..."
            }
            "0" { 
                Clear-Host
                Write-Host ""
                Write-Host "===============================================================================" -ForegroundColor Green
                Write-Host "                   Thank you for using SWAIF Platform Manager!                " -ForegroundColor Green
                Write-Host "                   Modular platform ready for professional use!              " -ForegroundColor Cyan
                Write-Host "===============================================================================" -ForegroundColor Green
                Write-Host ""
                return 
            }
            default { 
                Write-Host ""
                Write-Host ">> Invalid option! Please try again." -ForegroundColor Red
                Start-Sleep -Seconds 1
            }
        }
    }
}

switch ($Action) {
    "deploy" { & ".\management\start_all.ps1" }
    "monitor" { & ".\management\monitor_services.ps1" }
    "web" { Open-WebServices; Read-Host "Press Enter to continue..." }
    "stop" { & ".\management\stop_all.ps1" }
    "status" { Show-QuickStatus; Read-Host "Press Enter to continue..." }
    "cleanup" { & ".\management\pre_deployment_check.ps1" }
    "menu" { Start-InteractiveMenu }
    default { Start-InteractiveMenu }
}
