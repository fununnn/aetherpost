#!/usr/bin/env python3
"""Test script for platform implementations."""

import sys
import asyncio
from pathlib import Path

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def test_platform_creation():
    """Test platform instance creation."""
    print("🏗️ Testing platform instance creation...")
    
    try:
        from platforms.core.platform_factory import platform_factory
        
        # Test credentials for each platform
        test_credentials = {
            "twitter": {
                "api_key": "test_key",
                "api_secret": "test_secret",
                "access_token": "test_token",
                "access_token_secret": "test_token_secret"
            },
            "bluesky": {
                "identifier": "test.bsky.social",
                "password": "test_password"
            },
            "instagram": {
                "access_token": "test_token",
                "instagram_account_id": "test_account_id"
            },
            "linkedin": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "access_token": "test_token"
            },
            "youtube": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "access_token": "test_token",
                "refresh_token": "test_refresh_token"
            }
        }
        
        platforms_tested = []
        
        for platform_name, credentials in test_credentials.items():
            try:
                platform_instance = platform_factory.create_platform(
                    platform_name=platform_name,
                    credentials=credentials
                )
                
                print(f"✅ {platform_name}: インスタンス作成成功")
                platforms_tested.append(platform_name)
                
                # クリーンアップ
                if hasattr(platform_instance, 'cleanup'):
                    await platform_instance.cleanup()
                    
            except Exception as e:
                print(f"❌ {platform_name}: インスタンス作成失敗 - {e}")
        
        print(f"✅ テスト完了: {len(platforms_tested)}/5 プラットフォーム")
        return len(platforms_tested) == 5
        
    except Exception as e:
        print(f"❌ プラットフォームテスト失敗: {e}")
        return False

async def test_platform_capabilities():
    """Test platform capabilities."""
    print("\n🎯 Testing platform capabilities...")
    
    try:
        from platforms.core.platform_registry import platform_registry
        
        platforms = platform_registry.get_available_platforms()
        
        for platform_name in platforms:
            platform_info = platform_registry.get_platform_info(platform_name)
            
            if platform_info and 'error' not in platform_info:
                capabilities = platform_info.get('capabilities', [])
                content_types = platform_info.get('supported_content_types', [])
                
                print(f"✅ {platform_name}:")
                print(f"   - 機能: {', '.join(capabilities[:3])}{'...' if len(capabilities) > 3 else ''}")
                print(f"   - コンテンツ: {', '.join(content_types[:3])}{'...' if len(content_types) > 3 else ''}")
            else:
                print(f"❌ {platform_name}: 情報取得失敗")
        
        return True
        
    except Exception as e:
        print(f"❌ プラットフォーム機能テスト失敗: {e}")
        return False

async def test_authentication_methods():
    """Test authentication method availability."""
    print("\n🔐 Testing authentication methods...")
    
    try:
        from platforms.implementations.twitter_platform import TwitterPlatform
        from platforms.implementations.bluesky_platform import BlueskyPlatform
        from platforms.implementations.instagram_platform import InstagramPlatform
        from platforms.implementations.linkedin_platform import LinkedInPlatform
        from platforms.implementations.youtube_platform import YouTubePlatform
        
        platforms = [
            ("Twitter", TwitterPlatform),
            ("Bluesky", BlueskyPlatform), 
            ("Instagram", InstagramPlatform),
            ("LinkedIn", LinkedInPlatform),
            ("YouTube", YouTubePlatform)
        ]
        
        for name, platform_class in platforms:
            try:
                # 認証メソッドの存在確認
                if hasattr(platform_class, 'authenticate'):
                    print(f"✅ {name}: authenticate メソッド有り")
                else:
                    print(f"❌ {name}: authenticate メソッド無し")
                    
                # 認証設定の確認
                if hasattr(platform_class, '__init__'):
                    print(f"✅ {name}: 初期化メソッド有り")
                else:
                    print(f"❌ {name}: 初期化メソッド無し")
                    
            except Exception as e:
                print(f"❌ {name}: 認証テスト失敗 - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 認証メソッドテスト失敗: {e}")
        return False

async def test_content_posting_interface():
    """Test content posting interface."""
    print("\n📝 Testing content posting interface...")
    
    try:
        from platforms.core.platform_factory import platform_factory
        from platforms.core.base_platform import Content, ContentType
        
        # テスト用コンテンツ
        test_content = Content(
            content_type=ContentType.TEXT,
            text="Test post content",
            media=[],
            hashtags=["#test"],
            platform_data={}
        )
        
        test_credentials_mapping = {
            "twitter": {
                "api_key": "test",
                "api_secret": "test", 
                "access_token": "test",
                "access_token_secret": "test"
            },
            "bluesky": {
                "identifier": "test.bsky.social",
                "password": "test_password"
            },
            "instagram": {
                "access_token": "test_token",
                "instagram_account_id": "test_account_id"
            },
            "linkedin": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "access_token": "test_token"
            },
            "youtube": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "access_token": "test_token",
                "refresh_token": "test_refresh_token"
            }
        }
        
        platforms_with_posting = []
        
        for platform_name in ["twitter", "bluesky", "instagram", "linkedin", "youtube"]:
            try:
                platform_credentials = test_credentials_mapping.get(platform_name, {})
                platform_instance = platform_factory.create_platform(
                    platform_name=platform_name,
                    credentials=platform_credentials
                )
                
                # 投稿インターフェースの確認
                if hasattr(platform_instance, 'post_content'):
                    print(f"✅ {platform_name}: post_content メソッド有り")
                    platforms_with_posting.append(platform_name)
                else:
                    print(f"❌ {platform_name}: post_content メソッド無し")
                
                # クリーンアップ
                if hasattr(platform_instance, 'cleanup'):
                    await platform_instance.cleanup()
                    
            except Exception as e:
                print(f"❌ {platform_name}: 投稿インターフェーステスト失敗 - {e}")
        
        print(f"✅ 投稿機能: {len(platforms_with_posting)}/5 プラットフォーム")
        return len(platforms_with_posting) == 5
        
    except Exception as e:
        print(f"❌ 投稿インターフェーステスト失敗: {e}")
        return False

async def main():
    """Run all platform tests."""
    print("🧪 AetherPost Platform Integration Tests\n")
    
    tests = [
        test_platform_creation,
        test_platform_capabilities,
        test_authentication_methods,
        test_content_posting_interface
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ テスト例外発生: {e}")
    
    print(f"\n📊 プラットフォームテスト結果: {passed}/{total} 成功 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 全プラットフォームテスト成功!")
        return 0
    else:
        print("❌ 一部プラットフォームテスト失敗")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))