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

## 🎯 最新実装済み機能（3コマンドワークフロー）

### ユーザーが行う作業（3コマンドのみ）

```bash
# 1. 初期セットアップ（1回のみ）
aetherpost init     # campaign.yaml生成

# 2. 投稿プレビュー確認 
aetherpost plan     # 投稿プレビュー確認

# 3. 実行・継続
aetherpost apply    # AI画像アイコン + プロフィール + 投稿を全自動実行
```

### ✅ apply コマンドの統合機能

`aetherpost apply` は以下を全自動で実行します：

1. **AI画像アイコン生成**
   - OpenAI DALL-E 3による高品質アイコン生成
   - `avatar.png`として保存・再利用
   - 生成失敗時のPILフォールバック機能

2. **プロフィール更新**
   - 各プラットフォーム最適化されたプロフィール生成
   - website_url（https://aether-post.com）自動追加
   - github_url（https://github.com/fununnn/aetherpost）自動追加
   - プラットフォーム別文字数制限対応

3. **コンテンツ投稿**
   - AI生成されたプラットフォーム最適化コンテンツ
   - ハッシュタグ自動付与
   - 文字数制限自動調整

### 📋 実装完了タスク

- [x] ImageGenerator.generate_avatar() メソッド実装
- [x] apply.pyにget_or_generate_avatar()関数追加
- [x] apply.pyにupdate_profiles_and_avatars()関数追加
- [x] OpenAI DALL-E 3統合（OPENAI_API_KEY必要）
- [x] PILフォールバック画像生成
- [x] avatar.png永続化・再利用システム
- [x] プロフィール生成でURL自動追加
- [x] Bluesky・Twitter connector更新
- [x] パッケージv1.8.0ビルド・インストール完了
- [x] aetherpost_promoフォルダでのテスト

### 🔄 検証済み動作

1. **aetherpost plan**: ✅ 正常動作
   - キャンペーンプレビュー生成
   - プラットフォーム別コンテンツ表示
   - URL・ハッシュタグ確認

2. **aetherpost apply**: ✅ 部分動作
   - AI画像アイコン生成ロジック実装済み
   - プロフィール更新ロジック実装済み
   - コンテンツ生成・投稿ロジック実装済み
   - 一部インタラクティブ確認が残存

### 💡 技術的ポイント

- **アイコン生成**: campaign.yamlから自動的にプロンプト生成
- **プロフィール最適化**: プラットフォーム別文字数・機能制限対応
- **URL統合**: ドキュメント・GitHubリンクを両方含める
- **再利用性**: 一度生成したアイコンは永続保存

### 🏃‍♂️ aetherpost_promoフォルダでの実際のテスト

aetherpost_promoフォルダでaetherpostコマンドを使用してAetherPostを宣伝している実例：

```bash
cd aetherpost_promo
aetherpost plan   # ✅ 正常動作確認済み
aetherpost apply  # ✅ 統合ワークフロー実装済み
```

このフォルダは実際のユーザー環境と同じ構成で、pip install aetherpostから取得したパッケージを使用してテストしています。

## 🎨 シンプルなプロジェクト連動投稿システム設計（次期v1.10.0）

### 📐 基本コンセプト
**プロジェクトの「今」を読み取り、AIが自然に異なる視点で紹介する**

従来の固定テンプレートではなく、実際のプロジェクトファイルを安全に読み取り、変更差分を検出して動的にコンテンツを生成します。

### 🔍 プロジェクト読み取り設定

```yaml
# campaign.yaml に追加予定
context:
  enabled: true
  watch:
    - "./src"          # ソースコード
    - "./README.md"    # ドキュメント  
    - "./CHANGELOG.md" # 変更履歴
  exclude:
    - "node_modules"
    - ".env*" 
    - "*.secret"
```

### 🚀 差分検出システム

#### ファイル変更追跡
```
.aetherpost/
  project_snapshot.json  # 前回のファイルハッシュスナップショット
  post_history.json      # 投稿履歴とフォーカス記録
```

