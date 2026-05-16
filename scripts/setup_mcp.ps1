# scripts/setup_mcp.ps1
# Installs MCP servers for this project.
# Node.js MCP servers (sequential-thinking, github) are auto-installed via npx on first use —
# no manual action needed for them.
#
# Requirements: Python 3.11+, Node.js LTS.
#
# Run from the project root:
#   .\scripts\setup_mcp.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

# ── 1. Verify Node.js is available (required for sequential-thinking and github MCP) ──
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Warning "Node.js not found. Install Node.js LTS from https://nodejs.org/ — required for sequential-thinking and github MCP."
} else {
    Write-Host "==> Node.js: $(& node --version)"
}

# ── 2. Verify Python is available ──
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Warning "Python not found in PATH. Install Python 3.11+ from https://www.python.org/"
} else {
    Write-Host "==> Python: $(& python --version)"
}

# ── 3. Check .env file ──
$EnvFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Warning ".env file not found. Copy .env.example to .env and fill in GITHUB_PERSONAL_ACCESS_TOKEN (required for github MCP)."
} else {
    $pat = Select-String -Path $EnvFile -Pattern "GITHUB_PERSONAL_ACCESS_TOKEN=.+" -Quiet
    if (-not $pat) {
        Write-Warning "GITHUB_PERSONAL_ACCESS_TOKEN not set in .env — github MCP will not authenticate."
    } else {
        Write-Host "==> .env: GITHUB_PERSONAL_ACCESS_TOKEN found"
    }
}

# ── 4. Add project-specific Python MCP servers here if needed ──
# Example: create a .mcp_venv and install a Python MCP package
# $VenvPath = Join-Path $ProjectRoot ".mcp_venv"
# if (-not (Test-Path $VenvPath)) {
#     Write-Host "==> Creating .mcp_venv..."
#     & python -m venv $VenvPath
# }
# $VenvPython = Join-Path $VenvPath "Scripts\python.exe"
# & $VenvPython -m pip install --quiet your-mcp-package

Write-Host ""
Write-Host "✅ MCP setup complete."
Write-Host "   Node.js MCP servers (sequential-thinking, github) will auto-install on first use via npx."
Write-Host "   Restart Claude Code and run /mcp to verify both servers appear green."
