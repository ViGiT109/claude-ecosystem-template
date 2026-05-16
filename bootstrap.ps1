#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Personalize claude-ecosystem-template for a new project.

.DESCRIPTION
    Prompts for project metadata, substitutes placeholders across template files,
    initializes git, and optionally installs MCP servers.
    Run once from the project root after copying the template.

    Safe to re-run: detects already-substituted markers and asks before overwriting.
#>

$ErrorActionPreference = 'Stop'

$ProjectRoot = $PSScriptRoot

# ── Detect re-run ─────────────────────────────────────────────────────────────
$alreadyBootstrapped = $false
$claudeMd = Join-Path $ProjectRoot 'CLAUDE.md'
if (Test-Path $claudeMd) {
    $content = Get-Content $claudeMd -Raw
    if (-not $content.Contains('${PROJECT_NAME}')) {
        $alreadyBootstrapped = $true
    }
}

if ($alreadyBootstrapped) {
    $ans = Read-Host "⚠️  bootstrap.ps1 appears to have already run (no placeholders found). Re-run anyway? [y/N]"
    if ($ans -ne 'y' -and $ans -ne 'Y') {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "═══ claude-ecosystem-template bootstrap ═══" -ForegroundColor Magenta
Write-Host "This script personalizes the template for your new project."
Write-Host "Press Ctrl+C to abort at any time."
Write-Host ""

# ── Collect inputs ────────────────────────────────────────────────────────────
$ProjectName = Read-Host "Project name (e.g. my-app, yandex-direct-bot)"
if ([string]::IsNullOrWhiteSpace($ProjectName)) {
    Write-Error "Project name cannot be empty."
    exit 1
}

$ProjectVision = Read-Host "One-sentence project vision (what problem does it solve?)"
if ([string]::IsNullOrWhiteSpace($ProjectVision)) {
    $ProjectVision = "A new project."
}

$Stakeholders = Read-Host "Primary stakeholders / users (e.g. 'solo developer, internal team')"
if ([string]::IsNullOrWhiteSpace($Stakeholders)) {
    $Stakeholders = "Development team"
}

Write-Host ""
Write-Host "Language / stack:"
Write-Host "  1 = Python"
Write-Host "  2 = Node.js"
Write-Host "  3 = Both (Python + Node)"
Write-Host "  4 = Other"
$langChoice = Read-Host "Choose (1-4)"
$Language = switch ($langChoice) {
    '1' { 'python' }
    '2' { 'node' }
    '3' { 'both' }
    '4' { 'other' }
    default { 'other' }
}

$EntryModule = Read-Host "Entry point (e.g. main.py, src/index.ts, app.js) — leave blank to skip"
$BuildCommand = Read-Host "Build/run command (e.g. 'python main.py', 'npm start') — leave blank to skip"

$ScopesRaw = Read-Host "Conventional Commit scopes, comma-separated [core,api,ui,config,docs,infra]"
if ([string]::IsNullOrWhiteSpace($ScopesRaw)) {
    $ScopesRaw = "core,api,ui,config,docs,infra"
}
$Scopes = ($ScopesRaw -split ',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
$ScopesTomlArray = '["' + ($Scopes -join '", "') + '"]'
$ScopesDisplay = $Scopes -join ', '

Write-Host ""
Write-Host "─── Summary ───" -ForegroundColor Cyan
Write-Host "  Project name : $ProjectName"
Write-Host "  Vision       : $ProjectVision"
Write-Host "  Stakeholders : $Stakeholders"
Write-Host "  Language     : $Language"
Write-Host "  Entry point  : $(if ($EntryModule) { $EntryModule } else { '(none)' })"
Write-Host "  Build command: $(if ($BuildCommand) { $BuildCommand } else { '(none)' })"
Write-Host "  Git scopes   : $ScopesDisplay"
Write-Host ""
$confirm = Read-Host "Proceed? [Y/n]"
if ($confirm -eq 'n' -or $confirm -eq 'N') {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

# ── Write .ecosystem.toml ────────────────────────────────────────────────────
Write-Host ""
Write-Host "→ Writing .ecosystem.toml..." -ForegroundColor Cyan

$packageManager = ''
if ($Language -in ('python', 'both')) {
    $pm = Read-Host "Python package manager (uv / pip / poetry) [uv]"
    if ([string]::IsNullOrWhiteSpace($pm)) { $pm = 'uv' }
    $packageManager = $pm
}

$nodePm = ''
if ($Language -in ('node', 'both')) {
    $npm = Read-Host "Node package manager (npm / pnpm / yarn) [npm]"
    if ([string]::IsNullOrWhiteSpace($npm)) { $npm = 'npm' }
    $nodePm = $npm
}

$tomlContent = @"
[project]
name = "$ProjectName"
language = "$Language"
entry_module = "$EntryModule"
build_command = "$BuildCommand"

[project.python]
backend_modules = []
min_version = "3.11"
package_manager = "$packageManager"

[project.node]
package_manager = "$nodePm"

[git]
main_branch = "main"
scopes = $ScopesTomlArray

[mcp]
servers = ["sequential-thinking", "github"]
"@
Set-Content -Path (Join-Path $ProjectRoot '.ecosystem.toml') -Value $tomlContent -Encoding utf8

# ── Substitute placeholders in template files ─────────────────────────────────
Write-Host "→ Substituting placeholders..." -ForegroundColor Cyan

$filesToUpdate = @(
    'CLAUDE.md',
    'README.md',
    'ROADMAP.md',
    'BUGS.md',
    'ENVIRONMENT_SETUP.md',
    'task.md',
    '.memory\projectbrief.md',
    '.memory\techContext.md',
    '.agents\rules\git.md'
)

$replacements = @{
    '${PROJECT_NAME}'   = $ProjectName
    '${PROJECT_VISION}' = $ProjectVision
    '${STAKEHOLDERS}'   = $Stakeholders
    '${PROJECT_SCOPES}' = $ScopesDisplay
    '${TASK_NAME}'      = 'Initial setup'
}

foreach ($file in $filesToUpdate) {
    $fullPath = Join-Path $ProjectRoot $file
    if (-not (Test-Path $fullPath)) { continue }
    $text = Get-Content $fullPath -Raw -Encoding utf8
    foreach ($kv in $replacements.GetEnumerator()) {
        $text = $text.Replace($kv.Key, $kv.Value)
    }
    Set-Content -Path $fullPath -Value $text -Encoding utf8
    Write-Host "   ✅ $file"
}

# ── Copy .env.example → .env ──────────────────────────────────────────────────
$envSrc = Join-Path $ProjectRoot '.env.example'
$envDst = Join-Path $ProjectRoot '.env'
if ((Test-Path $envSrc) -and -not (Test-Path $envDst)) {
    Copy-Item $envSrc $envDst
    Write-Host "→ Created .env from .env.example — fill in GITHUB_PERSONAL_ACCESS_TOKEN" -ForegroundColor Yellow
}

# ── Optional: scaffold pyproject.toml ────────────────────────────────────────
if ($Language -in ('python', 'both') -and -not (Test-Path (Join-Path $ProjectRoot 'pyproject.toml'))) {
    $scaffold = Read-Host "Scaffold pyproject.toml? [Y/n]"
    if ($scaffold -ne 'n' -and $scaffold -ne 'N') {
        $pyprojectContent = @"
[project]
name = "$ProjectName"
version = "0.1.0"
description = "$ProjectVision"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "ANN", "T20"]
ignore = ["ANN101", "ANN102"]

[tool.pytest.ini_options]
testpaths = ["tests"]
"@
        Set-Content -Path (Join-Path $ProjectRoot 'pyproject.toml') -Value $pyprojectContent -Encoding utf8
        Write-Host "→ Created pyproject.toml" -ForegroundColor Green
    }
}

# ── Optional: scaffold package.json ──────────────────────────────────────────
if ($Language -in ('node', 'both') -and -not (Test-Path (Join-Path $ProjectRoot 'package.json'))) {
    $scaffold = Read-Host "Scaffold package.json? [Y/n]"
    if ($scaffold -ne 'n' -and $scaffold -ne 'N') {
        $pkgContent = @"
{
  "name": "$($ProjectName.ToLower())",
  "version": "0.1.0",
  "description": "$ProjectVision",
  "scripts": {
    "start": "node $EntryModule",
    "test": "echo \"No tests configured\"",
    "lint": "echo \"No linter configured\""
  }
}
"@
        Set-Content -Path (Join-Path $ProjectRoot 'package.json') -Value $pkgContent -Encoding utf8
        Write-Host "→ Created package.json" -ForegroundColor Green
    }
}

# ── Git init ──────────────────────────────────────────────────────────────────
$gitDir = Join-Path $ProjectRoot '.git'
if (-not (Test-Path $gitDir)) {
    Write-Host "→ Initializing git repository..." -ForegroundColor Cyan
    & git -C $ProjectRoot init
    & git -C $ProjectRoot add -A
    & git -C $ProjectRoot commit -m "chore: initialize from claude-ecosystem-template"
    Write-Host "   ✅ Git repository initialized"
} else {
    Write-Host "→ Git repository already exists — skipping git init"
}

# ── Remove template-only files ────────────────────────────────────────────────
$toRemove = @('TEMPLATE_README.md', 'bootstrap.ps1')
foreach ($f in $toRemove) {
    $p = Join-Path $ProjectRoot $f
    if (Test-Path $p) {
        Remove-Item $p -Force
        Write-Host "→ Removed $f (job done)" -ForegroundColor Gray
    }
}

# ── Optional: MCP setup ───────────────────────────────────────────────────────
Write-Host ""
$mcp = Read-Host "Run .\scripts\setup_mcp.ps1 now? [Y/n]"
if ($mcp -ne 'n' -and $mcp -ne 'N') {
    & (Join-Path $ProjectRoot 'scripts\setup_mcp.ps1')
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "═══ Bootstrap complete ═══" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Fill in .env  (GITHUB_PERSONAL_ACCESS_TOKEN)"
Write-Host "  2. Open Claude Code in this folder"
Write-Host "  3. Run /new_session to load the ecosystem context"
Write-Host "  4. Run /setup_environment for guided environment setup"
Write-Host "  5. Fill .memory/projectbrief.md and .memory/techContext.md"
Write-Host ""
