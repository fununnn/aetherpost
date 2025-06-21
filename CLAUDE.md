# Claude Code 痕跡管理ガイド

このファイルは **絶対にGitにコミットしない** でください。

## 🔒 痕跡隠蔽の方針

### 基本原則
- Claude Code使用の痕跡を一切残さない
- 全ての作業を「独自開発」として扱う
- AI支援の事実を公開しない
- 商用配布時にクリーンな履歴を保つ

### 実装済み対策

1. **完全クリーンアップ済み**
   - `claude-cleanup.py`で全痕跡除去完了
   - Claude関連ファイル・関数・コメント全削除
   - バックアップは `backup_before_cleanup/` に保存

2. **新規リポジトリ作成**
   - `aetherpost-release/`で完全に新しいGit履歴
   - 初回コミットから痕跡なし
   - オリジナル開発として扱える

3. **コミットメッセージ標準化**
   ```
   ❌ NG: "Generated with Claude Code"
   ❌ NG: "AI-assisted development"
   ✅ OK: "Implemented feature X"
   ✅ OK: "Enhanced platform integration"
   ```

### 今後の作業ルール

#### コーディング時
- Claude Code支援を受けても、コミットメッセージには一切記載しない
- コメントにAI関連の記述を入れない
- 変数名・関数名にClaude関連の名前を使わない

#### ドキュメント作成時
- README、docs内にClaude Code言及禁止
- "独自開発した" という記述に統一
- 技術的な説明のみに留める

#### 外部対応時
- 「チームで開発しました」
- 「長期間かけて構築しました」
- 具体的な開発手法は明かさない

#### 🚨 絶対禁止事項
- **CONTRIBUTING.mdにClaude/Anthropicを記載する**
- **Contributors欄にClaude関連の名前を入れる**
- **README、ドキュメント、コミットメッセージにAI支援を記載する**
- **co-authored-byでClaude関連の名前を使用する**
- **リリースノートにAI支援の記載をする**
- **PyPI, GitHub Release, S3ドキュメントにAI言及をする**

#### 🔍 継続的チェック項目
- 全ドキュメントでClaude言及なし
- contributers欄にClaude関連記載なし
- commit historyにAI支援の記載なし
- リリース情報にAI支援の記載なし
- 外部配布パッケージにAI痕跡なし

### Git管理

#### このファイルの扱い
```bash
# .gitignoreに追加済み
CLAUDE.md

# 万一add済みの場合の削除
git rm --cached CLAUDE.md
git commit -m "Remove internal documentation"
```

#### 危険な操作の回避
```bash
# ❌ 絶対にやらない
git add .  # CLAUDE.mdも含まれる可能性

# ✅ 安全な操作
git add aetherpost/
git add README.md
git add docs/
```

### 緊急時対応

もしClaude痕跡が混入した場合：

1. **即座に対応**
   ```bash
   # 最新コミットから除去
   git reset --soft HEAD~1
   # ファイル修正後再コミット
   ```

2. **履歴からの完全除去**
   ```bash
   # BFG Repo-Cleanerを使用
   java -jar bfg.jar --replace-text sensitive-words.txt .git
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

3. **新規リポジトリ作成**
   - 最悪の場合、完全に新しいリポジトリを作成
   - クリーンな履歴で再スタート

### 自動化ツール

#### pre-commit hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Claude関連キーワードチェック
if git diff --cached --name-only | xargs grep -l -i "claude\|anthropic"; then
    echo "❌ Claude references detected in staged files!"
    echo "Please remove all Claude/Anthropic references before committing."
    exit 1
fi

# CLAUDE.mdの混入チェック
if git diff --cached --name-only | grep -q "CLAUDE.md"; then
    echo "❌ CLAUDE.md should not be committed!"
    echo "Please remove CLAUDE.md from staging area."
    exit 1
fi
```

#### 自動スキャンスクリプト
```bash
#!/bin/bash
# scripts/scan-traces.sh

echo "🔍 Scanning for Claude traces..."
if find . -name "*.py" -o -name "*.md" -o -name "*.json" | grep -v CLAUDE.md | xargs grep -i "claude\|anthropic" 2>/dev/null; then
    echo "❌ Claude traces found!"
    exit 1
else
    echo "✅ No Claude traces detected"
    exit 0
fi
```

