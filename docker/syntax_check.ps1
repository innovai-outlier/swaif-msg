# PowerShell Syntax Checker
param([string]$FilePath)

$errors = @()
$tokens = @()
$ast = [System.Management.Automation.Language.Parser]::ParseFile($FilePath, [ref]$tokens, [ref]$errors)

if ($errors.Count -gt 0) {
    Write-Host "SYNTAX ERRORS FOUND in $FilePath" -ForegroundColor Red
    Write-Host "================================" -ForegroundColor Red
    foreach ($parseError in $errors) {
        Write-Host "Line $($parseError.Extent.StartLineNumber): $($parseError.Message)" -ForegroundColor Red
    }
    exit 1
} else {
    Write-Host "$FilePath`: Syntax OK" -ForegroundColor Green
    exit 0
}
