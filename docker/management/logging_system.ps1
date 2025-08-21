# SWAIF Platform - Enhanced Logging System
# Fixed and simplified logging system

# UTF-8 configuration
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'UTF8'

# Global logging variables
$script:timestamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$script:LogsDir = ".\logs"
$script:MainLogFile = "$($script:LogsDir)\platform_deployment_$($script:timestamp).md"

# Create logs folder if it doesn't exist
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
    
    # Colors by level
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
    
    # Log to main file only if variable is defined
    if ($script:MainLogFile -and (Test-Path (Split-Path $script:MainLogFile))) {
        try {
            Add-Content -Path $script:MainLogFile -Value $logEntry -ErrorAction SilentlyContinue
        } catch {
            # Ignore log write errors
        }
    }
}

function Start-ServiceWithLogging {
    param (
        [string]$ServiceName,
        [string]$ComposeFile,
        [string]$ServiceDir = "."
    )
    
    Write-DetailedLog "Starting service $ServiceName..." "INFO" $ServiceName
    
    try {
        # Create logs folder in service directory if it doesn't exist
        $serviceLogDir = Join-Path $ServiceDir "logs"
        if (-not (Test-Path $serviceLogDir)) {
            New-Item -ItemType Directory -Path $serviceLogDir -Force | Out-Null
        }
        
        # Specific log file for the service
        $serviceLogFile = Join-Path $serviceLogDir "$ServiceName_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').log"
        
        # Execute docker-compose up
        $process = Start-Process -FilePath "docker-compose" -ArgumentList "-f", $ComposeFile, "up", "-d" -NoNewWindow -PassThru -RedirectStandardOutput $serviceLogFile -RedirectStandardError $serviceLogFile
        $process.WaitForExit()
        
        if ($process.ExitCode -eq 0) {
            Write-DetailedLog "Service $ServiceName started successfully" "SUCCESS" $ServiceName
            return $true
        } else {
            Write-DetailedLog "Failed to start service $ServiceName" "ERROR" $ServiceName
            return $false
        }
    } catch {
        Write-DetailedLog "Exception starting service $ServiceName`: $($_.Exception.Message)" "ERROR" $ServiceName
        return $false
    }
}

function Initialize-DeploymentLog {
    Write-DetailedLog "Starting SWAIF platform deployment..." "INFO"
    
    if ($script:MainLogFile) {
        try {
            Add-Content -Path $script:MainLogFile -Value "# SWAIF Platform - Deployment Log`n" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "**Date/Time:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "**Version:** Modular Architecture v3.0`n" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "**Mode:** Deployment with pre-configured verification`n" -ErrorAction SilentlyContinue
        } catch {
            # Ignore log write errors
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
    
    Write-DetailedLog "Deployment finished!" "SUCCESS"
    Write-DetailedLog "Total time: $Duration seconds" "INFO"
    
    if ($script:MainLogFile) {
        try {
            Add-Content -Path $script:MainLogFile -Value "`n## Final Summary`n" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "**Execution time:** $Duration seconds`n" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "**Status:** Complete deployment`n" -ErrorAction SilentlyContinue
            
            # Final container status
            $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            Write-DetailedLog "Active containers:" "INFO"
            Write-Host $containers -ForegroundColor Green
            
            Add-Content -Path $script:MainLogFile -Value "### Active Containers" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "```" -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value $containers -ErrorAction SilentlyContinue
            Add-Content -Path $script:MainLogFile -Value "```" -ErrorAction SilentlyContinue
            
            Write-DetailedLog "Main log saved at: $script:MainLogFile" "INFO"
        } catch {
            # Ignore log write errors
        }
    }
}

# Functions are available when imported with dot-sourcing
# Don't use Export-ModuleMember to avoid module errors
