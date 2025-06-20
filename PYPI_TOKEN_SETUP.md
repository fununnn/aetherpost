# PyPI API Token Setup Guide

## 1. PyPI Token 取得

### Web UI で取得
1. https://pypi.org にアクセス
2. アカウントでログイン
3. Account settings → API tokens
4. "Add API token" をクリック
5. Token name: `aetherpost-release`
6. Scope: `Entire account` (または `aetherpost` プロジェクト限定)
7. "Add token" をクリック
8. 表示されたトークンをコピー（一度しか表示されません）

### トークン設定
```bash
# 環境変数として設定
export PYPI_API_TOKEN="pypi-XXXXXXXXXXXXXXXXXXXXXXXX"

# または .pypirc ファイルに設定
cat > ~/.pypirc << EOF
[distutils]
index-servers = pypi

[pypi]
username = __token__
password = pypi-XXXXXXXXXXXXXXXXXXXXXXXX
EOF
```

### PyPI アップロード実行
```bash
# 環境変数使用
python -m twine upload dist/* --username __token__ --password "$PYPI_API_TOKEN"

# または .pypirc 使用  
python -m twine upload dist/*
```

## 2. 現在の配布パッケージ確認
```bash
ls -la dist/
# aetherpost-1.5.0-py3-none-any.whl
# aetherpost-1.5.0.tar.gz

# パッケージ検証
python -m twine check dist/*
```

## 3. アップロード後確認
```bash
# インストールテスト
pip install aetherpost==1.5.0

# バージョン確認
python -c "import aetherpost; print(aetherpost.__version__)"
```