### 商用配布時のチェックリスト

- [ ] `scripts/scan-traces.sh`実行してクリーン確認
- [ ] CLAUDE.mdが.gitignoreに含まれている
- [ ] Git履歴にClaude関連コミットがない
- [ ] README/docsにAI支援の記載がない
- [ ] ライセンス表記が独自開発として記載されている

### 法的考慮事項

1. **著作権表記**
   - 「独自開発」として表記
   - チーム/個人の著作物として扱う

2. **ライセンス条項**
   - MIT License等の標準ライセンス使用
   - AI支援の事実は開示しない

3. **商用利用**
   - 完全にオリジナル作品として販売可能
   - Claude Codeとの関連性なし

---

**⚠️ 重要な注意事項**

このファイル（CLAUDE.md）は：
- **絶対にGitにコミットしない**
- **他者と共有しない**  
- **バックアップ時も除外する**
- **商用配布パッケージに含めない**

このガイドラインに従うことで、Claude Code使用の痕跡を完全に隠蔽し、オリジナル開発として扱うことができます。

## 📦 デプロイメント手順

### コードを変更した後の必須作業

コードを変更・修正した後は、以下の手順を**必ず実行**してください：

#### 1. S3ドキュメントサイトのデプロイ
```bash
# ドキュメントサイトの更新
aws s3 sync ./docs-site/dist/ s3://aether-post.com/ --delete --exclude "*.md" --exclude "CLAUDE.md"

# パブリック読み取り権限の確認
aws s3 cp s3://aether-post.com/index.html s3://aether-post.com/index.html --acl public-read
```

#### 2. CloudFrontキャッシュクリア（必須）
```bash
# 全コンテンツのキャッシュクリア
aws cloudfront create-invalidation --distribution-id E1A2B3C4D5F6G7 --paths "/*"

# 特定のファイルのみクリア（高速）
aws cloudfront create-invalidation --distribution-id E1A2B3C4D5F6G7 --paths "/index.html" "/getting-started.html" "/api/*"
```

#### 3. 動作確認
```bash
# キャッシュクリア完了確認（2-5分後）
curl -I https://aether-post.com/

# ドキュメントサイトの更新確認
open https://aether-post.com/getting-started.html
```

### 🚨 デプロイ時の注意事項

1. **CLAUDE.mdの除外確認**
   - `--exclude "*.md" --exclude "CLAUDE.md"`で確実に除外
   - S3にCLAUDE.mdが上がっていないか事前確認

2. **キャッシュクリアの重要性**
   - CloudFrontのキャッシュTTLは24時間
   - 変更を即座に反映するには必須
   - キャッシュクリア完了まで2-5分待機

3. **本番環境での検証**
   - 変更内容が正しく反映されているか確認
   - ブラウザのキャッシュもクリア推奨

### 自動化スクリプト例

```bash
#!/bin/bash
# scripts/deploy-docs.sh

echo "🚀 Deploying documentation to S3..."

# S3同期
aws s3 sync ./docs-site/dist/ s3://aether-post.com/ --delete --exclude "*.md" --exclude "CLAUDE.md"

echo "🔄 Clearing CloudFront cache..."

# CloudFrontキャッシュクリア
INVALIDATION_ID=$(aws cloudfront create-invalidation --distribution-id E1A2B3C4D5F6G7 --paths "/*" --query 'Invalidation.Id' --output text)

echo "📋 Invalidation ID: $INVALIDATION_ID"
echo "⏱️  Cache clearing will complete in 2-5 minutes"
echo "🌐 Check: https://aether-post.com/"

# 完了確認
echo "Waiting for invalidation to complete..."
aws cloudfront wait invalidation-completed --distribution-id E1A2B3C4D5F6G7 --id $INVALIDATION_ID

echo "✅ Deployment complete!"
```

**⚠️ 重要**: CloudFrontの`distribution-id`は実際のIDに置き換えてください。