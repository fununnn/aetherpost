# GitHub API Token Setup Guide

## 1. GitHub Personal Access Token 取得

### Classic Token (推奨)
1. https://github.com/settings/tokens にアクセス
2. "Generate new token" → "Generate new token (classic)"
3. Token description: `aetherpost-release`
4. Expiration: `90 days` (または適切な期間)
5. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `write:packages` (Upload packages to GitHub Package Registry)
   - ✅ `read:org` (Read org and team membership)
6. "Generate token" をクリック
7. 表示されたトークンをコピー（一度しか表示されません）

### Fine-grained Token (新形式)
1. https://github.com/settings/personal-access-tokens/fine-grained にアクセス
2. "Generate new token"
3. Token name: `aetherpost-release`
4. Repository access: `Selected repositories` → `fununnn/aetherpost`
5. Permissions:
   - Repository permissions:
     - ✅ `Contents: Write`
     - ✅ `Metadata: Read`
     - ✅ `Pull requests: Write`
   - Account permissions:
     - ✅ `Git SSH keys: Write`
6. "Generate token" をクリック

## 2. Token 設定

### 環境変数として設定
```bash
export GITHUB_TOKEN="ghp_XXXXXXXXXXXXXXXXXXXXXXXX"

# 永続化する場合
echo 'export GITHUB_TOKEN="ghp_XXXXXXXXXXXXXXXXXXXXXXXX"' >> ~/.bashrc
source ~/.bashrc
```

### GitHub CLI 設定
```bash
# GitHub CLI インストール
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# 認証
gh auth login --with-token <<< "$GITHUB_TOKEN"
```

## 3. GitHub Release 作成

### CLI 使用
```bash
gh release create v1.5.0 dist/* \
  --title "v1.5.0 - Universal Profile Management" \
  --notes-file RELEASE_NOTES.md
```

### API 直接使用
```bash
# Release 作成
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/fununnn/aetherpost/releases \
  -d '{
    "tag_name": "v1.5.0",
    "name": "v1.5.0 - Universal Profile Management",
    "body": "🚀 Complete profile management across all platforms",
    "draft": false,
    "prerelease": false
  }'

# アセット追加
RELEASE_ID=$(curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/fununnn/aetherpost/releases/tags/v1.5.0 | \
  jq -r '.id')

curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @dist/aetherpost-1.5.0-py3-none-any.whl \
  "https://uploads.github.com/repos/fununnn/aetherpost/releases/$RELEASE_ID/assets?name=aetherpost-1.5.0-py3-none-any.whl"
```

### Web UI 使用
1. https://github.com/fununnn/aetherpost/releases にアクセス
2. "Create a new release" をクリック
3. Tag: `v1.5.0` (既に存在)
4. Title: `v1.5.0 - Universal Profile Management`
5. Description: リリースノート記載
6. Assets: `dist/` 内のファイルをドラッグ&ドロップ
7. "Publish release" をクリック

## 4. 確認

### Token 動作確認
```bash
# GitHub API テスト
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

# Repository アクセステスト
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/fununnn/aetherpost
```