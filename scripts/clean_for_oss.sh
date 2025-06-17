#!/bin/bash

# Clean repository for OSS release
# Removes sensitive data and creates clean git history

set -e

echo "🧹 Cleaning AetherPost for OSS Release"
echo "======================================"

# 1. Remove sensitive files
echo "🔒 Removing sensitive files..."
rm -f .env .env.test .env.self_promotion
rm -f logs/*.json 2>/dev/null || true
rm -f *.state.json 2>/dev/null || true
rm -f .docs-config 2>/dev/null || true

# 2. Clean git history
echo "📝 Creating clean git repository..."
rm -rf .git
git init
git branch -m main

# 3. Create clean .gitignore
echo "📋 Creating clean .gitignore..."
cat > .gitignore << 'EOF'
# Environment files
.env*
!.env.example

# Logs
logs/*.json
*.log

# State files  
*.state.json
promo.state.json

# Temporary files
.docs-config
cloudfront-config.json
bucket-policy.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# AetherPost specific
.aetherpost/content_cache/
backup_before_cleanup/
aetherpost-release/
test-init/
demo-flow/

# Security - never commit
CLAUDE.md
EOF

# 4. Stage all files
echo "📦 Staging files for initial commit..."
git add .

# 5. Create initial commit
echo "🎯 Creating initial commit..."
git commit -m "Initial release: AetherPost v1.0

Features:
- Multi-platform social media automation
- AI-powered content generation with OpenAI
- Support for Twitter, YouTube, Reddit, Bluesky, Mastodon
- Self-promotion capabilities
- Command-line interface
- Comprehensive documentation

Built with ❤️ for the open source community."

echo ""
echo "✅ Repository cleaned for OSS release!"
echo ""
echo "📊 Repository status:"
git log --oneline
echo ""
echo "🚀 Ready for OSS publication!"
echo "   - No sensitive data in git history"
echo "   - Clean initial commit"
echo "   - Proper .gitignore in place"
echo ""
echo "🌟 Next steps:"
echo "   1. Create GitHub repository"  
echo "   2. git remote add origin <repo-url>"
echo "   3. git push -u origin main"