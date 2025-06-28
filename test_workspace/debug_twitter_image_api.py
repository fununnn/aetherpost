#!/usr/bin/env python3
"""Twitter画像API詳細デバッグ"""

import sys
import asyncio
import os
from pathlib import Path
from PIL import Image

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def debug_twitter_image_requirements():
    """Twitter画像要件とAPIレスポンスの詳細確認"""
    print("🐦 **Twitter 画像API詳細デバッグ**")
    print("=" * 50)
    
    # 1. 画像ファイル詳細確認
    avatar_path = "avatar.png"
    if os.path.exists(avatar_path):
        print(f"📁 画像ファイル詳細:")
        
        # ファイルサイズ
        file_size = os.path.getsize(avatar_path)
        print(f"   ファイルサイズ: {file_size} bytes ({file_size/1024:.1f} KB)")
        
        # 画像詳細 (PIL)
        try:
            with Image.open(avatar_path) as img:
                print(f"   画像形式: {img.format}")
                print(f"   画像サイズ: {img.size} ({img.width}x{img.height})")
                print(f"   カラーモード: {img.mode}")
                print(f"   DPI: {img.info.get('dpi', 'N/A')}")
        except Exception as e:
            print(f"   画像読み込みエラー: {e}")
        
        # Twitter API制限チェック
        print(f"\n📋 Twitter API制限チェック:")
        print(f"   ✅ ファイルサイズ制限: {file_size} <= 700KB = {file_size <= 700*1024}")
        print(f"   ✅ 画像形式: PNG対応")
        
        # 実際のAPI呼び出しテスト
        print(f"\n🔧 実際のAPI呼び出しテスト:")
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
                print("   ✅ 認証成功")
                
                # API v1.1で直接画像アップロード試行
                print("   🔄 API v1.1で画像アップロード中...")
                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: platform.api.update_profile_image(avatar_path)
                    )
                    print(f"   ✅ 画像アップロード成功: {result}")
                    
                    # ユーザー情報取得して確認
                    print("   🔍 更新後ユーザー情報取得...")
                    user_info = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: platform.api.verify_credentials()
                    )
                    
                    if user_info:
                        print(f"   📊 ユーザー情報:")
                        print(f"      名前: {user_info.name}")
                        print(f"      説明: {user_info.description}")
                        print(f"      プロフィール画像: {user_info.profile_image_url}")
                        print(f"      プロフィール画像HTTPS: {user_info.profile_image_url_https}")
                    
                except Exception as e:
                    print(f"   ❌ API呼び出しエラー: {e}")
                    print(f"   エラータイプ: {type(e).__name__}")
                    
                    # さらに詳細なエラー情報
                    if hasattr(e, 'response'):
                        print(f"   レスポンスコード: {e.response.status_code}")
                        print(f"   レスポンス内容: {e.response.text}")
                
                await platform.cleanup()
            else:
                print("   ❌ 認証失敗")
                
        except Exception as e:
            print(f"   ❌ プラットフォーム初期化エラー: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ {avatar_path} が存在しません")

if __name__ == "__main__":
    asyncio.run(debug_twitter_image_requirements())