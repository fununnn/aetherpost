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

---

# 🎯 AetherPost 設計方針・開発指針

## 核心コンセプト: 極限までシンプルなワークフロー

AetherPostは **Terraform風の3コマンドワークフロー** を採用し、ソーシャルメディア自動化を完全自動化します。

### 基本ワークフロー（3コマンドのみ）

```bash
# 1. 初期セットアップ（1回のみ）
aetherpost init     # 全ての設定・プロフィール生成・API設定完了

# 2. プロモーション計画確認
aetherpost plan     # 投稿内容プレビュー

# 3. 実行・継続
aetherpost apply    # 実際の投稿・プロフィール更新実行
```

**やめるとき:**
```bash
aetherpost destroy  # 全ての自動投稿停止・クリーンアップ
```

## 🎭 完全自動化の対象プラットフォーム

### 対応5プラットフォーム
1. **Twitter** - ツイート投稿・プロフィール更新・アイコン設定
2. **Bluesky** - ポスト投稿・プロフィール更新・アイコン設定  
3. **Instagram** - 投稿・ストーリー・プロフィール更新・アイコン設定
4. **LinkedIn** - 投稿・プロフィール更新・アイコン設定
5. **YouTube** - 動画投稿・チャンネル説明更新・アイコン設定

### 各プラットフォームでの自動処理

#### 共通機能（全プラットフォーム）
- **アイコン自動生成・設定**: AI生成ロゴをプロフィール画像に設定
- **プロフィール文自動生成・更新**: キャンペーン内容に基づく最適化プロフィール
- **日々のプロモーション投稿**: 継続的なコンテンツ生成・投稿

#### プラットフォーム固有機能
- **Twitter**: 280文字最適化ツイート、リツイート戦略
- **Bluesky**: 256文字最適化ポスト、分散型特性活用
- **Instagram**: ビジュアルコンテンツ、ストーリー投稿
- **LinkedIn**: プロフェッショナル向けコンテンツ
- **YouTube**: 動画投稿、チャンネル最適化、サムネイル生成

## 🎚️ 設定方法: 2つのアプローチ

### インタラクティブ初期化 → 自動ファイル生成
```bash
aetherpost init
# インタラクティブで設定収集:
# - プロジェクト名・説明入力
# - プラットフォーム選択  
# - API キー設定（ブラウザで直接取得ガイド）
# - アイコン生成・プロフィール生成
# - 投稿スケジュール設定
#
# → 自動的にcampaign.yamlを生成
# → plan/apply はそのファイルを使用
```

### 既存ファイル再利用（Claude Code等）
```bash
# campaign.yaml + .env.aetherpost を事前作成済みの場合
aetherpost init  # 既存設定を検出・そのまま利用
```

## 🔧 チューニング: ファイル編集のみ

**基本原則**: 追加コマンドは不要。設定ファイル編集で全て対応。

### campaign.yaml での調整
```yaml
# プロモーション内容の調整
content:
  style: friendly          # professional, creative, casual
  frequency: daily         # hourly, daily, weekly
  themes:
    - "新機能紹介"
    - "ユーザー事例"
    - "技術解説"

# プラットフォーム固有設定
platforms:
  twitter:
    hashtags: ["#開発", "#AI"]
    engagement_strategy: "active"
  youtube:
    video_length: "short"   # short, medium, long
    upload_schedule: "weekly"
```

### .env.aetherpost での調整
```bash
# 投稿頻度・タイミング調整
AETHERPOST_POSTING_FREQUENCY=daily
AETHERPOST_POSTING_TIME=09:00
AETHERPOST_TIMEZONE=Asia/Tokyo

# AI生成パラメータ調整
CONTENT_CREATIVITY_LEVEL=0.7
CONTENT_PROFESSIONAL_TONE=true
ICON_GENERATION_STYLE=modern

# プラットフォーム別有効無効
TWITTER_ENABLED=true
BLUESKY_ENABLED=true
INSTAGRAM_ENABLED=false
```

## 🚀 実行フロー詳細

### aetherpost init の処理内容
1. **プロジェクト設定収集**: 名前・説明・URL・ターゲット
2. **プラットフォーム選択**: 5つから利用するものを選択
3. **API認証設定**: 各プラットフォームAPI設定完了
4. **アイコン生成**: AIでプロジェクトロゴ自動生成
5. **プロフィール生成**: 各プラットフォーム最適化プロフィール文生成
6. **初期投稿計画**: 最初の投稿内容生成
7. **ワークスペース作成**: `.aetherpost/` ディレクトリ構築

