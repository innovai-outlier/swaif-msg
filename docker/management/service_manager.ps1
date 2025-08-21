# SWAIF Platform - Service Manager
# Complete service orchestration with monitoring

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "health")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "database", "api", "app", "n8n", "evolution", "swaif", "postgres", "redis")]
    [string]$Service = "all",
    
    [Parameter(Mandatory=$false)]
    [switch]$Follow
)

# Importar sistema de logging
. ".\management\logging_system.ps1"

# Service definitions
$Services = @{
    "postgres" = @{
        "ComposeFile" = "services_config/postgres/docker-compose.postgres.yml"
        "Container" = "postgres_swaif"
        "HealthURL" = $null
        "UIAccess" = $false
        "Layer" = "database"
    }
    "redis" = @{
        "ComposeFile" = "services_config/redis/docker-compose.redis.yml"
        "Container" = "redis_swaif"
        "HealthURL" = $null
        "UIAccess" = $false
        "Layer" = "database"
    }
    "evolution" = @{
        "ComposeFile" = "services_config/evolution_api/docker-compose.evolution.yml"
        "Container" = "evolution_api_swaif"
        "HealthURL" = "http://localhost:8080/manager"
        "UIAccess" = $true
        "Layer" = "api"
    }
    "n8n" = @{
        "ComposeFile" = "services_config/n8n/docker-compose.n8n.yml"
        "Container" = "n8n_production"
        "HealthURL" = "http://localhost:5678/healthz"
        "UIAccess" = $true
        "Layer" = "api"
    }
    "swaif" = @{
        "ComposeFile" = "services_config/swaif_app/docker-compose.swaif.yml"
        "Container" = "swaif_streamlit_app"
        "HealthURL" = "http://localhost:8501/healthz"
        "UIAccess" = $true
        "Layer" = "app"
    }
}

# Service groups by layer
$ServiceLayers = @{
    "database" = @("postgres", "redis")
    "api" = @("evolution", "n8n")
    "app" = @("swaif")
}

function Write-ServiceStatus {
    param($ServiceName, $Status, $Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Status) {
        "SUCCESS" { "Green" }
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "INFO" { "Cyan" }
        default { "White" }
    }
    Write-Host "[$timestamp] " -NoNewline
    Write-Host "[$Status] " -ForegroundColor $color -NoNewline
    Write-Host "$ServiceName - $Message"
}

function Get-ServiceList {
    param($ServiceParam)
    
    switch ($ServiceParam) {
        "all" { return $Services.Keys }
        "database" { return $ServiceLayers["database"] }
        "api" { return $ServiceLayers["api"] }
        "app" { return $ServiceLayers["app"] }
        default { return @($ServiceParam) }
    }
}

function Start-Service {
    param($ServiceName)
    
    $serviceConfig = $Services[$ServiceName]
    
    # Verificar se já existe container com o mesmo nome
    $existingContainer = docker ps -a -q -f name="^$($serviceConfig.Container)$"
    if ($existingContainer) {
        Write-ServiceStatus $ServiceName "WARNING" "Container already exists, removing old instance..."
        Write-DetailedLog "Container $($serviceConfig.Container) já existe, removendo instância anterior..." "WARNING"
        docker rm -f $serviceConfig.Container 2>$null | Out-Null
    }
    
    Write-ServiceStatus $ServiceName "INFO" "Starting service..."
    Write-DetailedLog "Iniciando serviço $ServiceName..." "INFO"
    
    try {
        $result = docker-compose -f $serviceConfig.ComposeFile up -d 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ServiceStatus $ServiceName "SUCCESS" "Service started successfully"
            Write-DetailedLog "Serviço $ServiceName iniciado com sucesso" "SUCCESS"
            
            # Wait for health check if URL is available
            if ($serviceConfig.HealthURL) {
                Start-Sleep -Seconds 10
                Test-ServiceHealth $ServiceName
            }
        } else {
            Write-ServiceStatus $ServiceName "ERROR" "Failed to start service: $result"
            Write-DetailedLog "Falha ao iniciar serviço $ServiceName`: $result" "ERROR"
        }
    } catch {
        Write-ServiceStatus $ServiceName "ERROR" "Exception starting service: $($_.Exception.Message)"
        Write-DetailedLog "Exceção ao iniciar serviço $ServiceName`: $($_.Exception.Message)" "ERROR"
    }
}

