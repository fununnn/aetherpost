#!/usr/bin/env python3
"""Debug real integration - 実際のプラットフォーム反映確認"""

import sys
import asyncio
import os
from pathlib import Path

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def debug_twitter_authentication():
    """Twitter認証の詳細デバッグ"""
    print("🐦 Deep Twitter Authentication Debug...")
    
    try:
        from platforms.implementations.twitter_platform import TwitterPlatform
        
        # 認証情報読み込み
        credentials = {}
        env_path = "/home/ubuntu/doc/autopromo/test_workspace/.env.aetherpost"
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()
        
        twitter_creds = {
            "api_key": credentials.get("TWITTER_API_KEY"),
            "api_secret": credentials.get("TWITTER_API_SECRET"),
            "access_token": credentials.get("TWITTER_ACCESS_TOKEN"),
            "access_token_secret": credentials.get("TWITTER_ACCESS_TOKEN_SECRET")
        }
        
        print(f"🔑 認証情報確認:")
        print(f"   API Key: {twitter_creds['api_key'][:10]}...")
        print(f"   API Secret: {twitter_creds['api_secret'][:10]}...")
        print(f"   Access Token: {twitter_creds['access_token'][:10]}...")
        print(f"   Access Token Secret: {twitter_creds['access_token_secret'][:10]}...")
        
        # プラットフォーム作成
        platform = TwitterPlatform(twitter_creds)
        
        # 詳細認証テスト
        print("🔄 認証実行...")
        auth_result = await platform.authenticate()
        
        print(f"認証結果: {auth_result}")
        
        if auth_result:
            print("✅ 認証成功 - 実際のAPI呼び出しテスト...")
            
            # 実際のAPIテスト（ユーザー情報取得）
            try:
                # ここで実際のTwitter APIを呼び出してユーザー情報を取得
                if hasattr(platform, '_verify_credentials'):
                    user_info = await platform._verify_credentials()
                    print(f"📊 ユーザー情報: {user_info}")
                else:
                    print("⚠️  _verify_credentials メソッドが存在しません")
                    
            except Exception as e:
                print(f"❌ API呼び出しエラー: {e}")
        
        else:
            print("❌ 認証失敗")
        
        await platform.cleanup()
        return auth_result
        
    except Exception as e:
        print(f"❌ Twitter認証デバッグ失敗: {e}")
        return False

