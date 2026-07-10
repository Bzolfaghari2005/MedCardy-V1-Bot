# MedCardy — run psql without PATH (reads password from .env)
# Usage:
#   .\scripts\database\psql.ps1
#   .\scripts\database\psql.ps1 -Database medcardy
#   .\scripts\database\psql.ps1 -File scripts\database\setup_medcardy.sql

param(
    [string]$User = "",
    [string]$Password = "",
    [string]$Database = "",
    [string]$File = "",
    [string]$DbHost = "",
    [int]$Port = 0
)

$projectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$envFile = Join-Path $projectRoot ".env"

function Read-DatabaseUrlFromEnv {
    if (-not (Test-Path $envFile)) { return $null }
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^\s*DATABASE_URL\s*=\s*(.+)\s*$') {
            return $Matches[1].Trim()
        }
    }
    return $null
}

function Parse-DatabaseUrl {
    param([string]$Url)
    if (-not $Url) { return $null }
    $normalized = $Url -replace '^postgresql://', 'postgres://'
    if ($normalized -notmatch '^postgres://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(.+)$') {
        return $null
    }
    return @{
        User = $Matches[1]
        Password = $Matches[2]
        Host = $Matches[3]
        Port = if ($Matches[4]) { [int]$Matches[4] } else { 5432 }
        Database = $Matches[5]
    }
}

$dbFromEnv = Parse-DatabaseUrl (Read-DatabaseUrlFromEnv)

$pgVersions = @("16", "15", "14", "13", "12")
$psqlPath = $null
$pgVersion = $null

foreach ($ver in $pgVersions) {
    $candidate = "C:\Program Files\PostgreSQL\$ver\bin\psql.exe"
    if (Test-Path $candidate) {
        $psqlPath = $candidate
        $pgVersion = $ver
        break
    }
}

if (-not $psqlPath) {
    Write-Error "psql not found. Install: winget install PostgreSQL.PostgreSQL.16"
    exit 1
}

if (-not $User -and $dbFromEnv) { $User = $dbFromEnv.User }
if (-not $Password -and $dbFromEnv) { $Password = $dbFromEnv.Password }
if (-not $DbHost -and $dbFromEnv) { $DbHost = $dbFromEnv.Host }
if ($Port -eq 0 -and $dbFromEnv) { $Port = $dbFromEnv.Port }

if (-not $User) { $User = "postgres" }
if (-not $DbHost) { $DbHost = "127.0.0.1" }

if ($Port -eq 0) {
    $confPath = "C:\Program Files\PostgreSQL\$pgVersion\data\postgresql.conf"
    $Port = 5432
    if (Test-Path $confPath) {
        $portLine = Select-String -Path $confPath -Pattern '^\s*port\s*=\s*(\d+)' | Select-Object -First 1
        if ($portLine) {
            $Port = [int]$portLine.Matches[0].Groups[1].Value
        }
    }
}

if ($Password) {
    $env:PGPASSWORD = $Password
}

$psqlArgs = @("-U", $User, "-h", $DbHost, "-p", $Port)
if ($Database) {
    $psqlArgs += @("-d", $Database)
} elseif ($dbFromEnv -and $dbFromEnv.Database) {
    $psqlArgs += @("-d", $dbFromEnv.Database)
}
if ($File) { $psqlArgs += @("-f", $File) }

Write-Host "Using: $psqlPath (port $Port, user $User)" -ForegroundColor Cyan
& $psqlPath @psqlArgs
