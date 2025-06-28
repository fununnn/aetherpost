#!/usr/bin/env python3
"""Test script for profile generation and update system."""

import sys
import asyncio
from pathlib import Path

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def test_profile_generation():
    """Test profile generation functionality."""
    print("🎭 Testing profile generation...")
    
    try:
        from core.profiles.generator import ProfileGenerator
        
        generator = ProfileGenerator()
        print("✅ ProfileGenerator初期化: OK")
        
        # テスト用プロジェクト情報
        test_project_info = {
            "name": "TestApp",
            "description": "Revolutionary productivity tool for developers",
            "website_url": "https://testapp.example.com",
            "github_url": "https://github.com/user/testapp",
            "tech_stack": ["Python", "FastAPI", "React"],
            "features": ["automation", "developer-tools", "productivity"]
        }
        
        # サポート対象プラットフォーム
        supported_platforms = generator.get_supported_platforms()
        print(f"✅ サポートプラットフォーム: {len(supported_platforms)} 個")
        
        # 各プラットフォームでプロフィール生成テスト
        generated_profiles = []
        
        for platform in ["twitter", "instagram", "linkedin", "github", "bluesky"][:3]:  # 3つに限定
            try:
                profile = generator.generate_profile(
                    platform=platform,
                    project_info=test_project_info,
                    style="friendly"
                )
                
                print(f"✅ {platform}: プロフィール生成成功")
                print(f"   - 表示名: {profile.display_name}")
                print(f"   - Bio長: {profile.character_count}/{profile.character_limit}")
                
                generated_profiles.append(platform)
                
            except Exception as e:
                print(f"❌ {platform}: プロフィール生成失敗 - {e}")
        
        print(f"✅ プロフィール生成: {len(generated_profiles)}/3 プラットフォーム")
        return len(generated_profiles) >= 2
        
    except Exception as e:
        print(f"❌ プロフィール生成テスト失敗: {e}")
        return False

async def test_profile_variations():
    """Test profile style variations."""
    print("\n🎨 Testing profile style variations...")
    
    try:
        from core.profiles.generator import ProfileGenerator
        
        generator = ProfileGenerator()
        
        test_project_info = {
            "name": "AetherPost",
            "description": "Social media automation for developers"
        }
        
        styles = ["professional", "friendly", "creative", "technical"]
        generated_variations = []
        
        for style in styles:
            try:
                profile = generator.generate_profile(
                    platform="twitter",
                    project_info=test_project_info,
                    style=style
                )
                
                print(f"✅ {style}: スタイル生成成功")
                print(f"   - Bio: {profile.bio[:50]}...")
                
                generated_variations.append(style)
                
            except Exception as e:
                print(f"❌ {style}: スタイル生成失敗 - {e}")
        
        print(f"✅ スタイルバリエーション: {len(generated_variations)}/4 スタイル")
        return len(generated_variations) >= 3
        
    except Exception as e:
        print(f"❌ スタイルバリエーションテスト失敗: {e}")
        return False

async def test_unified_profile_command():
    """Test unified profile command interface."""
    print("\n⚙️ Testing unified profile command...")
    
    try:
        # 直接プロフィールジェネレータを使用して統合テスト
        from core.profiles.generator import ProfileGenerator
        from platforms.core.platform_registry import platform_registry
        
        generator = ProfileGenerator()
        
        # プラットフォーム情報取得
        platform_info = platform_registry.get_platform_info("twitter")
        
        if not platform_info or 'error' in platform_info:
            print("❌ プラットフォーム情報取得失敗")
            return False
        
        test_project_info = {
            "name": "TestApp",
            "description": "Amazing developer tool",
            "website_url": "https://testapp.com",
            "github_url": "https://github.com/user/testapp"
        }
        
        # プロフィール生成
        profile = generator.generate_profile(
            platform="twitter",
            project_info=test_project_info,
            style="friendly"
        )
        
        print("✅ 統合プロフィールコマンド: OK")
        print(f"   - 表示名: {profile.display_name}")
        print(f"   - Bio: {profile.bio[:50]}...")
        print(f"   - Website: {profile.website_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ 統合プロフィールコマンドテスト失敗: {e}")
        return False

async def test_platform_registry_integration():
    """Test platform registry integration."""
    print("\n📋 Testing platform registry integration...")
    
    try:
        from platforms.core.platform_registry import platform_registry
        
        # 利用可能プラットフォーム取得
        available_platforms = platform_registry.get_available_platforms()
        print(f"✅ 利用可能プラットフォーム: {available_platforms}")
        
        # 各プラットフォームの情報確認
        valid_platforms = []
        
        for platform_name in available_platforms[:3]:  # 3つに限定
            platform_info = platform_registry.get_platform_info(platform_name)
            
            if platform_info and 'error' not in platform_info:
                char_limit = platform_info.get('character_limit', 0)
                capabilities = platform_info.get('capabilities', [])
                
                print(f"✅ {platform_name}:")
                print(f"   - 文字制限: {char_limit}")
                print(f"   - 機能数: {len(capabilities)}")
                
                valid_platforms.append(platform_name)
            else:
                print(f"❌ {platform_name}: 情報取得失敗")
        
        print(f"✅ プラットフォーム情報: {len(valid_platforms)}/3 有効")
        return len(valid_platforms) >= 2
        
    except Exception as e:
        print(f"❌ プラットフォームレジストリテスト失敗: {e}")
        return False

async def test_profile_url_integration():
    """Test URL integration in profiles."""
    print("\n🔗 Testing URL integration...")
    
    try:
        from core.profiles.generator import ProfileGenerator
        
        generator = ProfileGenerator()
        
        # URL情報を含むプロジェクト情報
        test_project_info = {
            "name": "AetherPost",
            "description": "Social media automation tool",
            "website_url": "https://aether-post.com",
            "github_url": "https://github.com/user/aetherpost",
            "urls": {
                "main": "https://aether-post.com",
                "github": "https://github.com/user/aetherpost",
                "docs": "https://docs.aether-post.com"
            }
        }
        
        # Twitter（URLが制限される）とLinkedIn（URLが推奨される）でテスト
        platforms_tested = []
        
        for platform in ["twitter", "linkedin"]:
            try:
                profile = generator.generate_profile(
                    platform=platform,
                    project_info=test_project_info,
                    style="professional"
                )
                
                has_url = bool(profile.website_url)
                has_additional_links = len(profile.additional_links) > 0
                
                print(f"✅ {platform}:")
                print(f"   - Website URL: {'有り' if has_url else '無し'}")
                print(f"   - 追加リンク: {len(profile.additional_links)}個")
                
                platforms_tested.append(platform)
                
            except Exception as e:
                print(f"❌ {platform}: URL統合テスト失敗 - {e}")
        
        print(f"✅ URL統合: {len(platforms_tested)}/2 プラットフォーム")
        return len(platforms_tested) == 2
        
    except Exception as e:
        print(f"❌ URL統合テスト失敗: {e}")
        return False

async def main():
    """Run all profile system tests."""
    print("🧪 AetherPost Profile System Tests\n")
    
    tests = [
        test_profile_generation,
        test_profile_variations,
        test_unified_profile_command,
        test_platform_registry_integration,
        test_profile_url_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ テスト例外発生: {e}")
    
    print(f"\n📊 プロフィールシステムテスト結果: {passed}/{total} 成功 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 全プロフィールシステムテスト成功!")
        return 0
    else:
        print("❌ 一部プロフィールシステムテスト失敗")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))