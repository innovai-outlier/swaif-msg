# SWAIF Platform - Enhanced Logging System
# Sistema de logs corrigido e simplificado

# Configuração UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'UTF8'

# Variáveis globais de logging
$script:timestamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$script:LogsDir = ".\logs"
$script:MainLogFile = "$($script:LogsDir)\platform_deployment_$($script:timestamp).md"

# Criar pasta logs se não existir
if (-not (Test-Path $script:LogsDir)) {
    New-Item -ItemType Directory -Path $script:LogsDir -Force | Out-Null
}

function Write-DetailedLog {
    param(
        [string]$Message, 
        [string]$Level = "INFO",
        [string]$Service = "PLATFORM"
    )
    
    $logTimestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$logTimestamp] [$Level] [$Service] $Message"
    
    # Cores por nível
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        "INFO" { "Cyan" }
        "DEBUG" { "Gray" }
        "HEADER" { "Magenta" }
        default { "White" }
    }
    
    Write-Host $logEntry -ForegroundColor $color
    
    # Log no arquivo principal apenas se a variável estiver definida
    if ($script:MainLogFile -and (Test-Path (Split-Path $script:MainLogFile))) {
        try {
            Add-Content -Path $script:MainLogFile -Value $logEntry -ErrorAction SilentlyContinue
        } catch {
            # Ignorar erros de escrita no log
        }
    }
}

function Start-ServiceWithLogging {
    param (
        [string]$ServiceName,
        [string]$ComposeFile,
        [string]$ServiceDir = "."
    )
    
    Write-DetailedLog "Iniciando serviço $ServiceName..." "INFO" $ServiceName
    
    try {
        # Criar pasta logs no diretório do serviço se não existir
        $serviceLogDir = Join-Path $ServiceDir "logs"
        if (-not (Test-Path $serviceLogDir)) {
            New-Item -ItemType Directory -Path $serviceLogDir -Force | Out-Null
        }
        
        # Arquivo de log específico para o serviço
        $serviceLogFile = Join-Path $serviceLogDir "$ServiceName_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').log"
        
        # Executar docker-compose up
        $process = Start-Process -FilePath "docker-compose" -ArgumentList "-f", $ComposeFile, "up", "-d" -NoNewWindow -PassThru -RedirectStandardOutput $serviceLogFile -RedirectStandardError $serviceLogFile
        $process.WaitForExit()
        
        if ($process.ExitCode -eq 0) {
            Write-DetailedLog "Serviço $ServiceName iniciado com sucesso" "SUCCESS" $ServiceName
            return $true
        } else {
            Write-DetailedLog "Falha ao iniciar serviço $ServiceName" "ERROR" $ServiceName
            return $false
        }
    } catch {
        Write-DetailedLog "Exceção ao iniciar serviço $ServiceName`: $($_.Exception.Message)" "ERROR" $ServiceName
        return $false
    }
}

function Initialize-DeploymentLog {
    Write-DetailedLog "Iniciando deployment da plataforma SWAIF..." "INFO"
    
    if ($script:MainLogFile) {
        try {
            Add-Content -Path $script:MainLogFile -Value "# SWAIF Platform - Deployment Log`n" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "**Data/Hora:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "**Versao:** Modular Architecture v3.0`n" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "**Modo:** Deployment com verificacao pre-configurada`n" -ErrorAction SilentlyContinue
        } catch {
            # Ignorar erros de escrita no log
        }
    }
}

function Finalize-DeploymentLog {
    param([DateTime]$StartTime = (Get-Date))
    
    $EndTime = Get-Date
    try {
        $Duration = ($EndTime - $StartTime).TotalSeconds
    } catch {
        $Duration = 0
    }
    
    Write-DetailedLog "Deployment finalizado!" "SUCCESS"
    Write-DetailedLog "Tempo total: $Duration segundos" "INFO"
    
    if ($script:MainLogFile) {
        try {
            Add-Content -Path $script:MainLogFile -Value "`n## Resumo Final`n" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "**Tempo de execucao:** $Duration segundos`n" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "**Status:** Deployment completo`n" -ErrorAction SilentlyContinue
            
            # Status final dos containers
            $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            Write-DetailedLog "Containers ativos:" "INFO"
            Write-Host $containers -ForegroundColor Green
            
            Add-Content -Path $script:MainLogFile -Value "### Containers Ativos" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "```" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value $containers -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "```" -ErrorAction SilentlyContinue
            
            Write-DetailedLog "Log principal salvo em: $script:MainLogFile" "INFO"
        } catch {
            # Ignorar erros de escrita no log
        }
    }
}

# Funcoes estao disponiveis quando importado com dot-sourcing
# Nao usar Export-ModuleMember para evitar erros de modulo
