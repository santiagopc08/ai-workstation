#!/bin/bash
set -e

echo "🚀 Bootstrapping ORBIT environment..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "📦 Syncing orbit-core..."
cd orbit-core && uv sync && cd ..

echo "📦 Syncing orbit-execution..."
cd orbit-execution && uv sync && cd ..

echo "📦 Syncing orbit-git..."
cd orbit-git && uv sync && cd ..

echo "📦 Syncing orbit-knowledge..."
cd orbit-knowledge && uv sync && cd ..

echo "📦 Syncing orbit-skills (Orchestrator)..."
cd orbit-skills && uv sync && cd ..

echo "✅ Bootstrap complete! ORBIT is ready to use."
echo "To test your installation, run: ./scripts/dev.sh"
