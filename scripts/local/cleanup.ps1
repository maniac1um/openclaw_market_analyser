# Safe cleanup for OpenClaw News Publisher (Windows PowerShell 5.1+ / 7+).
# Does NOT delete: .git, .env, openclaw-state/, openclaw-portal-state/, backups/, content/reports/
#
# Usage:
#   powershell -File scripts/local/cleanup.ps1                    # dry-run (default)
#   powershell -File scripts/local/cleanup.ps1 -Apply             # perform deletion
#   powershell -File scripts/local/cleanup.ps1 -Apply -Aggressive
#   powershell -File scripts/local/cleanup.ps1 -Apply -LogDays 30

[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$Aggressive,
    [int]$LogDays = 30
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
Set-Location $Root

$DryLabel = if ($Apply) { "[apply]" } else { "[dry-run]" }
$Removed = 0

function Write-Action([string]$Message) {
    Write-Host "$DryLabel $Message"
}

function Remove-SafePath([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    if ($Apply) {
        if (Test-Path -LiteralPath $Path -PathType Container) {
            Remove-Item -LiteralPath $Path -Recurse -Force
        } else {
            Remove-Item -LiteralPath $Path -Force
        }
    }
    Write-Action "remove: $Path"
    $script:Removed++
}

function Remove-OldFile([string]$Path, [int]$Days) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $item = Get-Item -LiteralPath $Path
    $cutoff = (Get-Date).AddDays(-$Days)
    if ($item.LastWriteTime -lt $cutoff) {
        Remove-SafePath $Path
    } else {
        Write-Action "keep (newer than ${Days}d): $Path"
    }
}

# --- Python / test caches ---
@(".pytest_cache", ".mypy_cache", ".ruff_cache", "htmlcov") | ForEach-Object {
    Remove-SafePath (Join-Path $Root $_)
}
Remove-SafePath (Join-Path $Root ".coverage")

Get-ChildItem -Path $Root -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\frontend\\node_modules\\" -and $_.FullName -notmatch "\\\.venv\\" } |
    ForEach-Object { Remove-SafePath $_.FullName }

# --- Skill ephemeral artifacts ---
$SkillsRoot = Join-Path $Root "skills"
if (Test-Path $SkillsRoot) {
    Get-ChildItem -Path $SkillsRoot -Directory | ForEach-Object {
        $skill = $_.FullName
        Remove-SafePath (Join-Path $skill "report_payload.json")
        Remove-SafePath (Join-Path $skill "gold_price_report.json")
        Remove-SafePath (Join-Path $skill "badminton_price_report.json")
        Remove-SafePath (Join-Path $skill ".openclaw")

        $runs = Join-Path $skill "runs"
        if (Test-Path $runs) {
            Get-ChildItem -Path $runs -Force -ErrorAction SilentlyContinue | ForEach-Object {
                Remove-SafePath $_.FullName
            }
            if ($Apply -and (Test-Path $runs)) {
                try {
                    Remove-Item -LiteralPath $runs -Force -ErrorAction Stop
                    Write-Action "remove empty dir: $runs"
                } catch {
                    Write-Action "left in place (not empty): $runs"
                }
            } elseif (Test-Path $runs) {
                Write-Action "remove contents of: $runs\"
            }
        }
    }
}

# --- Temp JSON at repo root ---
Get-ChildItem -Path $Root -File -Filter "tmp_*.json" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-SafePath $_.FullName }

Get-ChildItem -Path $Root -File -Filter ".env.bak.*" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-SafePath $_.FullName }

# --- Expired local server logs ---
$TempLog = Join-Path $env:TEMP "openclaw_news_publisher.server.log"
$TempPid = Join-Path $env:TEMP "openclaw_news_publisher.uvicorn.pid"
Remove-OldFile $TempLog $LogDays
Remove-OldFile $TempPid $LogDays

foreach ($logDir in @(
    (Join-Path $Root "frontend\logs"),
    (Join-Path $Root "logs")
)) {
    if (-not (Test-Path $logDir)) { continue }
    Get-ChildItem -Path $logDir -File -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-OldFile $_.FullName $LogDays
    }
}

# --- Aggressive optional targets ---
if ($Aggressive) {
    Remove-SafePath (Join-Path $Root "frontend\node_modules")
    Remove-SafePath (Join-Path $Root "frontend\dist")
    Remove-SafePath (Join-Path $Root ".venv")
    Get-ChildItem -Path $Root -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-SafePath $_.FullName }
    Remove-SafePath (Join-Path $Root "frontend\android\build")
    Remove-SafePath (Join-Path $Root "frontend\android\.gradle")
}

Write-Host ""
if ($Apply) {
    Write-Host "Done. Applied cleanup ($Removed action(s))."
    if ($Aggressive) {
        Write-Host "Aggressive mode: run 'pip install -e .' and 'cd frontend; npm ci; npm run build' before next deploy."
    }
} else {
    Write-Host "Dry-run complete ($Removed item(s) would be affected)."
    Write-Host "Re-run with: powershell -File scripts/local/cleanup.ps1 -Apply"
}

Write-Host ""
Write-Host "Protected (never touched by this script):"
Write-Host "  .git/  .env  openclaw-state/  openclaw-portal-state/  backups/  content/reports/  PostgreSQL"
