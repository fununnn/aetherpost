#!/usr/bin/env python3
"""Bluesky更新内容の詳細確認"""

import sys
import asyncio
import os
import json
from pathlib import Path

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def verify_bluesky_profile_update():
    """Blueskyプロフィール更新内容の詳細確認"""
    print("🦋 **Bluesky プロフィール更新確認**")
    print("=" * 50)
    
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
        
        platform = BlueskyPlatform(bluesky_creds)
        
        # 認証
        print("🔐 認証中...")
        if not await platform.authenticate():
            print("❌ 認証失敗")
            return False
        
        print(f"✅ 認証成功 (DID: {platform.did})")
        
        # 現在のプロフィール情報取得
        print("\n📋 現在のプロフィール情報:")
        current_profile = await platform._get_profile()
        
        if current_profile:
            print(f"   Handle: @{current_profile.get('handle')}")
            print(f"   表示名: {current_profile.get('displayName')}")
            print(f"   説明: {current_profile.get('description')}")
            print(f"   フォロワー: {current_profile.get('followersCount')}人")
            print(f"   フォロー中: {current_profile.get('followsCount')}人")
            print(f"   投稿数: {current_profile.get('postsCount')}件")
            
            # アバター情報確認
            avatar_url = current_profile.get('avatar')
            if avatar_url:
                print(f"   ✅ アバター: {avatar_url}")
            else:
                print(f"   ❌ アバター: 設定されていません")
        
        # プロフィールレコード詳細確認
        print("\n🔍 プロフィールレコード詳細:")
        profile_record = await platform._get_profile_record()
        
        if profile_record:
            value = profile_record.get('value', {})
            print(f"   URI: {profile_record.get('uri')}")
            print(f"   CID: {profile_record.get('cid')}")
            print(f"   Type: {value.get('$type')}")
            print(f"   表示名: {value.get('displayName')}")
            print(f"   説明: {value.get('description')}")
            
            # アバター詳細
            avatar_blob = value.get('avatar')
            if avatar_blob:
                print(f"   ✅ アバターBlob:")
                print(f"      Type: {avatar_blob.get('$type')}")
                print(f"      MIME: {avatar_blob.get('mimeType')}")
                print(f"      Size: {avatar_blob.get('size')} bytes")
                print(f"      Ref: {avatar_blob.get('ref', {}).get('$link')}")
            else:
                print(f"   ❌ アバターBlob: 設定されていません")
        
        # アバターファイルが存在するかチェック
        avatar_path = "avatar.png"
        print(f"\n📁 ローカルアバターファイル:")
        if os.path.exists(avatar_path):
            file_size = os.path.getsize(avatar_path)
            print(f"   ✅ {avatar_path} 存在: {file_size} bytes")
            
            # 手動でアバターアップロードしてみる
            print(f"\n🔄 手動アバターアップロードテスト...")
            from platforms.core.base_platform import Profile
            
            test_profile = Profile(
                display_name="AetherPost 🌐",
                bio="🚀 ソーシャルメディア自動化ツール | 開発者向け | AI画像アイコンテスト中 | https://aether-post.com",
                website_url="https://aether-post.com",
                avatar_path=avatar_path
            )
            
            result = await platform.update_profile(test_profile)
            if result.success:
                print(f"   ✅ 手動アバターアップロード成功!")
            else:
                print(f"   ❌ 手動アバターアップロード失敗: {result.error_message}")
        else:
            print(f"   ❌ {avatar_path} が存在しません")
        
        await platform.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ 確認中にエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(verify_bluesky_profile_update())