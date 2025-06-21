#!/bin/bash
# AetherPost Deployment Script
# Generated for local backend with starter template

set -e

echo "🚀 Deploying AetherPost..."

# Check requirements
if ! command -v aetherpost &> /dev/null; then
    echo "❌ AetherPost CLI not found. Install with: pip install autopromo"
    exit 1
fi

# Validate configuration
echo "📋 Validating configuration..."
aetherpost validate

# Plan deployment
echo "📊 Planning deployment..."
aetherpost plan

# Apply (with confirmation)
read -p "Apply changes? (y/N): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo "✅ Applying changes..."
    aetherpost apply
else
    echo "❌ Deployment cancelled"
    exit 1
fi

echo "🎉 Deployment complete!"
