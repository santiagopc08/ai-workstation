#!/bin/bash
set -e

echo "🔨 Installing ORBIT globally..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# We install orbit-skills globally, as it is the high-level orchestrator
echo "📦 Installing orbit-skills via uv tool..."
uv tool install ./orbit-skills

echo "✅ Install complete!"
echo "You can now run ORBIT CLI commands if configured in the orchestrator."
