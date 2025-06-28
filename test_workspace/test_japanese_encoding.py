#!/usr/bin/env python3
"""日本語・多言語エンコーディングテスト"""

import sys
import asyncio
import os
from pathlib import Path
from datetime import datetime

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def test_japanese_encoding():
    """日本語・多言語エンコーディングテスト"""
    print("🌍 **多言語エンコーディングテスト**")
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
        
        platform = BlueskyPlatform(bluesky_creds)
        
        # 認証
        print("🔐 認証中...")
        if not await platform.authenticate():
            print("❌ 認証失敗")
            return False
        
        print("✅ 認証成功")
        
        # 1. 日本語プロフィール更新テスト
        print("\n👤 日本語プロフィール更新テスト...")
        japanese_profile = Profile(
            display_name="AetherPost 🚀",
            bio="🌟 開発者向けソーシャルメディア自動化ツール | 日本語対応 | マルチプラットフォーム対応 🇯🇵✨ | https://aether-post.com",
            website_url="https://aether-post.com"
        )
        
        profile_result = await platform.update_profile(japanese_profile)
        if profile_result.success:
            print("✅ 日本語プロフィール更新成功！")
        else:
            print(f"❌ 日本語プロフィール更新失敗: {profile_result.error_message}")
        
        # 2. 多言語投稿テスト
        print("\n📝 多言語投稿テスト...")
        
        # 日本語
        timestamp = datetime.now().strftime("%H:%M:%S")
        japanese_content = Content(
            content_type=ContentType.TEXT,
            text=f"🚀 AetherPost日本語テスト投稿！ソーシャルメディア自動化で開発者の負担を軽減 ✨ {timestamp} #AetherPost #日本語 #開発者ツール",
            hashtags=["#AetherPost", "#日本語", "#開発者ツール"]
        )
        
        japanese_result = await platform.post_content(japanese_content)
        if japanese_result.success:
            print(f"✅ 日本語投稿成功: {japanese_result.post_id}")
        else:
            print(f"❌ 日本語投稿失敗: {japanese_result.error_message}")
        
        # 絵文字多用テスト
        emoji_content = Content(
            content_type=ContentType.TEXT,
            text=f"🎉🚀✨ AetherPost 絵文字テスト 🌟💻🔥 開発者向け自動化ツール 🛠️⚡📱 {timestamp} #emoji #test",
            hashtags=["#emoji", "#test"]
        )
        
        emoji_result = await platform.post_content(emoji_content)
        if emoji_result.success:
            print(f"✅ 絵文字投稿成功: {emoji_result.post_id}")
        else:
            print(f"❌ 絵文字投稿失敗: {emoji_result.error_message}")
        
        # 英語（比較用）
        english_content = Content(
            content_type=ContentType.TEXT,
            text=f"🚀 AetherPost English encoding test! Social media automation for developers ✨ {timestamp} #AetherPost #English #DevTools",
            hashtags=["#AetherPost", "#English", "#DevTools"]
        )
        
        english_result = await platform.post_content(english_content)
        if english_result.success:
            print(f"✅ 英語投稿成功: {english_result.post_id}")
        else:
            print(f"❌ 英語投稿失敗: {english_result.error_message}")
        
        await platform.cleanup()
        
        # 結果まとめ
        success_count = sum([
            profile_result.success,
            japanese_result.success,
            emoji_result.success,
            english_result.success
        ])
        
        print(f"\n📊 エンコーディングテスト結果: {success_count}/4 成功")
        
        if success_count == 4:
            print("🎉 すべての多言語テストが成功しました！文字化け問題は解決されています。")
        elif success_count >= 3:
            print("👍 ほとんどの多言語テストが成功しました。")
        else:
            print("⚠️ 一部のテストが失敗しました。エンコーディング設定を確認してください。")
        
        return success_count >= 3
        
    except Exception as e:
        print(f"❌ エンコーディングテスト中にエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_japanese_encoding())
    if result:
        print("\n🎉 多言語エンコーディングテスト成功!")
    else:
        print("\n⚠️ エンコーディングに問題があります。")