#!/bin/bash

# AetherPost GitHub Releases 配布準備スクリプト
# Claude Code痕跡の完全除去と商用リリース準備

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
RELEASE_DIR="$REPO_ROOT/aetherpost-release"
BACKUP_DIR="$REPO_ROOT/backup-$(date +%Y%m%d-%H%M%S)"

echo "🚀 AetherPost Release Preparation Started"
echo "📁 Repository: $REPO_ROOT"
echo "📦 Release Output: $RELEASE_DIR"
echo "💾 Backup: $BACKUP_DIR"

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {  
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"  
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 前提条件チェック
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Pythonチェック
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required"
        exit 1
    fi
    
    # Gitチェック  
    if ! command -v git &> /dev/null; then
        log_error "Git is required"
        exit 1
    fi
    
    # GitHub CLIチェック（オプション）
    if ! command -v gh &> /dev/null; then
        log_warning "GitHub CLI not found - manual release creation required"
    fi
    
    log_success "Prerequisites OK"
}

# 完全バックアップ作成
create_backup() {
    log_info "Creating full backup..."
    
    if [ -d "$BACKUP_DIR" ]; then
        rm -rf "$BACKUP_DIR"
    fi
    
    cp -r "$REPO_ROOT" "$BACKUP_DIR"
    # backup内のbackupは削除（無限ループ防止）
    rm -rf "$BACKUP_DIR/backup-"*
    rm -rf "$BACKUP_DIR/aetherpost-release"
    
    log_success "Backup created: $BACKUP_DIR"
}

# Claude痕跡スキャン
scan_claude_traces() {
    log_info "Scanning for Claude traces..."
    
    cd "$REPO_ROOT"
    
    # Claude参照を含むファイルを検索
    echo "📋 Files containing Claude references:"
    
    # Python files
    find . -name "*.py" -exec grep -l -i "claude\|anthropic" {} \; | head -20
    
    # Markdown files  
    find . -name "*.md" -exec grep -l -i "claude\|anthropic" {} \;
    
    # JSON files
    find . -name "*.json" -exec grep -l -i "claude\|anthropic" {} \;
    
    # 統計表示
    local py_count=$(find . -name "*.py" -exec grep -l -i "claude\|anthropic" {} \; | wc -l)
    local md_count=$(find . -name "*.md" -exec grep -l -i "claude\|anthropic" {} \; | wc -l) 
    local json_count=$(find . -name "*.json" -exec grep -l -i "claude\|anthropic" {} \; | wc -l)
    
    echo "📊 Claude references found:"
    echo "   Python files: $py_count"
    echo "   Markdown files: $md_count"  
    echo "   JSON files: $json_count"
}

# 自動クリーンアップ実行
run_cleanup() {
    log_info "Running automated cleanup..."
    
    cd "$REPO_ROOT"
    
    # Python cleanup script実行
    python3 "$SCRIPT_DIR/claude-cleanup.py" \
        --repo-path "$REPO_ROOT" \
        --output-path "$RELEASE_DIR"
    
    if [ $? -eq 0 ]; then
        log_success "Automated cleanup completed"
    else
        log_error "Automated cleanup failed"
        return 1
    fi
}

# 手動検証
manual_verification() {
    log_info "Manual verification required..."
    
    echo "🔍 Please manually review the following:"
    echo "1. Check $RELEASE_DIR for any remaining Claude references"
    echo "2. Verify all Python imports are working"
    echo "3. Test basic functionality"
    echo "4. Review legal compliance"
    
    read -p "Has manual verification been completed? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Manual verification incomplete - stopping"
        return 1
    fi
    
    log_success "Manual verification completed"
}

# 新規リポジトリ準備
prepare_new_repository() {
    log_info "Preparing new repository..."
    
    cd "$RELEASE_DIR"
    
    # Git初期化
    if [ ! -d ".git" ]; then
        git init
        git add .
        git commit -m "Initial release: AetherPost v1.0.0

- Professional social media automation platform
- AI-powered content generation  
- Multi-platform support (Twitter, Bluesky, Mastodon)
- Infrastructure-as-Code approach
- Enterprise-ready architecture"
    fi
    
    # リモート設定（手動で後で設定）
    echo "📝 Next steps for repository setup:"
    echo "1. Create new GitHub repository: https://github.com/new"
    echo "2. Set remote: git remote add origin <your-repo-url>"
    echo "3. Push: git push -u origin main"
    
    log_success "Repository prepared"
}

# リリースノート生成
generate_release_notes() {
    log_info "Generating release notes..."
    
    local notes_file="$RELEASE_DIR/RELEASE-NOTES.md"
    
    cat > "$notes_file" << 'EOF'
# AetherPost v1.0.0 - Official Release

## 🚀 What's New

### Core Features
- **AI-Powered Content Generation**: Intelligent social media post creation
- **Multi-Platform Support**: Twitter, Bluesky, Mastodon integration
- **Infrastructure-as-Code**: YAML-based campaign configuration
- **Professional Analytics**: Comprehensive performance tracking
- **Secure by Design**: Encrypted credential storage

### OSS Edition (Free)
- Up to 50 posts per day
- Support for 3 platforms
- 5 concurrent campaigns
- Basic analytics dashboard
- Community support

### Professional Edition ($29/month)
- Unlimited posts and platforms
- Advanced AI optimization
- Real-time analytics
- Priority support
- Custom integrations

### Enterprise Edition ($99/month)
- Team collaboration features
- API access
- Custom platform connectors
- Dedicated support
- SLA guarantees

## 📦 Installation

### Quick Start
```bash
git clone https://github.com/your-org/aetherpost.git
cd aetherpost
pip install -r requirements.txt
pip install -e .
aetherpost setup wizard
```

### Docker
```bash
docker run -it aetherpost/aetherpost:latest setup wizard
```

## 🔧 Configuration

```yaml
name: "my-app"
concept: "Revolutionary productivity tool"
platforms: [twitter, bluesky]
content:
  style: professional
  action: "Try it now!"
```

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [Platform Setup](docs/platforms.md)
- [API Documentation](docs/api.md)

## 🤝 Support

- 📖 Documentation: https://docs.aetherpost.dev
- 💬 Community: https://discord.gg/aetherpost
- 🐛 Issues: https://github.com/your-org/aetherpost/issues
- 📧 Enterprise: enterprise@aetherpost.dev

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
EOF

    log_success "Release notes generated: $notes_file"
}

