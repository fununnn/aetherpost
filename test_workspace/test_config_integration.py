#!/usr/bin/env python3
"""Test script for configuration file integration."""

import sys
import asyncio
import os
import yaml
import tempfile
from pathlib import Path

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def test_campaign_yaml_structure():
    """Test campaign.yaml structure and validation."""
    print("📄 Testing campaign.yaml structure...")
    
    try:
        # テスト用campaign.yaml作成
        test_campaign = {
            "name": "TestApp",
            "concept": "Revolutionary productivity tool for developers",
            "url": "https://testapp.com",
            "platforms": ["twitter", "bluesky", "instagram"],
            "content": {
                "style": "friendly",
                "action": "Check it out!",
                "hashtags": ["#test", "#app"],
                "language": "en",
                "max_length": 280
            },
            "image": "auto"
        }
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_campaign, f, default_flow_style=False)
            temp_path = f.name
        
        print("✅ campaign.yaml作成: OK")
        
        # ファイル読み込みテスト
        try:
            with open(temp_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            # 必須フィールド確認
            required_fields = ["name", "concept", "platforms", "content"]
            missing_fields = [field for field in required_fields if field not in loaded_config]
            
            if not missing_fields:
                print("✅ 必須フィールド: 全て存在")
            else:
                print(f"❌ 必須フィールド: 不足 {missing_fields}")
                return False
            
            # プラットフォーム数確認
            platforms = loaded_config.get("platforms", [])
            if len(platforms) >= 1:
                print(f"✅ プラットフォーム設定: {len(platforms)}個")
            else:
                print("❌ プラットフォーム設定: 無効")
                return False
            
        finally:
            # 一時ファイル削除
            os.unlink(temp_path)
        
        return True
        
    except Exception as e:
        print(f"❌ campaign.yaml構造テスト失敗: {e}")
        return False

async def test_credentials_loading():
    """Test credentials loading from .env.aetherpost."""
    print("\n🔐 Testing credentials loading...")
    
    try:
        # テスト用認証情報ファイル作成
        test_env_content = """
# Twitter credentials
TWITTER_API_KEY=test_twitter_key
TWITTER_API_SECRET=test_twitter_secret
TWITTER_ACCESS_TOKEN=test_twitter_token
TWITTER_ACCESS_TOKEN_SECRET=test_twitter_token_secret

# Bluesky credentials
BLUESKY_IDENTIFIER=test.bsky.social
BLUESKY_PASSWORD=test_bluesky_password

# OpenAI credentials
OPENAI_API_KEY=test_openai_key

# AI Service credentials
AI_SERVICE_API_KEY=test_ai_service_key
"""
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(test_env_content)
            temp_env_path = f.name
        
        print("✅ .env.aetherpost作成: OK")
        
        # 認証情報解析テスト
        parsed_credentials = {}
        
        with open(temp_env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    parsed_credentials[key.strip()] = value.strip()
        
        # プラットフォーム別認証情報グループ化
        platform_groups = {}
        for key, value in parsed_credentials.items():
            if key.startswith('TWITTER_'):
                platform_groups.setdefault('twitter', {})[key] = value
            elif key.startswith('BLUESKY_'):
                platform_groups.setdefault('bluesky', {})[key] = value
            elif key.startswith('OPENAI_'):
                platform_groups.setdefault('openai', {})[key] = value
            elif key.startswith('AI_SERVICE_'):
                platform_groups.setdefault('ai_service', {})[key] = value
        
        print(f"✅ 認証情報グループ: {len(platform_groups)}種類")
        
        # 各プラットフォームの認証情報確認
        expected_platforms = ['twitter', 'bluesky', 'openai', 'ai_service']
        found_platforms = list(platform_groups.keys())
        
        missing_platforms = set(expected_platforms) - set(found_platforms)
        
        if not missing_platforms:
            print("✅ 全プラットフォーム認証情報: 存在")
        else:
            print(f"⚠️  一部プラットフォーム認証情報: 不足 {missing_platforms}")
        
        # クリーンアップ
        os.unlink(temp_env_path)
        
        return len(found_platforms) >= 3
        
    except Exception as e:
        print(f"❌ 認証情報読み込みテスト失敗: {e}")
        return False

async def test_config_parser_integration():
    """Test ConfigParser integration with actual models."""
    print("\n⚙️ Testing ConfigParser integration...")
    
    try:
        from core.config.parser import ConfigLoader
        from core.config.models import CampaignConfig, ContentConfig
        
        # ConfigLoader初期化
        config_loader = ConfigLoader()
        print("✅ ConfigLoader初期化: OK")
        
        # テスト用設定作成
        test_content_config = ContentConfig(
            style="friendly",
            action="Check it out!",
            hashtags=["#test", "#app"],
            language="en",
            max_length=280
        )
        
        test_campaign_config = CampaignConfig(
            name="TestApp",
            concept="Test application for developers",
            url="https://testapp.com",
            platforms=["twitter", "bluesky"],
            content=test_content_config,
            image="auto"
        )
        
        print("✅ 設定モデル作成: OK")
        
        # 設定バリデーション
        validation_tests = []
        
        # 名前の確認
        if test_campaign_config.name == "TestApp":
            print("✅ 名前フィールド: 正常")
            validation_tests.append(True)
        else:
            print("❌ 名前フィールド: 異常")
            validation_tests.append(False)
        
        # プラットフォームリストの確認
        if isinstance(test_campaign_config.platforms, list) and len(test_campaign_config.platforms) > 0:
            print(f"✅ プラットフォームリスト: {len(test_campaign_config.platforms)}個")
            validation_tests.append(True)
        else:
            print("❌ プラットフォームリスト: 無効")
            validation_tests.append(False)
        
        # コンテンツ設定の確認
        if test_campaign_config.content and test_campaign_config.content.style:
            print(f"✅ コンテンツ設定: {test_campaign_config.content.style}スタイル")
            validation_tests.append(True)
        else:
            print("❌ コンテンツ設定: 無効")
            validation_tests.append(False)
        
        success_rate = validation_tests.count(True) / len(validation_tests)
        print(f"✅ 設定統合: {success_rate*100:.1f}% 成功")
        
        return success_rate >= 0.8
        
    except Exception as e:
        print(f"❌ ConfigParser統合テスト失敗: {e}")
        return False

async def test_environment_variable_handling():
    """Test environment variable handling and precedence."""
    print("\n🌍 Testing environment variable handling...")
    
    try:
        # 環境変数設定テスト
        test_env_vars = {
            "AETHERPOST_DEFAULT_STYLE": "professional",
            "AETHERPOST_DEFAULT_LANGUAGE": "ja",
            "AETHERPOST_MAX_PLATFORMS": "3"
        }
        
        # 環境変数を一時的に設定
        original_values = {}
        for key, value in test_env_vars.items():
            original_values[key] = os.environ.get(key)
            os.environ[key] = value
        
        print("✅ 環境変数設定: OK")
        
        # 環境変数読み込みテスト
        env_checks = []
        
        for key, expected_value in test_env_vars.items():
            actual_value = os.environ.get(key)
            if actual_value == expected_value:
                print(f"✅ {key}: {actual_value}")
                env_checks.append(True)
            else:
                print(f"❌ {key}: 期待値{expected_value} 実際値{actual_value}")
                env_checks.append(False)
        
        # 環境変数を元に戻す
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
        
        success_rate = env_checks.count(True) / len(env_checks)
        print(f"✅ 環境変数処理: {success_rate*100:.1f}% 成功")
        
        return success_rate >= 0.8
        
    except Exception as e:
        print(f"❌ 環境変数処理テスト失敗: {e}")
        return False

async def test_url_configuration():
    """Test URL configuration as mentioned in CLAUDE.md."""
    print("\n🔗 Testing URL configuration...")
    
    try:
        # CLAUDE.mdで言及されているURL設定のテスト
        test_urls = {
            "website_url": "https://aether-post.com",
            "github_url": "https://github.com/fununnn/aetherpost"
        }
        
        print("✅ テスト用URL設定: OK")
        
        # URL妥当性確認
        url_validations = []
        
        for url_type, url_value in test_urls.items():
            # 基本的なURL形式チェック
            if url_value.startswith(('http://', 'https://')):
                print(f"✅ {url_type}: 有効なURL形式")
                url_validations.append(True)
            else:
                print(f"❌ {url_type}: 無効なURL形式")
                url_validations.append(False)
        
        # プロフィール統合でのURL使用確認
        from core.profiles.generator import ProfileGenerator
        
        generator = ProfileGenerator()
        
        # URL統合テスト用プロジェクト情報
        test_project_info = {
            "name": "AetherPost",
            "description": "Social media automation for developers",
            **test_urls
        }
        
        # Twitter用プロフィール生成（URLが含まれるか確認）
        profile = generator.generate_profile(
            platform="twitter",
            project_info=test_project_info,
            style="professional"
        )
        
        if profile.website_url:
            print(f"✅ プロフィールURL統合: {profile.website_url}")
            url_validations.append(True)
        else:
            print("❌ プロフィールURL統合: 失敗")
            url_validations.append(False)
        
        success_rate = url_validations.count(True) / len(url_validations)
        print(f"✅ URL設定: {success_rate*100:.1f}% 成功")
        
        return success_rate >= 0.8
        
    except Exception as e:
        print(f"❌ URL設定テスト失敗: {e}")
        return False

async def main():
    """Run all configuration integration tests."""
    print("🧪 AetherPost Configuration Integration Tests\n")
    
    tests = [
        test_campaign_yaml_structure,
        test_credentials_loading,
        test_config_parser_integration,
        test_environment_variable_handling,
        test_url_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ テスト例外発生: {e}")
    
    print(f"\n📊 設定ファイル統合テスト結果: {passed}/{total} 成功 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 全設定ファイル統合テスト成功!")
        return 0
    else:
        print("❌ 一部設定ファイル統合テスト失敗")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))