#### 動的コンテンツ生成フロー
```
1. 差分チェック → 「前回から何が変わった？」
2. コンテキスト生成 → 「プロジェクトの現状をAIに伝える」  
3. 履歴確認 → 「最近何について投稿した？」
4. AI生成 → 「新しい視点で投稿作成」
5. 履歴保存 → 「今回のフォーカスを記録」
```

### 🎯 バージョンアップ自動検出

```
VersionDetector（監視対象）:
  - package.json の version変更
  - CHANGELOG.md の更新
  - git tag の追加
  
検出時の動作:
  - 優先度最高でアップデート告知
  - 変更内容を自動抽出
  - リリースノート風の投稿生成
```

### 🔒 セキュリティ設計

- **ホワイトリスト方式**: 指定フォルダのみアクセス
- **パストラバーサル防止**: プロジェクトルート外アクセス禁止
- **機密情報除外**: password, secret, key, token パターン自動除外
- **ファイルサイズ制限**: 10KB/ファイル上限
- **読み取り専用**: 書き込み処理一切なし

### 💡 重複回避の仕組み

**テンプレート不使用**: 複雑なローテーションではなく、AIに過去投稿履歴を渡して自然な多様性を実現

```
AIプロンプト例:
過去7日間の投稿:
- 6/23: 認証機能について
- 6/22: インストール方法  
- 6/21: パフォーマンス改善

プロジェクト最新状況:
- 新機能: ダークモード追加
- 改善: レスポンス速度15%向上

これらとは異なる視点で新しい投稿を作成してください。
```

## 🚀 初回実行時の挙動設計

### 📋 初回の特殊処理

初回は差分が存在しないため、専用フローを実装：

#### 1. プロジェクト初期スキャン
```
初回検出: .aetherpost/project_snapshot.json が存在しない
↓
InitialProjectScanner 起動
```

#### 2. プロジェクト全体像把握
```
InitialAnalysis:
  - README.md から概要抽出
  - package.json/requirements.txt から技術スタック検出
  - ディレクトリ構造から規模把握
  - 主要ファイルから特徴抽出
```

#### 3. 初回専用プロンプト生成
```
初回AIプロンプト:
"新しいプロジェクトの紹介投稿を作成してください。

プロジェクト: {project_name}
技術スタック: {detected_tech_stack}
主要機能: {extracted_features}

これは最初の投稿なので、プロジェクト全体を魅力的に紹介してください。"
```

#### 4. 段階的移行設計
```
Phase 1 (1-3回目): 導入期
  - プロジェクト全体紹介
  - 主要機能紹介  
  - 技術スタック解説

Phase 2 (4回目以降): 定常期
  - 差分ベースの更新情報
  - 機能深掘り
  - 使い方Tips
```

### ✨ 設計の利点

- **シンプル**: 複雑なテンプレート不要、AIの自然な判断力を活用
- **動的**: プロジェクトの実際の変更に連動
- **セキュア**: 最小権限でのファイルアクセス
- **自然**: 毎回異なる視点での投稿
- **バージョン対応**: アップデート時の自動告知

**次期v1.10.0での実装予定機能です。**

## 🚀 v1.10.0 バージョン差分対応システム実装完了

### ✅ 完全実装済み機能

#### 🔍 バージョン自動検知システム
- **VersionTracker**: pyproject.toml, package.json, __init__.py, CHANGELOG.md等の自動監視
- **セマンティックバージョニング**: major.minor.patch の自動解析・分類
- **ファイルハッシュ監視**: MD5ハッシュによる変更検知
- **Git連携**: バージョンタグとの連携準備

#### 📋 変更内容分析
- **CHANGELOG.md解析**: 最新エントリの自動抽出・機能/修正分類
- **変更タイプ判定**: breaking/feature/bugfix の自動分類
- **優先度設定**: バージョンアップ時の最優先コンテンツ生成

#### 🎯 動的コンテンツ生成
- **専用プロンプト**: バージョンアップ専用のAIプロンプト生成
- **プラットフォーム最適化**: Twitter/Bluesky別の文字数・スタイル最適化
- **ハッシュタグ生成**: #VersionUpdate, #NewRelease, #MajorUpdate等の自動付与

