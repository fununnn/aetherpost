# Manual Release Guide - v1.5.0

## 🎯 現在の状況
- ✅ コード実装完了
- ✅ v1.5.0タグ作成済み
- ✅ 配布パッケージ構築済み (dist/)
- ✅ S3ドキュメント更新完了
- 🔄 PyPI配布 - トークン必要
- 🔄 GitHub Release - Web UIで可能

## 📦 PyPI リリース手順

### 1. PyPI トークン取得
1. https://pypi.org でログイン
2. Account settings → API tokens → Add API token
3. Name: `aetherpost-release`, Scope: Entire account
4. トークンをコピー

### 2. アップロード実行
```bash
# トークン設定
export PYPI_API_TOKEN="pypi-XXXXXXXXXXXXXXXXXXXXXXXX"

# アップロード
python -m twine upload dist/* --username __token__ --password "$PYPI_API_TOKEN"
```

### 3. 確認
```bash
pip install aetherpost==1.5.0
python -c "import aetherpost; print(aetherpost.__version__)"
```

## 🏷️ GitHub Release 作成手順

### Web UI使用 (推奨)
1. https://github.com/fununnn/aetherpost/releases にアクセス
2. "Create a new release" をクリック
3. 以下を入力:

**Tag:** v1.5.0 (既存タグを選択)

**Title:** v1.5.0 - Universal Profile Management

**Description:**
```markdown
# 🚀 AetherPost v1.5.0 - Universal Profile Management

## ✨ Major New Features

### 🌐 Complete Profile Management System
- **全プラットフォーム対応**: Twitter, Bluesky, Mastodon, Instagram, Discord
- **統一設定**: 1つの`campaign.yaml`で全プラットフォームのプロファイル管理
- **自動最適化**: 各プラットフォームの文字数制限に自動対応
- **プレビュー機能**: `aetherpost plan`で事前確認

### 🎯 Platform Support
- ✅ **Twitter/X**: Full profile sync (name, bio, website)
- ✅ **Bluesky**: Full profile sync (name, bio, website) 
- ✅ **Mastodon**: Full profile sync (name, bio, website field)
- ✅ **Instagram**: Bio and website sync (business accounts)
- ✅ **Discord**: Bot username updates (API limitations)

## 📋 Usage

```yaml
# campaign.yaml
profile:
  display_name: "My Project"
  bio: "🚀 Amazing tool for developers"
  website: "https://github.com/user/project"
  sync_on_apply: true
```

```bash
aetherpost plan   # Preview profile updates
aetherpost apply  # Apply posts + profile updates
```

## 🔧 Technical Improvements
- Enhanced character limit optimization
- Robust error handling for all platforms
- Unified profile sync architecture
- Comprehensive platform-specific documentation

## 📈 Platform Character Limits
- **Twitter**: 160 chars bio, 50 char name
- **Bluesky**: 256 chars bio, 64 char name  
- **Mastodon**: 500 chars bio, 30 char name
- **Instagram**: 150 chars bio, 30 char name
- **Discord**: 190 chars bio, 32 char name

## 🚀 Installation

```bash
pip install aetherpost==1.5.0
# or
pip install --upgrade aetherpost
```

## 📚 Documentation
- [Profile Management Guide](https://d3b75mcubdhimz.cloudfront.net/profile-management.html)
- [Complete Documentation](https://d3b75mcubdhimz.cloudfront.net)

This release enables consistent branding across all social media platforms with a single, unified configuration!
```

4. **Assets**: 以下のファイルをドラッグ&ドロップ
   - `/home/ubuntu/doc/autopromo/dist/aetherpost-1.5.0-py3-none-any.whl`
   - `/home/ubuntu/doc/autopromo/dist/aetherpost-1.5.0.tar.gz`

5. "Publish release" をクリック

## 📊 リリース完了後の確認

### PyPI確認
```bash
# 新版確認
pip search aetherpost || curl https://pypi.org/pypi/aetherpost/json | jq '.info.version'

# インストールテスト
pip install aetherpost==1.5.0
aetherpost --version
```

### GitHub確認
- https://github.com/fununnn/aetherpost/releases でv1.5.0表示確認
- ダウンロード数確認

### ドキュメント確認
- https://d3b75mcubdhimz.cloudfront.net でプロファイル機能確認
- https://d3b75mcubdhimz.cloudfront.net/profile-management.html アクセス確認

## 🎉 完了
すべて完了後、各プラットフォームでv1.5.0リリース告知を実施！