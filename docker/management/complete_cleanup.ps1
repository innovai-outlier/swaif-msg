# SWAIF Platform - Complete Cleanup
# Removes all containers, networks, and volumes for SWAIF services

param(
    [Parameter(Mandatory=$false)]
    [switch]$Confirm
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'UTF8'

function Write-Header {
    Write-Host ""
    Write-Host "===============================================================================" -ForegroundColor DarkRed
    Write-Host "                     SWAIF PLATFORM - COMPLETE CLEANUP                       " -ForegroundColor DarkRed
    Write-Host "===============================================================================" -ForegroundColor DarkRed
    Write-Host ""
}

if (-not $Confirm) {
    Write-Header
    Write-Host "⚠️  WARNING: This script will remove ALL SWAIF artifacts!" -ForegroundColor Red
    Write-Host "   This will result in permanent loss of all stored data." -ForegroundColor Red
    Write-Host ""
    Write-Host "Artifacts that will be removed:" -ForegroundColor Yellow
    Write-Host "• All SWAIF containers (evoapi, n8n, postgres, redis)" -ForegroundColor White
    Write-Host "• All Docker networks created by services" -ForegroundColor White
    Write-Host "• All volumes (PostgreSQL, Redis, N8N data, etc.)" -ForegroundColor White
    Write-Host "• Unused images" -ForegroundColor White
    Write-Host ""
    
    $response = Read-Host "Are you sure you want to continue? Type 'CONFIRM' to proceed"
    
    if ($response -ne "CONFIRM") {
        Write-Host "Operation cancelled by user." -ForegroundColor Yellow
        exit 0
    }
}

Write-Header

Write-Host "🧹 Starting complete SWAIF platform cleanup..." -ForegroundColor Cyan
Write-Host ""

$originalLocation = Get-Location

# Stop and remove N8N services
Write-Host ">> Stopping and removing N8N services..." -ForegroundColor Yellow
try {
    Set-Location ".\n8n"
    docker compose down -v --remove-orphans 2>$null
    Write-Host "   ✓ N8N services removed" -ForegroundColor Green
} catch {
    Write-Host "   ! Error removing N8N: $_" -ForegroundColor Yellow
}

Set-Location $originalLocation

# Stop and remove Evolution API services
Write-Host ">> Stopping and removing Evolution API services..." -ForegroundColor Yellow
try {
    Set-Location ".\evoapi"
    docker compose down -v --remove-orphans 2>$null
    Write-Host "   ✓ Evolution API services removed" -ForegroundColor Green
} catch {
    Write-Host "   ! Error removing Evolution API: $_" -ForegroundColor Yellow
}

Set-Location $originalLocation

# General Docker cleanup
Write-Host ""
Write-Host ">> Running general Docker cleanup..." -ForegroundColor Yellow
try {
    # Remove stopped containers
    $containers = docker ps -aq 2>$null
    if ($containers) {
        docker rm $containers 2>$null
        Write-Host "   ✓ Containers removed" -ForegroundColor Green
    }
    
    # Remove unused volumes
    docker volume prune -f 2>$null
    Write-Host "   ✓ Unused volumes removed" -ForegroundColor Green
    
    # Remove unused networks
    docker network prune -f 2>$null
    Write-Host "   ✓ Unused networks removed" -ForegroundColor Green
    
    # Remove unused images
    docker image prune -f 2>$null
    Write-Host "   ✓ Unused images removed" -ForegroundColor Green
    
} catch {
    Write-Host "   ! Error in general cleanup: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ COMPLETE CLEANUP FINISHED" -ForegroundColor Green
Write-Host "   All SWAIF artifacts have been removed." -ForegroundColor Green
Write-Host "   System ready for fresh installation." -ForegroundColor Cyan
Write-Host ""
Write-Host "To start a clean installation:" -ForegroundColor Cyan
Write-Host "   .\management\start_all.ps1" -ForegroundColor White
