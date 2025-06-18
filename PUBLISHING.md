# 📦 AetherPost PyPI公開ガイド

## 🔧 事前準備

### 1. PyPI アカウント設定
```bash
# PyPI と TestPyPI にアカウント作成
# https://pypi.org/account/register/
# https://test.pypi.org/account/register/

# API Token を取得し、~/.pypirc に設定
cat > ~/.pypirc << EOF
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_API_TOKEN_HERE
EOF
```

### 2. 公開ツールのインストール
```bash
pip install --upgrade pip
pip install --upgrade build twine
```

## 🚀 公開手順

### 1. バージョン確認
```bash
# 以下のファイルのバージョンが一致していることを確認
grep version setup.py
grep version pyproject.toml
grep __version__ aetherpost/__init__.py
```

### 2. ビルド
```bash
# クリーンビルド
rm -rf dist/ build/ *.egg-info/

# パッケージビルド
python -m build

# 生成されたファイルを確認
ls -la dist/
# aetherpost-1.1.0-py3-none-any.whl
# aetherpost-1.1.0.tar.gz
```

### 3. TestPyPI でテスト
```bash
# TestPyPI にアップロード
python -m twine upload --repository testpypi dist/*

# TestPyPI からインストールテスト
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ aetherpost==1.1.0

# 動作確認
aetherpost --version
aetherpost --help
```

### 4. 本番PyPI公開
```bash
# 本番 PyPI にアップロード
python -m twine upload dist/*

# 公開確認
pip install aetherpost==1.1.0
```

## 🔍 検証チェックリスト

### 公開前チェック
- [ ] バージョンが全ファイルで一致
- [ ] README.md が最新
- [ ] LICENSE ファイルが存在
- [ ] requirements-oss.txt が正しい
- [ ] Git タグが作成済み
- [ ] GitHub に変更がプッシュ済み

### 公開後チェック
- [ ] PyPI ページが正しく表示
- [ ] `pip install aetherpost` が成功
- [ ] インストール後の動作確認
- [ ] ドキュメントリンクが有効
- [ ] GitHub リポジトリリンクが有効

## 🚨 トラブルシューティング

### よくある問題
1. **バージョン重複エラー**
   ```bash
   # バージョンを上げて再試行
   # setup.py, pyproject.toml, aetherpost/__init__.py を更新
   ```

2. **パッケージが見つからない**
   ```bash
   # パッケージ構造を確認
   python -c "import aetherpost; print(aetherpost.__version__)"
   ```

3. **依存関係エラー**
   ```bash
   # requirements-oss.txt の内容を確認
   # setup.py の install_requires を確認
   ```

## 📝 自動化案

### GitHub Actions での自動公開
```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@v1.8.10
      with:
        user: __token__
        password: ${{ secrets.PYPI_API_TOKEN }}
```

## 🎯 次回リリース用コマンド

```bash
# 次回バージョンアップ時のワンライナー
VERSION="1.2.0"
sed -i "s/version = \".*\"/version = \"$VERSION\"/" setup.py pyproject.toml
sed -i "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" aetherpost/__init__.py
git add setup.py pyproject.toml aetherpost/__init__.py
git commit -m "Bump version to $VERSION"
git tag "v$VERSION"
```

---

**注意**: 本番公開前に必ずTestPyPIでテストしてください！