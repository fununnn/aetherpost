#!/usr/bin/env python3
"""Twitterアイコン更新専用テスト"""

import sys
import asyncio
import os
from pathlib import Path

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def test_twitter_avatar_update():
    """Twitterアイコン更新の詳細テスト"""
    print("🐦 **Twitter アイコン更新詳細テスト**")
    print("=" * 50)
    
    try:
        from platforms.implementations.twitter_platform import TwitterPlatform
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
        
        twitter_creds = {
            "api_key": credentials.get("TWITTER_API_KEY"),
            "api_secret": credentials.get("TWITTER_API_SECRET"),
            "access_token": credentials.get("TWITTER_ACCESS_TOKEN"),
            "access_token_secret": credentials.get("TWITTER_ACCESS_TOKEN_SECRET")
        }
        
        platform = TwitterPlatform(twitter_creds)
        
        # 認証
        print("🔐 認証中...")
        if not await platform.authenticate():
            print("❌ 認証失敗")
            return False
        
        print("✅ 認証成功")
        
        # アバターファイル確認
        avatar_path = "avatar.png"
        print(f"\n📁 アバターファイル確認...")
        if os.path.exists(avatar_path):
            file_size = os.path.getsize(avatar_path)
            print(f"✅ avatar.png 存在: {file_size} bytes")
        else:
            print("❌ avatar.png が存在しません")
            return False
        
        # プロフィール更新（アイコン含む）
        print(f"\n👤 アイコン付きプロフィール更新テスト...")
        test_profile = Profile(
            display_name="AetherPost",
            bio="🚀 Social media automation for developers | Testing icon update | https://aether-post.com",
            website_url="https://aether-post.com",
            avatar_path=avatar_path
        )
        
        print(f"📝 更新するプロフィール:")
        print(f"   名前: {test_profile.display_name}")
        print(f"   Bio: {test_profile.bio}")
        print(f"   Website: {test_profile.website_url}")
        print(f"   Avatar: {test_profile.avatar_path}")
        
        # プロフィール更新実行
        result = await platform.update_profile(test_profile)
        
        print(f"\n🔄 更新結果:")
        print(f"   成功: {result.success}")
        if result.error_message:
            print(f"   エラー: {result.error_message}")
        
        # API の詳細確認
        print(f"\n🔍 API詳細確認:")
        print(f"   API v1.1 client: {platform.api is not None}")
        print(f"   API v2 client: {platform.client is not None}")
        
        if platform.api:
            print("   ✅ API v1.1 利用可能（プロフィール画像更新用）")
        else:
            print("   ❌ API v1.1 利用不可")
        
        await platform.cleanup()
        return result.success
        
    except Exception as e:
        print(f"❌ アイコン更新テスト中にエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_manual_avatar_upload():
    """手動アバターアップロードテスト"""
    print("\n🎨 **手動アバターアップロードテスト**")
    print("=" * 30)
    
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
        
        platform = TwitterPlatform(twitter_creds)
        
        if await platform.authenticate():
            avatar_path = "avatar.png"
            if os.path.exists(avatar_path):
                print(f"📤 {avatar_path} を直接アップロード中...")
                
                # 直接API v1.1でアイコン更新
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, lambda: platform.api.update_profile_image(avatar_path)
                    )
                    print("✅ アイコン更新成功！")
                    return True
                except Exception as e:
                    print(f"❌ アイコン更新失敗: {e}")
                    return False
            else:
                print("❌ avatar.png が見つかりません")
                return False
        else:
            print("❌ 認証失敗")
            return False
        
    except Exception as e:
        print(f"❌ 手動アップロードエラー: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Twitter アイコン更新テスト開始\n")
    
    # テスト1: 統合プロフィール更新
    result1 = asyncio.run(test_twitter_avatar_update())
    
    # テスト2: 手動アバターアップロード
    result2 = asyncio.run(test_manual_avatar_upload())
    
    print(f"\n📊 テスト結果:")
    print(f"   統合プロフィール更新: {'✅' if result1 else '❌'}")
    print(f"   手動アバターアップロード: {'✅' if result2 else '❌'}")
    
    if result1 or result2:
        print("\n🎉 Twitterアイコン更新が成功しました！")
    else:
        print("\n⚠️ Twitterアイコン更新に問題があります。")