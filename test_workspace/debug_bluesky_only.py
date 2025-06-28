#!/usr/bin/env python3
"""Bluesky専用デバッグスクリプト"""

import sys
import asyncio
import os
from pathlib import Path
from datetime import datetime

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def test_bluesky_detailed():
    """Blueskyの詳細テスト"""
    print("🦋 **Bluesky詳細デバッグ**")
    print("=" * 50)
    
    try:
        from platforms.implementations.bluesky_platform import BlueskyPlatform
        from platforms.core.base_platform import Content, ContentType, Profile
        
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
        
        print(f"🔑 認証情報:")
        print(f"   Identifier: {bluesky_creds['identifier']}")
        print(f"   Password: {bluesky_creds['password'][:5]}...")
        
        # プラットフォーム作成
        platform = BlueskyPlatform(bluesky_creds)
        
        # 1. 認証テスト
        print("\n🔐 認証テスト...")
        auth_result = await platform.authenticate()
        print(f"認証結果: {auth_result}")
        
        if not auth_result:
            print("❌ 認証失敗。処理を停止します。")
            return False
        
        print(f"✅ 認証成功")
        print(f"   Session Token: {platform.session_token[:20]}..." if platform.session_token else "No token")
        print(f"   DID: {platform.did}")
        
        # 2. プロフィール更新テスト
        print("\n👤 プロフィール更新テスト...")
        test_profile = Profile(
            display_name="AetherPost",
            bio="🚀 ソーシャルメディア自動化ツール for developers | https://aether-post.com",
            website_url="https://aether-post.com"
        )
        
        profile_result = await platform.update_profile(test_profile)
        print(f"プロフィール更新結果: {profile_result.success}")
        if not profile_result.success:
            print(f"エラー: {profile_result.error_message}")
        else:
            print("✅ プロフィール更新成功")
        
        # 3. 投稿テスト
        print("\n📝 投稿テスト...")
        timestamp = datetime.now().strftime("%H:%M:%S")
        test_content = Content(
            content_type=ContentType.TEXT,
            text=f"🚀 AetherPostのテスト投稿です！開発者向けソーシャルメディア自動化ツール {timestamp} #AetherPost #開発者ツール",
            hashtags=["#AetherPost", "#開発者ツール"]
        )
        
        post_result = await platform.post_content(test_content)
        print(f"投稿結果: {post_result.success}")
        if post_result.success:
            print(f"✅ 投稿成功! Post ID: {post_result.post_id}")
            print(f"URL: {post_result.post_url}")
        else:
            print(f"❌ 投稿失敗: {post_result.error_message}")
        
        await platform.cleanup()
        return auth_result and profile_result.success and post_result.success
        
    except Exception as e:
        print(f"❌ Blueskyテスト中にエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bluesky_detailed())
    if result:
        print("\n🎉 Bluesky全機能テスト成功!")
    else:
        print("\n⚠️ Blueskyに問題があります。")