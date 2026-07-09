#!/bin/bash
set -e

echo "🛠️  Running ORBIT Development Checks..."

PACKAGES=("orbit-core" "orbit-execution" "orbit-git" "orbit-knowledge" "orbit-skills")

for pkg in "${PACKAGES[@]}"; do
    echo "=========================================="
    echo "🔍 Checking $pkg"
    echo "=========================================="
    cd "$pkg"
    
    echo "1️⃣  Running ruff..."
    uv run ruff check src/ tests/
    
    echo "2️⃣  Running mypy..."
    # orbit-core has its source differently, fallback gracefully if paths differ slightly
    if [ -d "src/$pkg" ]; then
        uv run mypy src/$pkg/
    else
        uv run mypy src/
    fi
    
    echo "3️⃣  Running pytest..."
    uv run pytest tests/ -v
    
    cd ..
    echo "✅ $pkg passed!"
    echo ""
done

echo "🎉 All ORBIT packages passed developer checks!"
