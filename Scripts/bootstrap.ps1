# ORBIT Bootstrap Script for Windows

Write-Host "🚀 Bootstrapping ORBIT environment..." -ForegroundColor Cyan

# Check for uv
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ uv is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "irm https://astral.sh/uv/install.ps1 | iex" -ForegroundColor Yellow
    exit 1
}

$packages = @("orbit-core", "orbit-execution", "orbit-git", "orbit-knowledge", "orbit-skills")

foreach ($pkg in $packages) {
    Write-Host "📦 Syncing $pkg..." -ForegroundColor Cyan
    Set-Location $pkg
    uv sync
    Set-Location ..
}

Write-Host "✅ Bootstrap complete! ORBIT is ready to use." -ForegroundColor Green
Write-Host "To test your installation, run dev scripts inside each folder." -ForegroundColor Yellow
