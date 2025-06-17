# AetherPost GitHub Releases 配布戦略

## 戦略比較

### 方法A: 新規リポジトリ作成 ⭐ **推奨**

**メリット:**
- 完全にクリーンな履歴
- [AI Service] Code痕跡の完全除去
- プロフェッショナルな印象
- 法的リスクの最小化

**デメリット:**
- スター数・フォーク数のリセット
- SEO・検索履歴の喪失
- 既存リンクの無効化

**実装手順:**
```bash
# 1. 新規リポジトリ作成
gh repo create your-org/aetherpost-official --public

# 2. クリーンアップ済みコードをプッシュ
cd aetherpost-release
git init
git add .
git commit -m "Initial release: AetherPost v1.0.0"
git remote add origin https://github.com/your-org/aetherpost-official.git
git push -u origin main

# 3. 最初のリリース作成  
gh release create v1.0.0 --title "AetherPost v1.0.0" --notes "First official release"
```

### 方法B: 現リポジトリのクリーン化

**メリット:**
- スター数・履歴の継承
- 既存リンクの維持
- SEO効果の継続

**デメリット:**
- 技術的リスク（履歴破損の可能性）
- Claude参照の完全除去が困難
- 法的グレーゾーン

**実装手順:**
```bash
# ⚠️ 危険：実行前に必ずバックアップ

# 1. BFGでClaude参照を履歴から除去
java -jar bfg.jar --replace-text [AI Service]-references.txt .git

# 2. Git filter-branchで特定ファイルを履歴から削除
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch docs/[AI Service]-CODE.md' \
  --prune-empty --tag-name-filter cat -- --all

# 3. 強制プッシュ（破壊的）
git push --force --all
git push --force --tags
```

### 方法C: サブディレクトリ抽出

**メリット:**
- 部分的なクリーン履歴
- 必要な部分のみ抽出可能

**デメリット:**
- 複雑な作業
- 依存関係の管理が困難

## 有料化モデル

### 段階的有料化戦略

#### Phase 1: オープンソース版（OSS Edition）
- **価格**: 無料
- **制限**: 
  - 50投稿/日
  - 3プラットフォーム
  - 5キャンペーン
  - 基本分析のみ
- **目的**: ユーザー獲得・ブランド構築

#### Phase 2: プロフェッショナル版
- **価格**: $29/月
- **機能**:
  - 無制限投稿
  - 全プラットフォーム対応
  - 高度な分析
  - AI最適化
  - メール支援

#### Phase 3: エンタープライズ版
- **価格**: $99/月
- **機能**:
  - チーム管理
  - API access
  - カスタム統合
  - 専用支援
  - SLA保証

### 技術的実装

```python
# aetherpost/core/edition.py
class EditionManager:
    def __init__(self):
        self.edition = self._detect_edition()
    
    def _detect_edition(self):
        # ライセンスキー検出
        if os.getenv('AETHERPOST_LICENSE_KEY'):
            return 'enterprise'
        elif os.path.exists('.aetherpost/pro.license'):
            return 'professional'
        else:
            return 'oss'
    
    def check_limits(self, feature: str) -> bool:
        limits = {
            'oss': {
                'daily_posts': 50,
                'platforms': 3,
                'campaigns': 5
            },
            'professional': {},  # 無制限
            'enterprise': {}     # 無制限
        }
        
        current_limits = limits.get(self.edition, {})
        return self._check_feature_limit(feature, current_limits)
```

## 実装スケジュール

### Week 1: 痕跡除去
- [ ] [AI Service] Code参照の完全スキャン
- [ ] 自動化スクリプト実行
- [ ] 手動検証・修正
- [ ] 法的レビュー

### Week 2: リポジトリ準備
- [ ] 新規リポジトリ作成
- [ ] README/ドキュメント整備
- [ ] ライセンス条項確認
- [ ] CI/CD設定

### Week 3: 有料化機能実装
- [ ] ライセンス検証システム
- [ ] 使用量制限実装
- [ ] 課金システム統合
- [ ] テスト実施

### Week 4: リリース
- [ ] GitHub Releases設定
- [ ] マーケティング資料準備
- [ ] 公式ドキュメント
- [ ] ローンチ実行

## リスク管理

### 法的リスク
- **対策**: 独立した著作権表示
- **検証**: 法的レビューの実施
- **保険**: 適切なライセンス条項

### 技術的リスク
- **対策**: 段階的移行
- **検証**: 徹底したテスト
- **回復**: 完全バックアップ

### 市場リスク
- **対策**: 無料版の継続提供
- **検証**: ユーザーフィードバック
- **調整**: 価格戦略の柔軟性

## 成功指標

### 短期目標（3ヶ月）
- OSS版: 1,000 GitHub stars
- Pro版: 50 paying customers
- 月間收益: $1,500

### 長期目標（1年）
- OSS版: 5,000 GitHub stars
- Pro版: 200 paying customers
- Enterprise版: 10 paying customers
- 月間收益: $10,000