# SWAIF Platform - Pre-deployment Check and Cleanup
# Checks and cleans existing artifacts before starting the stack

param(
    [Parameter(Mandatory=$false)]
    [switch]$Force,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBackup
)

# Configuration of SWAIF artifacts
$SwaifContainers = @(
    "postgres_swaif",
    "redis_swaif", 
    "evolution_api_swaif",
    "n8n_production",
    "swaif_streamlit_app"
)

$SwaifNetworks = @(
    "swaif_network",
    "postgres_swaif_network",
    "redis_swaif_network",
    "evolution_swaif_network",
    "n8n_swaif_network",
    "swaif_app_swaif_network"
)

$SwaifVolumes = @(
    "swaif_postgres_data",
    "swaif_redis_data",
    "swaif_n8n_data",
    "swaif_evolution_instances",
    "swaif_evolution_store",
    "swaif_app_logs",
    "postgres_data",
    "redis_data",
    "n8n_data",
    "evolution_instances",
    "evolution_store"
)

function Write-CheckStatus {
    param($Item, $Status, $Message)
    $timestamp = Get-Date -Format "HH:mm:ss"
    $color = switch ($Status) {
        "FOUND" { "Yellow" }
        "REMOVED" { "Green" }
        "ERROR" { "Red" }
        "INFO" { "Cyan" }
        "CLEAN" { "Green" }
        default { "White" }
    }
    Write-Host "[$timestamp] " -NoNewline
    Write-Host "[$Status] " -ForegroundColor $color -NoNewline
    Write-Host "$Item - $Message"
}

function Test-ContainerExists {
    param($ContainerName)
    $container = docker ps -a -q -f name="^${ContainerName}$"
    return ($container -ne $null -and $container.Trim() -ne "")
}

function Test-NetworkExists {
    param($NetworkName)
    $network = docker network ls -q -f name="^${NetworkName}$"
    return ($network -ne $null -and $network.Trim() -ne "")
}

function Test-VolumeExists {
    param($VolumeName)
    $volume = docker volume ls -q -f name="^${VolumeName}$"
    return ($volume -ne $null -and $volume.Trim() -ne "")
}

function Remove-SwaifContainer {
    param($ContainerName)
    
    if (Test-ContainerExists $ContainerName) {
        Write-CheckStatus $ContainerName "FOUND" "Container exists, checking status..."
        
        # Verificar se está rodando
        $running = docker ps -q -f name="^${ContainerName}$"
        if ($running) {
            Write-CheckStatus $ContainerName "INFO" "Stopping running container..."
            docker stop $ContainerName | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-CheckStatus $ContainerName "INFO" "Container stopped successfully"
            }
        }
        
        # Remover container
        Write-CheckStatus $ContainerName "INFO" "Removing container..."
        docker rm $ContainerName | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-CheckStatus $ContainerName "REMOVED" "Container removed successfully"
        } else {
            Write-CheckStatus $ContainerName "ERROR" "Failed to remove container"
        }
    } else {
        Write-CheckStatus $ContainerName "CLEAN" "No existing container found"
    }
}

function Remove-SwaifNetwork {
    param($NetworkName)
    
    if (Test-NetworkExists $NetworkName) {
        Write-CheckStatus $NetworkName "FOUND" "Network exists, removing..."
        docker network rm $NetworkName | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-CheckStatus $NetworkName "REMOVED" "Network removed successfully"
        } else {
            Write-CheckStatus $NetworkName "ERROR" "Failed to remove network (may be in use)"
        }
    } else {
        Write-CheckStatus $NetworkName "CLEAN" "No existing network found"
    }
}

function Backup-SwaifVolume {
    param($VolumeName)
    
    if (-not $SkipBackup -and (Test-VolumeExists $VolumeName)) {
        $backupDir = ".\backups\pre-deployment\$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"
        if (-not (Test-Path $backupDir)) {
            New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        }
        
        Write-CheckStatus $VolumeName "INFO" "Creating backup..."
        $backupFile = "$backupDir\${VolumeName}_backup.tar.gz"
        
        docker run --rm -v "${VolumeName}:/data" -v "${PWD}/backups:/backup" alpine tar czf "/backup/pre-deployment/$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')/${VolumeName}_backup.tar.gz" -C /data . 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-CheckStatus $VolumeName "INFO" "Backup created: $backupFile"
        } else {
            Write-CheckStatus $VolumeName "ERROR" "Backup failed"
        }
    }
}

