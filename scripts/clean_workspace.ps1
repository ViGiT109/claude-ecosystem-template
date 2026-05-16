#requires -Version 5.1
<#
.SYNOPSIS
    Clean project workspace of cache and generated artifacts.

.DESCRIPTION
    Three cleanup levels:
      safe     — caches and regenerable junk (always safe)
      extended — + worktree venv duplicates, runtime outputs
      deep     — + embedding models, MCP venv (requires confirmation)

    Protection: runs ONLY from the project repository root.
    Never touches .git, main .venv, .memory/*.md|*.jsonl, source code, or docs.

.PARAMETER Level
    safe (default) | extended | deep

.PARAMETER DryRun
    Show what would be deleted without deleting anything.

.PARAMETER Yes
    Skip interactive confirmation for extended/deep levels.

.EXAMPLE
    .\scripts\clean_workspace.ps1
    .\scripts\clean_workspace.ps1 -Level extended -DryRun
    .\scripts\clean_workspace.ps1 -Level deep -Yes
#>
[CmdletBinding()]
param(
    [ValidateSet('safe', 'extended', 'deep')]
    [string]$Level = 'safe',

    [switch]$DryRun,

    [switch]$Yes
)

$ErrorActionPreference = 'Stop'

# ── Guard: must run from project root ────────────────────────────────────────
function Test-ProjectRoot {
    try {
        $top = (& git rev-parse --show-toplevel 2>$null).Trim()
    } catch {
        return $false
    }
    if (-not $top) { return $false }
    $cwd = (Get-Location).Path.TrimEnd('\').Replace('/', '\')
    $top = $top.TrimEnd('\').Replace('/', '\')
    if ($cwd -ne $top) { return $false }
    # Verify by project markers (customize after bootstrap)
    $markers = @('CLAUDE.md', '.memory')
    foreach ($m in $markers) {
        if (-not (Test-Path (Join-Path $top $m))) { return $false }
    }
    return $true
}

if (-not (Test-ProjectRoot)) {
    Write-Host "❌ This script must be run from the project repository root." -ForegroundColor Red
    Write-Host "   Current folder: $((Get-Location).Path)" -ForegroundColor Yellow
    exit 1
}

$RepoRoot = (Get-Location).Path

# ── Utilities ────────────────────────────────────────────────────────────────
function Format-Size {
    param([long]$Bytes)
    if ($Bytes -ge 1GB) { return ('{0:N2} GB' -f ($Bytes / 1GB)) }
    if ($Bytes -ge 1MB) { return ('{0:N1} MB' -f ($Bytes / 1MB)) }
    if ($Bytes -ge 1KB) { return ('{0:N1} KB' -f ($Bytes / 1KB)) }
    return "$Bytes B"
}

function Get-PathSize {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return 0 }
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if ($null -eq $item) { return 0 }
    if ($item.PSIsContainer) {
        $sum = (Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum).Sum
        return [long]($sum ?? 0)
    }
    return [long]$item.Length
}

function Get-RepoSize {
    $sum = (Get-ChildItem -LiteralPath $RepoRoot -Recurse -Force -File -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
    return [long]($sum ?? 0)
}

$script:Targets = New-Object System.Collections.Generic.List[object]

$script:AlwaysJunkNames = @(
    '__pycache__', '.ruff_cache', '.pytest_cache', '.mypy_cache',
    '.ipynb_checkpoints', 'htmlcov', '.turbo'
)
$script:AlwaysJunkExtensions = @(
    '.pyc', '.pyo', '.tmp', '.bak', '.swp', '.swo', '.orig'
)
$script:AlwaysJunkFiles = @(
    'Thumbs.db', '.DS_Store', 'desktop.ini', '.coverage', 'coverage.xml'
)

function Test-AlwaysJunk {
    param([string]$Path)
    $leaf = Split-Path -Leaf $Path
    if ($script:AlwaysJunkNames -contains $leaf) { return $true }
    if ($script:AlwaysJunkFiles -contains $leaf) { return $true }
    $ext = [System.IO.Path]::GetExtension($leaf)
    if ($script:AlwaysJunkExtensions -contains $ext) { return $true }
    return $false
}

function Add-Target {
    param([string]$Path, [string]$Reason)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $rel = (Resolve-Path -LiteralPath $Path).Path

    foreach ($hard in $script:HardProtected) {
        if ($rel -ieq $hard -or $rel.StartsWith("$hard\", [System.StringComparison]::OrdinalIgnoreCase)) {
            return
        }
    }

    $isAlwaysJunk = Test-AlwaysJunk -Path $rel
    if (-not $isAlwaysJunk) {
        foreach ($protected in $script:Protected) {
            if ($rel -ieq $protected -or $rel.StartsWith("$protected\", [System.StringComparison]::OrdinalIgnoreCase)) {
                return
            }
        }
    }

    $script:Targets.Add([pscustomobject]@{
        Path   = $rel
        Reason = $Reason
        Size   = Get-PathSize -Path $rel
    })
}

# ── Always protected (never deleted even inside) ──────────────────────────────
$script:HardProtected = @(
    (Join-Path $RepoRoot '.git'),
    (Join-Path $RepoRoot '.venv'),
    (Join-Path $RepoRoot '.memory\chroma_db')
) | ForEach-Object { $_.TrimEnd('\') }

# ── Soft protected (protected, but always-junk inside is still cleaned) ───────
$script:Protected = @(
    (Join-Path $RepoRoot 'src'),
    (Join-Path $RepoRoot 'tests'),
    (Join-Path $RepoRoot 'docs'),
    (Join-Path $RepoRoot '.agents'),
    (Join-Path $RepoRoot '.claude\commands'),
    (Join-Path $RepoRoot '.claude\skills'),
    (Join-Path $RepoRoot '.claude\hooks'),
    (Join-Path $RepoRoot '.claude\agents'),
    (Join-Path $RepoRoot '.claude\settings.json'),
    (Join-Path $RepoRoot '.memory')
) | ForEach-Object { $_.TrimEnd('\') }

# ── SAFE: caches and .pyc files ──────────────────────────────────────────────
function Collect-Safe {
    Write-Host "→ Scanning safe targets..." -ForegroundColor Cyan
    $dirNames = @('__pycache__', '.ruff_cache', '.pytest_cache', '.mypy_cache',
                  '.ipynb_checkpoints', 'htmlcov', '.turbo', 'node_modules\.cache')
    foreach ($name in $dirNames) {
        Get-ChildItem -LiteralPath $RepoRoot -Recurse -Directory -Force -Filter $name -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notlike "*\.git\*" -and $_.FullName -notlike "*\.venv\*" } |
            ForEach-Object { Add-Target -Path $_.FullName -Reason "cache: $name" }
    }
    $filePatterns = @('*.pyc', '*.pyo', '*.tmp', '*.bak', '*.swp', '*.swo', '*.orig',
                      '.coverage', 'coverage.xml', 'Thumbs.db', '.DS_Store', 'desktop.ini')
    foreach ($pat in $filePatterns) {
        Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -Force -Filter $pat -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notlike "*\.git\*" -and $_.FullName -notlike "*\.venv\*" } |
            ForEach-Object { Add-Target -Path $_.FullName -Reason "file: $pat" }
    }
}

# ── EXTENDED: worktree venv duplicates ───────────────────────────────────────
function Collect-Extended {
    Write-Host "→ Scanning extended targets..." -ForegroundColor Cyan
    $worktreesDir = Join-Path $RepoRoot '.claude\worktrees'
    if (Test-Path $worktreesDir) {
        $gitOutput = & git worktree list --porcelain 2>$null
        $aliveWorktrees = @()
        $prunable = @()
        $currentPath = $null
        foreach ($line in $gitOutput) {
            if ($line -like 'worktree *') {
                $currentPath = ($line -replace '^worktree\s+', '').Trim().Replace('/', '\').TrimEnd('\')
            } elseif ($line -eq 'prunable' -or $line -like 'prunable *') {
                if ($currentPath) { $prunable += $currentPath }
            } elseif ($line -eq '') {
                if ($currentPath) { $aliveWorktrees += $currentPath }
                $currentPath = $null
            }
        }
        if ($currentPath) { $aliveWorktrees += $currentPath }

        foreach ($p in $prunable) {
            if (Test-Path $p) { Add-Target -Path $p -Reason 'worktree: prunable' }
        }
        Get-ChildItem -LiteralPath $worktreesDir -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
            $wt = $_.FullName.TrimEnd('\')
            $isAlive = $aliveWorktrees | Where-Object { $_ -ieq $wt }
            $isPrunable = $prunable | Where-Object { $_ -ieq $wt }
            if (-not $isAlive -and -not $isPrunable) {
                Add-Target -Path $wt -Reason 'worktree: orphan'
            } else {
                $venv = Join-Path $wt '.venv'
                if (Test-Path $venv) { Add-Target -Path $venv -Reason 'worktree: duplicate .venv' }
            }
        }
    }
}

# ── DEEP: embedding models, MCP venv ─────────────────────────────────────────
function Collect-Deep {
    Write-Host "→ Scanning deep targets..." -ForegroundColor Cyan
    $models = Join-Path $RepoRoot '.memory\models'
    if (Test-Path $models) {
        Get-ChildItem -LiteralPath $models -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ne '.gitkeep' } |
            ForEach-Object { Add-Target -Path $_.FullName -Reason 'embedding model (re-downloads on next use)' }
    }
    $mcp = Join-Path $RepoRoot '.mcp_venv'
    if (Test-Path $mcp) {
        Add-Target -Path $mcp -Reason 'MCP venv (re-created by scripts/setup_mcp.ps1)'
    }
}

# ── Run collection ────────────────────────────────────────────────────────────
$sizeBefore = Get-RepoSize
Write-Host ""
Write-Host "═══ Project cleanup — level: $Level ═══" -ForegroundColor Magenta
Write-Host "Current project size: $(Format-Size $sizeBefore)" -ForegroundColor Gray
Write-Host ""

Collect-Safe
if ($Level -in @('extended', 'deep')) { Collect-Extended }
if ($Level -eq 'deep')                 { Collect-Deep }

# ── Summary ──────────────────────────────────────────────────────────────────
$totalSize = ($script:Targets | Measure-Object -Property Size -Sum).Sum ?? 0
$totalCount = $script:Targets.Count

Write-Host ""
Write-Host "─── Cleanup plan ───" -ForegroundColor Cyan

if ($totalCount -eq 0) {
    Write-Host "Nothing to delete. Project is already clean." -ForegroundColor Green
    exit 0
}

$grouped = $script:Targets | Group-Object Reason | Sort-Object { -($_.Group | Measure-Object Size -Sum).Sum }
foreach ($g in $grouped) {
    $gSize = ($g.Group | Measure-Object Size -Sum).Sum
    Write-Host ("  [{0,4}]  {1,10}  — {2}" -f $g.Count, (Format-Size $gSize), $g.Name) -ForegroundColor White
}
Write-Host ""
Write-Host ("TOTAL: {0} objects, {1}" -f $totalCount, (Format-Size $totalSize)) -ForegroundColor Yellow

$topTargets = $script:Targets | Sort-Object Size -Descending | Select-Object -First 10
if ($topTargets.Count -gt 0) {
    Write-Host ""
    Write-Host "Top 10 largest targets:" -ForegroundColor Cyan
    foreach ($t in $topTargets) {
        $rel = $t.Path.Replace($RepoRoot, '').TrimStart('\')
        Write-Host ("  {0,10}  {1}" -f (Format-Size $t.Size), $rel) -ForegroundColor Gray
    }
}

# ── Confirm ──────────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Host ""
    Write-Host "🟡 DryRun: nothing deleted." -ForegroundColor Yellow
    exit 0
}

if ($Level -in @('extended', 'deep') -and -not $Yes) {
    Write-Host ""
    $ans = Read-Host "Confirm deletion? [y/N]"
    if ($ans -ne 'y' -and $ans -ne 'Y') {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# ── Delete ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "→ Deleting..." -ForegroundColor Cyan

if ($Level -in @('extended', 'deep')) {
    & git worktree prune 2>$null | Out-Null
}

$deleted = 0
$failed = 0
foreach ($t in $script:Targets) {
    try {
        if (Test-Path -LiteralPath $t.Path) {
            Remove-Item -LiteralPath $t.Path -Recurse -Force -ErrorAction Stop
            $deleted++
        }
    } catch {
        $failed++
        Write-Host ("  ✗ {0}: {1}" -f $t.Path, $_.Exception.Message) -ForegroundColor Red
    }
}

$sizeAfter = Get-RepoSize
$freed = $sizeBefore - $sizeAfter

Write-Host ""
Write-Host "═══ Done ═══" -ForegroundColor Green
Write-Host ("  Deleted: {0} objects (errors: {1})" -f $deleted, $failed)
Write-Host ("  Project size: {0} → {1}" -f (Format-Size $sizeBefore), (Format-Size $sizeAfter))
Write-Host ("  Freed: {0}" -f (Format-Size $freed)) -ForegroundColor Green