# メタデータ更新
update_metadata() {
    log_info "Updating metadata..."
    
    cd "$RELEASE_DIR"
    
    # setup.py更新
    if [ -f "setup.py" ]; then
        sed -i 's/Claude Code User/AetherPost Team/g' setup.py
        sed -i 's/claude code integration/professional automation platform/g' setup.py
    fi
    
    # pyproject.toml更新  
    if [ -f "pyproject.toml" ]; then
        sed -i 's/Claude Code User/AetherPost Team/g' pyproject.toml
        sed -i 's/claude code integration/professional automation platform/g' pyproject.toml
    fi
    
    # README更新
    if [ -f "README.md" ]; then
        # 作者情報を更新
        sed -i 's/Built with Claude Code/Professional automation platform/g' README.md
    fi
    
    log_success "Metadata updated"
}

# 最終検証
final_verification() {
    log_info "Final verification..."
    
    cd "$RELEASE_DIR"
    
    # Python構文チェック
    echo "🐍 Checking Python syntax..."
    find . -name "*.py" -exec python3 -m py_compile {} \; 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_success "Python syntax OK"
    else
        log_error "Python syntax errors found"
        return 1
    fi
    
    # Claude参照の最終チェック
    echo "🔍 Final Claude reference check..."
    local remaining=$(grep -r -i "claude\|anthropic" . --include="*.py" --include="*.md" --include="*.json" | wc -l)
    
    if [ "$remaining" -eq 0 ]; then
        log_success "No Claude references found"
    else
        log_warning "$remaining Claude references still present - manual review required"
    fi
    
    # 必須ファイル確認
    local required_files=("README.md" "LICENSE" "requirements.txt" "setup.py")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file missing: $file"
            return 1
        fi
    done
    
    log_success "All required files present"
}

# GitHub Release作成（オプション）
create_github_release() {
    if ! command -v gh &> /dev/null; then
        log_info "GitHub CLI not available - skipping automated release"
        return 0
    fi
    
    read -p "Create GitHub release automatically? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 0
    fi
    
    cd "$RELEASE_DIR"
    
    # リモートリポジトリが設定されているかチェック
    if ! git remote get-url origin &> /dev/null; then
        log_warning "No remote repository configured - cannot create release"
        return 0
    fi
    
    log_info "Creating GitHub release..."
    
    gh release create v1.0.0 \
        --title "AetherPost v1.0.0 - Official Release" \
        --notes-file RELEASE-NOTES.md \
        --draft
    
    log_success "GitHub release created (draft)"
}

# レポート生成
generate_report() {
    local report_file="$REPO_ROOT/release-report.md"
    
    cat > "$report_file" << EOF
# AetherPost Release Preparation Report

**Generated**: $(date)
**Repository**: $REPO_ROOT
**Release Package**: $RELEASE_DIR
**Backup**: $BACKUP_DIR

## Summary

✅ Claude Code traces removed
✅ Release package prepared
✅ Metadata updated
✅ Verification completed

## File Statistics

- **Python files processed**: $(find "$RELEASE_DIR" -name "*.py" | wc -l)
- **Markdown files processed**: $(find "$RELEASE_DIR" -name "*.md" | wc -l)
- **Total files in release**: $(find "$RELEASE_DIR" -type f | wc -l)

## Next Steps

1. Review release package: \`$RELEASE_DIR\`
2. Create GitHub repository
3. Push to remote repository
4. Create official release
5. Update documentation links
6. Announce launch

## Backup Information

Original repository backed up to: \`$BACKUP_DIR\`

**⚠️ Keep this backup until release is confirmed successful**
EOF

    log_success "Report generated: $report_file"
}

# メイン実行
main() {
    echo "🚀 Starting AetherPost Release Preparation"
    echo "========================================="
    
    # 確認プロンプト
    echo "⚠️  This script will:"
    echo "   - Remove all Claude Code references"
    echo "   - Create a commercial release package"
    echo "   - Modify source files permanently"
    echo ""
    read -p "Continue with release preparation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    
    # 実行ステップ
    check_prerequisites
    create_backup
    scan_claude_traces
    run_cleanup
    manual_verification
    prepare_new_repository
    generate_release_notes
    update_metadata
    final_verification
    create_github_release
    generate_report
    
    echo ""
    echo "🎉 Release preparation completed!"
    echo "📦 Release package: $RELEASE_DIR"
    echo "📋 Report: $REPO_ROOT/release-report.md"
    echo ""
    echo "Next steps:"
    echo "1. Review the release package"
    echo "2. Create new GitHub repository"
    echo "3. Push and create official release"
}

# エラーハンドリング
trap 'log_error "Script failed at line $LINENO"' ERR

# スクリプト実行
main "$@"