function Remove-SwaifVolume {
    param($VolumeName)
    
    if (Test-VolumeExists $VolumeName) {
        Write-CheckStatus $VolumeName "FOUND" "Volume exists"
        
        # Fazer backup se solicitado
        if (-not $SkipBackup) {
            Backup-SwaifVolume $VolumeName
        }
        
        # Remover volume
        if ($Force) {
            Write-CheckStatus $VolumeName "INFO" "Removing volume (forced)..."
            docker volume rm $VolumeName | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-CheckStatus $VolumeName "REMOVED" "Volume removed successfully"
            } else {
                Write-CheckStatus $VolumeName "ERROR" "Failed to remove volume"
            }
        } else {
            Write-CheckStatus $VolumeName "INFO" "Volume preserved (use -Force to remove)"
        }
    } else {
        Write-CheckStatus $VolumeName "CLEAN" "No existing volume found"
    }
}

# Início do processo de limpeza
Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                      SWAIF PRE-DEPLOYMENT CLEANUP                           ║" -ForegroundColor Cyan
Write-Host "║                     $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')                        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($Force) {
    Write-Host "⚠️  FORCE MODE ENABLED - Volumes will be removed!" -ForegroundColor Red
}
if ($SkipBackup) {
    Write-Host "⚠️  BACKUP SKIPPED - No backups will be created!" -ForegroundColor Yellow
}
Write-Host ""

# 1. Verificar e parar containers
Write-Host "╔════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor White
Write-Host "║ CONTAINER CLEANUP                                                          ║" -ForegroundColor White
Write-Host "╚════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor White

foreach ($container in $SwaifContainers) {
    Remove-SwaifContainer $container
}

Write-Host ""

# 2. Verificar e remover redes
Write-Host "╔════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor White
Write-Host "║ NETWORK CLEANUP                                                            ║" -ForegroundColor White
Write-Host "╚════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor White

foreach ($network in $SwaifNetworks) {
    Remove-SwaifNetwork $network
}

Write-Host ""

# 3. Verificar volumes
Write-Host "╔════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor White
Write-Host "║ VOLUME CLEANUP                                                             ║" -ForegroundColor White
Write-Host "╚════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor White

# Criar diretório de backup se necessário
if (-not $SkipBackup -and -not (Test-Path ".\backups")) {
    New-Item -ItemType Directory -Path ".\backups" -Force | Out-Null
    Write-CheckStatus "Backup" "INFO" "Created backup directory"
}

foreach ($volume in $SwaifVolumes) {
    Remove-SwaifVolume $volume
}

Write-Host ""

# 4. Limpeza geral do Docker
Write-Host "╔════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor White
Write-Host "║ DOCKER SYSTEM CLEANUP                                                     ║" -ForegroundColor White
Write-Host "╚════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor White

Write-CheckStatus "Docker" "INFO" "Removing unused containers..."
docker container prune -f | Out-Null

Write-CheckStatus "Docker" "INFO" "Removing unused networks..."
docker network prune -f | Out-Null

Write-CheckStatus "Docker" "INFO" "Removing unused images..."
docker image prune -f | Out-Null

Write-Host ""

# 5. Verificação final
Write-Host "╔════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║ FINAL VERIFICATION                                                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green

$remainingContainers = 0
$remainingNetworks = 0
$remainingVolumes = 0

foreach ($container in $SwaifContainers) {
    if (Test-ContainerExists $container) {
        Write-CheckStatus $container "ERROR" "Container still exists!"
        $remainingContainers++
    }
}

foreach ($network in $SwaifNetworks) {
    if (Test-NetworkExists $network) {
        Write-CheckStatus $network "ERROR" "Network still exists!"
        $remainingNetworks++
    }
}

foreach ($volume in $SwaifVolumes) {
    if (Test-VolumeExists $volume) {
        if ($Force) {
            Write-CheckStatus $volume "ERROR" "Volume still exists!"
            $remainingVolumes++
        } else {
            Write-CheckStatus $volume "INFO" "Volume preserved"
        }
    }
}

Write-Host ""

# Resumo final
if ($remainingContainers -eq 0 -and $remainingNetworks -eq 0 -and ($Force -and $remainingVolumes -eq 0 -or -not $Force)) {
    Write-Host "✅ PRE-DEPLOYMENT CLEANUP COMPLETED SUCCESSFULLY" -ForegroundColor Green
    Write-Host "   Ready for fresh deployment!" -ForegroundColor Green
} else {
    Write-Host "⚠️  CLEANUP COMPLETED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "   Some artifacts may still exist. Check logs above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run: .\management\start_all.ps1" -ForegroundColor White
Write-Host "2. Monitor: .\management\monitor_services.ps1" -ForegroundColor White
