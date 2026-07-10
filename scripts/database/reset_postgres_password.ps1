# Reset postgres password when forgotten (Windows)
# Run PowerShell as Administrator:
#   cd "C:\Users\Benyamin\Desktop\MedCardy Bot V1"
#   .\scripts\database\reset_postgres_password.ps1

param(
    [string]$NewPassword = "postgres",
    [string]$PgVersion = "16",
    [string]$PgUser = "postgres"
)

$ErrorActionPreference = "Stop"

function Test-IsAdmin {
    $current = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    return $current.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) {
    Write-Host ""
    Write-Host "Run PowerShell as Administrator, then run this script again." -ForegroundColor Red
    exit 1
}

$pgBin = "C:\Program Files\PostgreSQL\$PgVersion\bin"
$pgData = "C:\Program Files\PostgreSQL\$PgVersion\data"
$pgHba = Join-Path $pgData "pg_hba.conf"
$pgConf = Join-Path $pgData "postgresql.conf"
$psql = Join-Path $pgBin "psql.exe"
$serviceName = "postgresql-x64-$PgVersion"

if (-not (Test-Path $psql)) { throw "psql not found: $psql" }
if (-not (Test-Path $pgHba)) { throw "pg_hba.conf not found: $pgHba" }

$port = 5432
if (Test-Path $pgConf) {
    $portLine = Select-String -Path $pgConf -Pattern '^\s*port\s*=\s*(\d+)' | Select-Object -First 1
    if ($portLine) { $port = [int]$portLine.Matches[0].Groups[1].Value }
}

$backup = "$pgHba.backup-medcardy-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $pgHba $backup -Force
Write-Host "Backup: $backup" -ForegroundColor Cyan
Write-Host "PostgreSQL $PgVersion on port $port" -ForegroundColor Cyan

$content = Get-Content $pgHba -Raw
$patched = $content -replace 'scram-sha-256', 'trust'
Set-Content -Path $pgHba -Value $patched -NoNewline

try {
    Write-Host "Restarting $serviceName ..." -ForegroundColor Cyan
    Restart-Service $serviceName -Force
    Start-Sleep -Seconds 2

    $sql = "ALTER USER $PgUser WITH PASSWORD '$NewPassword';"
    & $psql -U $PgUser -h 127.0.0.1 -p $port -d postgres -c $sql | Out-Host

    Write-Host ""
    Write-Host "Password updated." -ForegroundColor Green
    Write-Host "DATABASE_URL=postgres://${PgUser}:${NewPassword}@localhost:${port}/medcardy" -ForegroundColor Green
}
finally {
    Write-Host "Restoring pg_hba.conf ..." -ForegroundColor Cyan
    Copy-Item $backup $pgHba -Force
    Restart-Service $serviceName -Force
}

Write-Host ""
Write-Host "Done. Connect with:" -ForegroundColor Green
Write-Host "  .\scripts\database\psql.ps1 -User postgres -Database postgres" -ForegroundColor White
