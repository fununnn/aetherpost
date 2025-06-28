#!/usr/bin/env python3
"""Blueskyプロフィール詳細デバッグ"""

import sys
import asyncio
import json
from pathlib import Path

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def debug_bluesky_profile():
    """Blueskyプロフィール取得・更新のデバッグ"""
    print("🦋 **Bluesky プロフィール詳細デバッグ**")
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
            return
        
        print(f"✅ 認証成功")
        print(f"   DID: {platform.did}")
        
        # 現在のプロフィール取得テスト
        print("\n📋 現在のプロフィール取得テスト...")
        current_profile = await platform._get_profile()
        
        if current_profile:
            print("✅ プロフィール取得成功:")
            print(f"   Handle: {current_profile.get('handle')}")
            print(f"   Display Name: {current_profile.get('displayName')}")
            print(f"   Description: {current_profile.get('description')}")
            print(f"   Followers: {current_profile.get('followersCount')}")
            print(f"   Following: {current_profile.get('followsCount')}")
            
            # プロフィールの詳細構造を確認
            print(f"\n📄 プロフィール構造 (JSON):")
            print(json.dumps(current_profile, indent=2, ensure_ascii=False))
            
            # プロフィールレコード取得テスト
            print(f"\n🔍 プロフィールレコード取得テスト...")
            try:
                import aiohttp
                
                session = await platform._get_session()
                headers = platform._get_authenticated_headers()
                
                # プロフィールレコードを直接取得
                params = {
                    "repo": platform.did,
                    "collection": "app.bsky.actor.profile",
                    "rkey": "self"
                }
                
                async with session.get(
                    f"{platform.base_url}/xrpc/com.atproto.repo.getRecord",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        record_data = await response.json()
                        print("✅ プロフィールレコード取得成功:")
                        print(json.dumps(record_data, indent=2, ensure_ascii=False))
                    else:
                        error_text = await response.text()
                        print(f"❌ プロフィールレコード取得失敗: {response.status} - {error_text}")
                        
                        # レコードが存在しない場合は作成が必要
                        if response.status == 400:
                            print("💡 プロフィールレコードが存在しません。createRecordで作成する必要があります。")
                            
            except Exception as e:
                print(f"❌ プロフィールレコード取得エラー: {e}")
        else:
            print("❌ プロフィール取得失敗")
        
        await platform.cleanup()
        
    except Exception as e:
        print(f"❌ デバッグ中にエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_bluesky_profile())