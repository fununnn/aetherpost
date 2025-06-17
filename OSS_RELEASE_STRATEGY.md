# AetherPost OSS リリース戦略

## 🔒 現在の状況分析

### Private Repository の現状
- ✅ GitHub上でprivate repository
- ✅ 権限設定なし（デフォルト設定）
- ✅ 外部からアクセス不可
- ⚠️ 機密情報が含まれている可能性

## 🛡️ 安全なOSSリリース手順

### 1. 現在のリポジトリ保護 ✅
**現状は既に安全:**
- Private repositoryなので外部に漏洩なし
- 権限設定していないため、意図しないアクセスなし

### 2. 新規クリーンリポジトリ作成（推奨）⭐

```bash
# Step 1: 現在のディレクトリでクリーンアップ実行
./scripts/clean_for_oss.sh

# Step 2: GitHub上で新しいpublic repositoryを作成
# 例: "aetherpost" という名前で

# Step 3: クリーンな履歴をプッシュ
git remote add origin https://github.com/YOUR-USERNAME/aetherpost.git
git push -u origin main
```

### 3. 既存リポジトリ利用方法（次善策）

もし既存のprivate repositoryを使いたい場合：

```bash
# Step 1: ローカルでクリーンアップ
./scripts/clean_for_oss.sh

# Step 2: 強制プッシュで履歴を完全置換
git push --force-with-lease origin main

# Step 3: GitHubでpublic化
# Settings → Danger Zone → Change repository visibility → Make public
```

## 🎯 推奨アプローチ: 新規リポジトリ

### メリット
- **完全隔離**: 機密情報の漏洩リスクゼロ
- **クリーンスタート**: 混乱のない明確な履歴
- **安心感**: 既存privateリポジトリは保持
- **ブランド統一**: "aetherpost"名でリリース可能

### 手順詳細

1. **ローカルクリーンアップ**
   ```bash
   # 現在のディレクトリで実行
   ./scripts/clean_for_oss.sh
   ```

2. **GitHub新規リポジトリ作成**
   - Repository name: `aetherpost`
   - Description: "AI-powered social media automation platform"
   - Public repository
   - MIT License
   - README.md込み

3. **クリーンなコードプッシュ**
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/aetherpost.git
   git push -u origin main
   ```

4. **ドキュメント更新**
   - GitHubリポジトリURLを正しいものに更新
   - ドキュメントサイトのリンク修正

## 🌐 ドキュメントサイト統合

### 現在の設定
- **HTTPS URL**: https://d3b75mcubdhimz.cloudfront.net
- **統一表示**: 全リンクがこのURLに更新済み

### OSS公開後の調整

GitHubリポジトリ作成後：

```bash
# ドキュメント内のリンクを正しいGitHubリポジトリに更新
find docs-site -name "*.html" -exec sed -i 's#https://d3b75mcubdhimz.cloudfront.net#https://github.com/YOUR-USERNAME/aetherpost#g' {} \;

# CloudFrontに再アップロード
aws s3 sync docs-site/ s3://aetherpost-docs/ --delete
```

## 🔐 セキュリティチェックリスト

### クリーンアップ対象 ✅
- [ ] `.env*` ファイル全削除
- [ ] API keys / tokens除去  
- [ ] Git履歴完全消去
- [ ] 適切な.gitignore設定
- [ ] 機密情報スキャン完了

### 除外すべきファイル ✅
```
.env*
logs/*.json
*.state.json
backup_before_cleanup/
aetherpost-release/
CLAUDE.md  # 👈 重要: 絶対に含めない
```

## 🚀 公開後のメンテナンス

### GitHub Repository設定
- **Issues**: 有効化
- **Discussions**: 有効化  
- **Security**: Vulnerability alertsを有効化
- **Pages**: ドキュメントサイトをGitHub Pagesでも提供可能

### CI/CD設定
- GitHub Actions for testing
- Automated releases
- Code quality checks

## ⚠️ 注意事項

### 絶対に避けるべきこと
1. **既存privateリポジトリの直接公開化**
2. **履歴を残したままの移行**  
3. **CLAUDE.mdの公開**
4. **API keysの混入**

### 安全な手順の確認
✅ 新規リポジトリ作成  
✅ クリーンアップスクリプト使用  
✅ 機密情報の完全除去  
✅ 適切な.gitignore設定  

---

**推奨事項**: 新規public repositoryを作成し、クリーンアップしたコードのみを公開することで、最も安全にOSSリリースが可能です。