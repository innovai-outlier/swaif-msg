# Quick start script for SWAIF Platform - SIMPLIFIED VERSION
# Starts all services in proper dependency order

# Importar sistema de logging
. ".\management\logging_system.ps1"

$StartTime = Get-Date
Initialize-DeploymentLog

Write-Host "=== SWAIF Platform Startup ===" -ForegroundColor Magenta

Write-Host ""
Write-DetailedLog "Iniciando todos os serviços em ordem de dependência..." "INFO"

# Start database layer first
Write-DetailedLog "Step 1: Iniciando camada de banco de dados..." "HEADER"
Write-Host "Step 1: Starting Database Layer..." -ForegroundColor Yellow
& ".\management\service_manager.ps1" -Action start -Service database
Write-DetailedLog "Camada de banco de dados iniciada" "SUCCESS"

# Wait for databases to be ready
Write-DetailedLog "Aguardando inicialização dos bancos de dados (10s)..." "INFO"
Write-Host "Waiting for databases to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Start API layer
Write-DetailedLog "Step 2: Iniciando camada de APIs..." "HEADER"
Write-Host "Step 2: Starting API Layer..." -ForegroundColor Yellow
& ".\management\service_manager.ps1" -Action start -Service api
Write-DetailedLog "Camada de APIs iniciada" "SUCCESS"

# Wait for APIs to be ready
Write-DetailedLog "Aguardando inicialização das APIs (10s)..." "INFO"
Write-Host "Waiting for APIs to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Start application layer
Write-DetailedLog "Step 3: Iniciando camada de aplicação..." "HEADER"
Write-Host "Step 3: Starting Application Layer..." -ForegroundColor Yellow
& ".\management\service_manager.ps1" -Action start -Service app
Write-DetailedLog "Camada de aplicação iniciada" "SUCCESS"

# Final status check
Write-DetailedLog "Step 4: Verificando status do sistema..." "HEADER"
Write-Host "Step 4: Checking System Status..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
& ".\management\service_manager.ps1" -Action status -Service all

$EndTime = Get-Date
$Duration = $EndTime - $StartTime
Write-DetailedLog "Deployment completo! Duração total: $($Duration.TotalSeconds) segundos" "SUCCESS"

Write-Host ""
Write-DetailedLog "=== SWAIF Platform completamente iniciada ===" "SUCCESS"
Write-Host "=== SWAIF Platform Started ===" -ForegroundColor Green
Write-Host ""
Write-Host "UI Access Points:" -ForegroundColor Cyan
Write-Host "• N8N Workflow Engine: http://localhost:5678 (admin/swaif123)" -ForegroundColor White
Write-Host "• Evolution API Manager: http://localhost:8080/manager" -ForegroundColor White
Write-Host "• SWAIF Analytics App: http://localhost:8501" -ForegroundColor White
Write-DetailedLog "Pontos de acesso UI disponíveis: N8N (5678), Evolution API (8080), SWAIF App (8501)" "INFO"
Write-Host ""
Write-Host "To monitor services: .\management\monitor_services.ps1" -ForegroundColor Yellow
Write-Host "To stop all services: .\management\stop_all.ps1" -ForegroundColor Yellow

# Finalizar log de deployment
Finalize-DeploymentLog -StartTime $StartTime
