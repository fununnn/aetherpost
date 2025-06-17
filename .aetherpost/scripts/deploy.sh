#!/bin/bash
# AutoPromo Deployment Script
# Generated for local backend with production template

set -e

echo "🚀 Deploying AutoPromo..."

# Check requirements
if ! command -v autopromo &> /dev/null; then
    echo "❌ AutoPromo CLI not found. Install with: pip install autopromo"
    exit 1
fi

# Validate configuration
echo "📋 Validating configuration..."
autopromo validate

# Plan deployment
echo "📊 Planning deployment..."
autopromo plan

# Apply (with confirmation)
read -p "Apply changes? (y/N): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo "✅ Applying changes..."
    autopromo apply
else
    echo "❌ Deployment cancelled"
    exit 1
fi

echo "🎉 Deployment complete!"