### aetherpost plan の処理内容
1. **投稿内容生成**: 各プラットフォーム向けコンテンツ
2. **プレビュー表示**: 実際の投稿内容確認
3. **スケジュール確認**: 投稿タイミング表示
4. **リソース確認**: アイコン・画像等の生成状況

### aetherpost apply の処理内容
1. **プロフィール更新**: アイコン・プロフィール文設定
2. **投稿実行**: 生成されたコンテンツを実際に投稿
3. **継続スケジュール開始**: 日々の自動投稿開始
4. **状態保存**: 実行状況をステートファイルに保存

### aetherpost destroy の処理内容
1. **自動投稿停止**: 継続的投稿の停止
2. **スケジュール削除**: 予約投稿のキャンセル
3. **ステートファイル削除**: 実行履歴のクリーンアップ
4. **プロフィール復元** (オプション): 元のプロフィールに戻す

## 🎨 コンテンツ生成戦略

### 多様性確保
- **テーマローテーション**: 機能紹介→ユーザー事例→技術背景→未来展望
- **トーン変化**: フォーマル→カジュアル→専門的→親しみやすい
- **フォーマット多様化**: テキスト→画像付き→動画→投票

### プラットフォーム最適化
- **Twitter**: 短文・ハッシュタグ最適化・リプライ戦略
- **LinkedIn**: 長文・専門性重視・ビジネス観点
- **Instagram**: ビジュアル重視・ストーリー活用
- **YouTube**: 動画コンテンツ・SEO最適化・サムネイル

## 🔄 継続的改善

### 自動学習機能
- **エンゲージメント分析**: 反応の良い投稿パターン学習
- **最適タイミング発見**: フォロワー活動時間分析
- **コンテンツ最適化**: A/Bテストによる改善

### メンテナンスフリー設計
- **API制限自動回避**: レート制限検知・待機
- **エラー自動復旧**: 一時的障害からの自動回復
- **設定自動更新**: プラットフォーム仕様変更への対応

## 📊 運用監視

### ダッシュボード機能（Web UI）
- **投稿状況確認**: 各プラットフォームの投稿履歴
- **エンゲージメント統計**: いいね・リツイート・コメント数
- **フォロワー増減**: 成長トレンド可視化
- **コンテンツ効果分析**: 最も効果的な投稿タイプ特定

### アラート機能
- **API制限警告**: 使用量90%到達時通知
- **投稿失敗通知**: エラー発生時の即座通知
- **成果報告**: 週次・月次成果サマリー

## 🎯 開発優先順位

### v1.x系 (現在)
- [x] 基本3コマンドワークフロー
- [x] 5プラットフォーム対応
- [x] プロフィール自動生成
- [ ] アイコン自動生成・設定
- [ ] 継続投稿システム

### v2.x系 (次期)
- [ ] Web UIダッシュボード
- [ ] 高度なエンゲージメント分析
- [ ] A/Bテスト機能
- [ ] マルチ言語対応

### v3.x系 (将来)
- [ ] 動画コンテンツ自動生成
- [ ] インフルエンサー連携
- [ ] 広告キャンペーン統合

---

## 🔄 ワークフロー詳細

### ファイル連携フロー
```bash
aetherpost init
# └── インタラクティブ設定収集
#     └── campaign.yaml 自動生成
#         ├── プロジェクト情報
#         ├── プラットフォーム設定
#         ├── コンテンツ設定
#         └── URLs設定

aetherpost plan
# └── campaign.yaml 読み込み
#     └── 投稿内容生成・プレビュー

aetherpost apply  
# └── campaign.yaml 読み込み
#     └── 実際の投稿・プロフィール更新実行
```

### 設定ファイルの役割
- **campaign.yaml**: initで生成される中心設定ファイル
- **.env.aetherpost**: API認証情報（機密情報）
- **plan/apply**: 常にcampaign.yamlを参照

---

**核心思想**: 「設定は1回、あとは全自動」

AetherPostは開発者が本来の開発に集中できるよう、ソーシャルメディアプロモーションを完全に自動化します。複雑なコマンドや継続的な手動操作は一切不要。Terraformのシンプルさとソーシャルメディアの効果的活用を両立させた、究極のプロモーション自動化ツールです。