async def debug_bluesky_authentication():
    """Bluesky認証の詳細デバッグ"""
    print("\n🦋 Deep Bluesky Authentication Debug...")
    
    try:
        from platforms.implementations.bluesky_platform import BlueskyPlatform
        
        # 認証情報読み込み
        credentials = {}
        env_path = "/home/ubuntu/doc/autopromo/test_workspace/.env.aetherpost"
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()
        
        bluesky_creds = {
            "identifier": credentials.get("BLUESKY_IDENTIFIER"),
            "password": credentials.get("BLUESKY_PASSWORD")
        }
        
        print(f"🔑 認証情報確認:")
        print(f"   Identifier: {bluesky_creds['identifier']}")
        print(f"   Password: {bluesky_creds['password'][:5]}...")
        
        # プラットフォーム作成
        platform = BlueskyPlatform(bluesky_creds)
        
        # 詳細認証テスト
        print("🔄 認証実行...")
        auth_result = await platform.authenticate()
        
        print(f"認証結果: {auth_result}")
        
        if auth_result:
            print("✅ 認証成功")
        else:
            print("❌ 認証失敗")
        
        await platform.cleanup()
        return auth_result
        
    except Exception as e:
        print(f"❌ Bluesky認証デバッグ失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_real_profile_update():
    """実際のプロフィール更新テスト"""
    print("\n👤 Real Profile Update Test...")
    
    try:
        from platforms.core.platform_factory import platform_factory
        from platforms.core.base_platform import Profile
        
        # 認証情報読み込み
        credentials = {}
        env_path = "/home/ubuntu/doc/autopromo/test_workspace/.env.aetherpost"
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()
        
        # Twitter プロフィール更新テスト
        print("🐦 Twitter プロフィール更新...")
        
        twitter_creds = {
            "api_key": credentials.get("TWITTER_API_KEY"),
            "api_secret": credentials.get("TWITTER_API_SECRET"),
            "access_token": credentials.get("TWITTER_ACCESS_TOKEN"),
            "access_token_secret": credentials.get("TWITTER_ACCESS_TOKEN_SECRET")
        }
        
        twitter_platform = platform_factory.create_platform(
            platform_name="twitter",
            credentials=twitter_creds
        )
        
        # 認証
        if await twitter_platform.authenticate():
            # テスト用プロフィール作成
            test_profile = Profile(
                display_name="AetherPost",
                bio="🚀 Social media automation for developers | Testing AetherPost integration | https://aether-post.com",
                website_url="https://aether-post.com",
                avatar_path="avatar.png" if os.path.exists("avatar.png") else None
            )
            
            print(f"📝 更新するプロフィール:")
            print(f"   名前: {test_profile.display_name}")
            print(f"   Bio: {test_profile.bio}")
            print(f"   Website: {test_profile.website_url}")
            print(f"   Avatar: {test_profile.avatar_path}")
            
            # 実際にプロフィール更新実行
            result = await twitter_platform.update_profile(test_profile)
            
            print(f"🔄 更新結果: {result}")
            
            if result and result.success:
                print("✅ Twitter プロフィール更新成功！")
                return True
            else:
                print(f"❌ Twitter プロフィール更新失敗: {result.error_message if result else 'Unknown error'}")
                
        else:
            print("❌ Twitter 認証失敗")
        
        await twitter_platform.cleanup()
        return False
        
    except Exception as e:
        print(f"❌ プロフィール更新テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_real_post_creation():
    """実際の投稿作成テスト"""
    print("\n📝 Real Post Creation Test...")
    
    try:
        from platforms.core.platform_factory import platform_factory
        from platforms.core.base_platform import Content, ContentType
        
        # 認証情報読み込み
        credentials = {}
        env_path = "/home/ubuntu/doc/autopromo/test_workspace/.env.aetherpost"
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()
        
        # Twitter 投稿テスト
        print("🐦 Twitter 投稿作成...")
        
        twitter_creds = {
            "api_key": credentials.get("TWITTER_API_KEY"),
            "api_secret": credentials.get("TWITTER_API_SECRET"),
            "access_token": credentials.get("TWITTER_ACCESS_TOKEN"),
            "access_token_secret": credentials.get("TWITTER_ACCESS_TOKEN_SECRET")
        }
        
        twitter_platform = platform_factory.create_platform(
            platform_name="twitter",
            credentials=twitter_creds
        )
        
        # 認証
        if await twitter_platform.authenticate():
            # テスト投稿作成
            test_content = Content(
                content_type=ContentType.TEXT,
                text="🚀 Testing AetherPost integration! Social media automation for developers is working! #automation #developers #test",
                hashtags=["#automation", "#developers", "#test"]
            )
            
            print(f"📝 投稿内容:")
            print(f"   テキスト: {test_content.text}")
            print(f"   文字数: {len(test_content.text)}")
            print(f"   ハッシュタグ: {test_content.hashtags}")
            
            # 実際に投稿実行
            result = await twitter_platform.post_content(test_content)
            
            print(f"🔄 投稿結果: {result}")
            
            if result and result.success:
                print(f"✅ Twitter 投稿成功！投稿ID: {result.post_id}")
                return True
            else:
                print(f"❌ Twitter 投稿失敗: {result.error_message if result else 'Unknown error'}")
                
        else:
            print("❌ Twitter 認証失敗")
        
        await twitter_platform.cleanup()
        return False
        
    except Exception as e:
        print(f"❌ 投稿作成テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """実際の統合デバッグ実行"""
    print("🔍 **AetherPost Real Integration Debug**")
    print("=" * 50)
    print("実際のプラットフォーム反映を詳細デバッグ\n")
    
    # ワーキングディレクトリ変更
    os.chdir("/home/ubuntu/doc/autopromo/test_workspace")
    
    # 段階的テスト実行
    tests = [
        ("Twitter認証詳細確認", debug_twitter_authentication),
        ("Bluesky認証詳細確認", debug_bluesky_authentication),
        ("実際のプロフィール更新", test_real_profile_update),
        ("実際の投稿作成", test_real_post_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name}: SUCCESS")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Debug Results: {passed}/{total} passed")
    
    if passed == 0:
        print("🚨 実際のプラットフォーム反映に問題があります。実装を確認する必要があります。")
    elif passed < total:
        print("⚠️  一部機能に問題があります。詳細を確認して修正が必要です。")
    else:
        print("🎉 全ての機能が実際のプラットフォームで動作しています！")
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))