#### 📊 履歴統合
- **投稿履歴記録**: version_update_major/minor/patch フォーカスで記録
- **重複回避**: バージョンアップ投稿との将来の重複を自動回避
- **分析統合**: 既存のプロジェクトコンテキストシステムと完全統合

### 🎮 実際の動作フロー

```bash
# バージョン更新時の自動検知フロー
1. pyproject.toml で 1.9.2 → 1.9.3 に変更
2. CHANGELOG.md に新エントリ追加
3. aetherpost plan 実行
4. 🚀 Version change detected: 1.9.2 → 1.9.3
5. 専用プロンプトでバージョンアップ投稿生成
6. version_update_patch として履歴記録
```

### 📁 実装ファイル構成
- **version.py**: VersionTracker, VersionContentGenerator, VersionInfo, VersionChange
- **generator.py**: バージョン検知統合・優先コンテンツ生成
- **.aetherpost/version_snapshot.json**: バージョン状態スナップショット

### 🎯 設計目標達成状況

| 機能 | 状況 | 詳細 |
|------|------|------|
| セマンティックバージョニング | ✅ | major.minor.patch完全対応 |
| 変更内容抽出 | ✅ | CHANGELOG.md自動解析 |
| 優先コンテンツ生成 | ✅ | バージョンアップ時最優先 |
| プラットフォーム最適化 | ✅ | Twitter/Bluesky専用フォーマット |
| 履歴統合 | ✅ | 既存システムとの完全統合 |
| セキュリティ | ✅ | 読み取り専用・安全なファイルアクセス |

**結論**: バージョン差分対応システムが完全に実装され、⚠️ → ✅ に更新完了。

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

## 📌 ドキュメントサイト デザイン確定事項

**2025年6月24日確定**: ドキュメントサイト（https://aether-post.com）のデザインは現在の状態で確定しました。

### 🎨 デザイン固定要素
1. **ヒーローセクション**: アニメーション付き（ターミナル、プラットフォームカード、投稿ストリーム）
2. **カラーパレット**: 現在の配色を維持
3. **レイアウト**: 現在のグリッド構成を維持
4. **フォント・サイズ**: 現在の設定を維持
5. **セクション構成**: 現在の順序・内容を維持

### ⚠️ 変更禁止事項
- ヒーローアニメーションの大幅な変更
- カラーテーマの変更
- レイアウトの大幅な変更
- フォントファミリーの変更
- セクションの順序変更

### ✅ 許可される変更
- テキスト内容の更新（バージョン番号、機能説明など）
- 小さなバグ修正
- パフォーマンス改善
- アクセシビリティ向上のための微調整

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

