#!/usr/bin/env python3
"""BlueskyアバターをAPI制限に合わせてリサイズ"""

import sys
import asyncio
import os
from pathlib import Path
from PIL import Image
import io

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

def resize_image_for_bluesky(input_path: str, output_path: str, max_size_kb: int = 100):
    """Bluesky用に画像をリサイズ・圧縮"""
    print(f"🎨 画像リサイズ: {input_path} → {output_path}")
    
    try:
        with Image.open(input_path) as img:
            # 元の画像情報
            original_size = os.path.getsize(input_path)
            print(f"   元サイズ: {img.size} ({original_size} bytes = {original_size/1024:.1f} KB)")
            
            # RGBAからRGBに変換（PNGの透明度対応）
            if img.mode in ('RGBA', 'LA'):
                # 白背景で透明度を埋める
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])  # alpha channel as mask
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # サイズとクオリティを調整してファイルサイズを制限内にする
            sizes_to_try = [(256, 256), (200, 200), (150, 150), (128, 128), (100, 100)]
            qualities = [85, 75, 65, 55, 45]
            
            target_size = max_size_kb * 1024  # KB to bytes
            
            for size in sizes_to_try:
                for quality in qualities:
                    # リサイズ
                    resized = img.resize(size, Image.Resampling.LANCZOS)
                    
                    # メモリ上でJPEG圧縮テスト
                    buffer = io.BytesIO()
                    resized.save(buffer, format='JPEG', quality=quality, optimize=True)
                    compressed_size = buffer.tell()
                    
                    print(f"   試行: {size} quality={quality} → {compressed_size} bytes ({compressed_size/1024:.1f} KB)")
                    
                    if compressed_size <= target_size:
                        # 目標サイズ以下になったので保存
                        with open(output_path, 'wb') as f:
                            f.write(buffer.getvalue())
                        
                        print(f"   ✅ 成功: {size} quality={quality}")
                        print(f"   最終サイズ: {compressed_size} bytes ({compressed_size/1024:.1f} KB)")
                        return True
            
            # 全て失敗した場合、最小設定で強制保存
            print("   ⚠️ 目標サイズに達しませんでした。最小設定で保存します。")
            final_img = img.resize((100, 100), Image.Resampling.LANCZOS)
            final_img.save(output_path, format='JPEG', quality=30, optimize=True)
            
            final_size = os.path.getsize(output_path)
            print(f"   最終サイズ: {final_size} bytes ({final_size/1024:.1f} KB)")
            return True
            
    except Exception as e:
        print(f"   ❌ リサイズエラー: {e}")
        return False

async def test_resized_bluesky_upload():
    """リサイズした画像でBlueskyアップロードテスト"""
    print(f"\n🦋 **リサイズ画像でBlueskyアップロードテスト**")
    print("=" * 50)
    
    try:
        from platforms.implementations.bluesky_platform import BlueskyPlatform
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
        
        bluesky_creds = {
            "identifier": credentials.get("BLUESKY_IDENTIFIER"),
            "password": credentials.get("BLUESKY_PASSWORD")
        }
        
        platform = BlueskyPlatform(bluesky_creds)
        
        if await platform.authenticate():
            print("✅ 認証成功")
            
            # リサイズした画像でプロフィール更新
            resized_avatar = "avatar_bluesky_resized.jpg"
            test_profile = Profile(
                display_name="AetherPost 🌐",
                bio="🚀 ソーシャルメディア自動化ツール | 開発者向け | リサイズアイコンテスト | https://aether-post.com",
                website_url="https://aether-post.com",
                avatar_path=resized_avatar
            )
            
            print(f"🔄 リサイズアバターでプロフィール更新中...")
            result = await platform.update_profile(test_profile)
            
            if result.success:
                print("✅ プロフィール更新成功！")
                
                # 更新後の確認
                print("\n📋 更新後プロフィール確認:")
                updated_profile = await platform._get_profile()
                if updated_profile:
                    avatar_url = updated_profile.get('avatar')
                    if avatar_url:
                        print(f"   ✅ 新しいアバターURL: {avatar_url}")
                    else:
                        print(f"   ❌ アバターが設定されていません")
                
                return True
            else:
                print(f"❌ プロフィール更新失敗: {result.error_message}")
                return False
        else:
            print("❌ 認証失敗")
            return False
        
    except Exception as e:
        print(f"❌ テスト中にエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎨 Bluesky アバターリサイズ & アップロードテスト")
    print("=" * 60)
    
    # Step 1: 画像リサイズ
    original_avatar = "avatar.png"
    resized_avatar = "avatar_bluesky_resized.jpg"
    
    if os.path.exists(original_avatar):
        if resize_image_for_bluesky(original_avatar, resized_avatar, max_size_kb=100):
            print("✅ 画像リサイズ完了")
            
            # Step 2: アップロードテスト
            result = asyncio.run(test_resized_bluesky_upload())
            
            if result:
                print("\n🎉 Blueskyアバター更新が完全に成功しました！")
                print("📱 確認: https://bsky.app/profile/aetherpost.bsky.social")
            else:
                print("\n⚠️ アップロードに問題があります。")
        else:
            print("❌ 画像リサイズ失敗")
    else:
        print(f"❌ {original_avatar} が存在しません")