function Stop-Service {
    param($ServiceName)
    
    $serviceConfig = $Services[$ServiceName]
    Write-ServiceStatus $ServiceName "INFO" "Stopping service..."
    
    try {
        $result = docker-compose -f $serviceConfig.ComposeFile down 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ServiceStatus $ServiceName "SUCCESS" "Service stopped successfully"
        } else {
            Write-ServiceStatus $ServiceName "ERROR" "Failed to stop service: $result"
        }
    } catch {
        Write-ServiceStatus $ServiceName "ERROR" "Exception stopping service: $($_.Exception.Message)"
    }
}

function Get-ServiceStatus {
    param($ServiceName)
    
    $serviceConfig = $Services[$ServiceName]
    $container = docker ps -q -f name=$serviceConfig.Container
    
    if ($container) {
        $status = docker inspect $container --format='{{.State.Status}}'
        $uptime = docker inspect $container --format='{{.State.StartedAt}}'
        $health = docker inspect $container --format='{{.State.Health.Status}}' 2>$null
        
        Write-ServiceStatus $ServiceName "INFO" "Status: $status | Started: $uptime | Health: $health"
        
        if ($serviceConfig.UIAccess) {
            Write-ServiceStatus $ServiceName "INFO" "UI Access: $($serviceConfig.HealthURL)"
        }
    } else {
        Write-ServiceStatus $ServiceName "WARNING" "Container not running"
    }
}

function Test-ServiceHealth {
    param($ServiceName)
    
    $serviceConfig = $Services[$ServiceName]
    if (-not $serviceConfig.HealthURL) {
        Write-ServiceStatus $ServiceName "INFO" "No health endpoint configured"
        return
    }
    
    try {
        $response = Invoke-WebRequest -Uri $serviceConfig.HealthURL -Method GET -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-ServiceStatus $ServiceName "SUCCESS" "Health check passed"
        } else {
            Write-ServiceStatus $ServiceName "WARNING" "Health check returned status: $($response.StatusCode)"
        }
    } catch {
        Write-ServiceStatus $ServiceName "ERROR" "Health check failed: $($_.Exception.Message)"
    }
}

function Show-ServiceLogs {
    param($ServiceName)
    
    $serviceConfig = $Services[$ServiceName]
    Write-ServiceStatus $ServiceName "INFO" "Showing logs..."
    
    if ($Follow) {
        docker-compose -f $serviceConfig.ComposeFile logs -f
    } else {
        docker-compose -f $serviceConfig.ComposeFile logs --tail=50
    }
}

# Main execution
$servicesToProcess = Get-ServiceList $Service

Write-Host "=== SWAIF Platform Service Manager ===" -ForegroundColor Magenta
Write-Host "Action: $Action | Target: $Service | Services: $($servicesToProcess -join ', ')" -ForegroundColor Cyan
Write-Host ""

switch ($Action) {
    "start" {
        # Start services in dependency order
        foreach ($layer in @("database", "api", "app")) {
            $layerServices = $servicesToProcess | Where-Object { $Services[$_].Layer -eq $layer }
            foreach ($serviceName in $layerServices) {
                Start-Service $serviceName
                Start-Sleep -Seconds 2
            }
        }
    }
    
    "stop" {
        # Stop services in reverse dependency order
        foreach ($layer in @("app", "api", "database")) {
            $layerServices = $servicesToProcess | Where-Object { $Services[$_].Layer -eq $layer }
            foreach ($serviceName in $layerServices) {
                Stop-Service $serviceName
            }
        }
    }
    
    "restart" {
        # Stop then start
        foreach ($serviceName in $servicesToProcess) {
            Stop-Service $serviceName
        }
        Start-Sleep -Seconds 5
        foreach ($serviceName in $servicesToProcess) {
            Start-Service $serviceName
        }
    }
    
    "status" {
        foreach ($serviceName in $servicesToProcess) {
            Get-ServiceStatus $serviceName
        }
    }
    
    "health" {
        foreach ($serviceName in $servicesToProcess) {
            Test-ServiceHealth $serviceName
        }
    }
    
    "logs" {
        if ($servicesToProcess.Count -eq 1) {
            Show-ServiceLogs $servicesToProcess[0]
        } else {
            Write-Host "Logs can only be shown for one service at a time" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "=== Operation Complete ===" -ForegroundColor Magenta