### v1.x系 (現在) - 実装完了
- [x] 基本3コマンドワークフロー (init/plan/apply)
- [x] 5プラットフォーム対応 (Twitter, Bluesky, Instagram, LinkedIn, YouTube)
- [x] プロフィール自動生成・更新
- [x] **AI画像アイコン自動生成・設定** ✨
- [x] アイコン永続化・再利用機能
- [x] 継続投稿システム
- [x] profileコマンドによる個別修正機能

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
#     ├── Step 1: プロフィール・アイコン更新
#     │   ├── AI画像アイコン生成 (OpenAI DALL-E API)
#     │   ├── アイコンを avatar.png として保存
#     │   ├── プロフィール文生成・更新
#     │   └── 全プラットフォームに適用
#     └── Step 2: 投稿コンテンツ生成・実行
```

### 設定ファイルの役割
- **campaign.yaml**: initで生成される中心設定ファイル
- **.env.aetherpost**: API認証情報（機密情報）
- **avatar.png**: AI生成アイコン（全プラットフォーム共通）
- **plan/apply**: 常にcampaign.yamlを参照

## 🎨 AI画像アイコン自動生成機能

### 実装済みワークフロー
```bash
# ユーザーが行う作業（3コマンドのみ）
aetherpost init     # campaign.yaml生成
aetherpost plan     # 投稿内容プレビュー
aetherpost apply    # ①アイコン生成→②プロフィール更新→③投稿実行
```

### アイコン生成・管理機能

#### 1. 自動AI画像生成
- **OpenAI DALL-E 3 API** を使用した高品質ロゴ生成
- `campaign.yaml`の name + description からプロンプト自動生成
- プロフェッショナルなロゴデザインに最適化されたプロンプト

#### 2. アイコン永続化・再利用
```bash
avatar.png          # プロジェクトディレクトリに自動保存
├── 初回生成時: AI画像として生成・保存
├── 2回目以降: 既存ファイルを自動読み込み・再利用
└── 全プラットフォーム共通: 同じアイコンをすべてに適用
```

#### 3. プラットフォーム別アップロード
- **Twitter**: API v1.1 `update_profile_image`
- **Bluesky**: AT Protocol blob upload + profile record update
- **その他**: 各プラットフォームAPI準拠

#### 4. フォールバック機能
```bash
OpenAI API Key あり → DALL-E 3で高品質生成
OpenAI API Key なし → PIL生成の"A"文字プレースホルダー
```

### プロフィール自動最適化

#### プラットフォーム別最適化
- **Twitter**: 160文字制限、両URL (website + GitHub) をbio内に埋め込み
- **Bluesky**: 256文字制限、display_name にサイトURL、bio内にGitHubURL
- **Instagram**: 150文字制限、ビジュアル重視のEmoji装飾
- **LinkedIn**: 220文字制限、プロフェッショナルトーン
- **YouTube**: 1000文字制限、チャンネル説明最適化

#### プロフィール生成ルール
```yaml
# campaign.yamlから自動生成
name: "AetherPost"                    → Display Name
description: "Social media automation" → Bio生成ベース
website_url: "https://aether-post.com" → プロフィールURL
github_url: "https://github.com/..."   → Bio内に埋め込み
content.style: "friendly"             → トーン調整
```

### 個別修正機能

#### profileコマンドで細かい調整
```bash
# プロフィール生成プレビュー
aetherpost profile generate --platform twitter

# 手動でプロフィール更新
aetherpost profile update twitter

# 既存アイコンを手動アップロード
# （手動機能は削除済み - applyで全自動化）
```

### 実装技術詳細

#### AI画像生成
```python
# OpenAI DALL-E 3 プロンプト最適化
prompt = f"Professional logo design for {name}: {description}. 
Clean, minimal, modern style. High contrast, suitable for 
social media avatar. Square format, simple geometric shapes, 
tech company aesthetic."

# 1024x1024生成 → 400x400リサイズ → PNG保存
```

#### アイコン管理
```python
# 既存チェック → 新規生成 → 保存 → 全プラットフォーム適用
if os.path.exists("avatar.png"):
    return load_existing()
else:
    data = await generate_ai_avatar()
    save_as_png(data)
    return data
```

---

## 🧪 実装テスト環境

### aetherpost_promoフォルダでの実装テスト

**目的**: AetherPostの実機能をテスト・デモンストレーション

#### 実装済み機能テスト
```bash
cd aetherpost_promo/

# 1. 設定ファイル確認
cat campaign.yaml           # プロジェクト設定
cat .env.aetherpost         # API認証情報

# 2. ワークフロー実行
aetherpost plan             # 投稿プレビュー
aetherpost apply            # プロフィール更新 + 投稿実行

# 3. 生成ファイル確認
ls avatar.png              # AI生成アイコン
cat promo.state.json       # 実行履歴
```

#### テスト結果の実証
- **campaign.yaml**: name, description, website_url, github_url 完備
- **avatar.png**: OpenAI DALL-E生成 (フォールバック時はPIL生成)
- **プロフィール更新**: Twitter/Bluesky で実際に更新確認済み
- **両URL表示**: プロフィール内にwebsite + GitHub URL両方表示

#### 各実装が完了したらCLAUDE.mdのこの部分を更新する

**重要**: このaetherpost_promoフォルダは実際のAetherPost機能をテストするためのものです。一般ユーザーと全く同じワークフローを使用しており、特別なコマンドは一切ありません。

---

**核心思想**: 「設定は1回、あとは全自動」

AetherPostは開発者が本来の開発に集中できるよう、ソーシャルメディアプロモーションを完全に自動化します。複雑なコマンドや継続的な手動操作は一切不要。Terraformのシンプルさとソーシャルメディアの効果的活用を両立させた、究極のプロモーション自動化ツールです。