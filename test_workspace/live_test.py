#!/usr/bin/env python3
"""Live integration test with real API credentials."""

import sys
import asyncio
import os
from pathlib import Path

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

async def test_real_avatar_generation():
    """Test real AI avatar generation with OpenAI."""
    print("🎨 Testing Real AI Avatar Generation...")
    
    try:
        from core.media.avatar_generator import get_or_generate_avatar
        from core.config.models import CampaignConfig, ContentConfig
        
        # Load credentials from .env.aetherpost
        credentials = {}
        env_path = "/home/ubuntu/doc/autopromo/test_workspace/.env.aetherpost"
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        credentials[key.strip()] = value.strip()
        
        # OpenAI credentials setup
        openai_creds = {}
        for key, value in credentials.items():
            if key.startswith('OPENAI_'):
                openai_key = key.replace('OPENAI_', '').lower()
                openai_creds[openai_key] = value
        
        creds_dict = {'openai': openai_creds} if openai_creds else {}
        
        # Test config
        content_config = ContentConfig(
            style="friendly",
            action="Check it out!",
            language="en"
        )
        
        test_config = CampaignConfig(
            name="AetherPost",
            concept="Social media automation for developers",
            platforms=["twitter"],
            content=content_config
        )
        
        print("🔄 Generating avatar with OpenAI DALL-E 3...")
        
        # Remove existing avatar to force generation
        if os.path.exists("avatar.png"):
            os.remove("avatar.png")
        
        avatar_path = await get_or_generate_avatar(test_config, creds_dict, force_generate=True)
        
        if avatar_path and os.path.exists(avatar_path):
            file_size = os.path.getsize(avatar_path)
            print(f"✅ Avatar generated successfully: {avatar_path} ({file_size} bytes)")
            return True
        else:
            print("❌ Avatar generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Real avatar generation test failed: {e}")
        return False

async def test_real_platform_authentication():
    """Test real platform authentication."""
    print("\n🔐 Testing Real Platform Authentication...")
    
    try:
        from platforms.core.platform_factory import platform_factory
        
        # Load credentials
        credentials = {}
        env_path = "/home/ubuntu/doc/autopromo/test_workspace/.env.aetherpost"
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()
        
        # Test Twitter authentication
        print("🐦 Testing Twitter authentication...")
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
        
        twitter_auth = await twitter_platform.authenticate()
        if twitter_auth:
            print("✅ Twitter authentication: SUCCESS")
        else:
            print("❌ Twitter authentication: FAILED")
        
        await twitter_platform.cleanup()
        
        # Test Bluesky authentication
        print("🦋 Testing Bluesky authentication...")
        bluesky_creds = {
            "identifier": credentials.get("BLUESKY_IDENTIFIER"),
            "password": credentials.get("BLUESKY_PASSWORD")
        }
        
        bluesky_platform = platform_factory.create_platform(
            platform_name="bluesky",
            credentials=bluesky_creds
        )
        
        bluesky_auth = await bluesky_platform.authenticate()
        if bluesky_auth:
            print("✅ Bluesky authentication: SUCCESS")
        else:
            print("❌ Bluesky authentication: FAILED")
        
        await bluesky_platform.cleanup()
        
        return twitter_auth or bluesky_auth
        
    except Exception as e:
        print(f"❌ Real platform authentication test failed: {e}")
        return False

async def test_real_content_generation():
    """Test real content generation with AI."""
    print("\n📝 Testing Real Content Generation...")
    
    try:
        from core.content.generator import ContentGenerator
        from core.config.models import CredentialsConfig, CampaignConfig, ContentConfig
        
        # Load credentials
        credentials = {}
        env_path = "/home/ubuntu/doc/autopromo/test_workspace/.env.aetherpost"
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()
        
        # Setup credentials
        openai_creds = {}
        for key, value in credentials.items():
            if key.startswith('OPENAI_'):
                openai_key = key.replace('OPENAI_', '').lower()
                openai_creds[openai_key] = value
        
        creds_config = CredentialsConfig(
            openai=openai_creds if openai_creds else None
        )
        
        generator = ContentGenerator(creds_config)
        
        # Test config
        content_config = ContentConfig(
            style="friendly",
            action="Check it out!",
            hashtags=["#automation", "#developers"],
            language="en"
        )
        
        campaign_config = CampaignConfig(
            name="AetherPost",
            concept="Social media automation for developers - making dev marketing effortless",
            url="https://aether-post.com",
            platforms=["twitter"],
            content=content_config
        )
        
        print("🤖 Generating content with AI...")
        
        content = await generator.generate_content(campaign_config, "twitter")
        
        if content and content.get("text"):
            print(f"✅ Content generated successfully:")
            print(f"   Text: {content['text'][:100]}...")
            print(f"   Length: {len(content['text'])} chars")
            print(f"   Hashtags: {content.get('hashtags', [])}")
            return True
        else:
            print("❌ Content generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Real content generation test failed: {e}")
        return False

async def test_real_profile_generation():
    """Test real profile generation and optimization."""
    print("\n🎭 Testing Real Profile Generation...")
    
    try:
        from core.profiles.generator import ProfileGenerator
        
        generator = ProfileGenerator()
        
        # Project info from campaign.yaml
        project_info = {
            "name": "AetherPost",
            "description": "Social media automation for developers - making dev marketing effortless",
            "website_url": "https://aether-post.com",
            "github_url": "https://github.com/fununnn/aetherpost",
            "urls": {
                "main": "https://aether-post.com",
                "github": "https://github.com/fununnn/aetherpost",
                "docs": "https://docs.aether-post.com"
            }
        }
        
        # Generate profiles for multiple platforms
        platforms_tested = []
        
        for platform in ["twitter", "bluesky", "linkedin"]:
            try:
                profile = generator.generate_profile(
                    platform=platform,
                    project_info=project_info,
                    style="friendly"
                )
                
                print(f"✅ {platform.title()} profile generated:")
                print(f"   Display Name: {profile.display_name}")
                print(f"   Bio: {profile.bio[:80]}...")
                print(f"   Website: {profile.website_url}")
                print(f"   Characters: {profile.character_count}/{profile.character_limit}")
                
                platforms_tested.append(platform)
                
            except Exception as e:
                print(f"❌ {platform} profile generation failed: {e}")
        
        return len(platforms_tested) >= 2
        
    except Exception as e:
        print(f"❌ Real profile generation test failed: {e}")
        return False

async def main():
    """Run live integration tests with real APIs."""
    print("🚀 **AetherPost Live Integration Test**")
    print("=" * 50)
    print("Using real API credentials for comprehensive testing\n")
    
    # Change to test workspace
    os.chdir("/home/ubuntu/doc/autopromo/test_workspace")
    
    tests = [
        ("AI Avatar Generation", test_real_avatar_generation),
        ("Platform Authentication", test_real_platform_authentication),
        ("Content Generation", test_real_content_generation),
        ("Profile Generation", test_real_profile_generation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Live Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All live tests PASSED! AetherPost is working perfectly with real APIs!")
    elif passed >= total * 0.75:
        print("👍 Most live tests passed! AetherPost is working well with real APIs!")
    else:
        print("⚠️  Some live tests failed. Check API credentials and network connectivity.")
    
    return 0 if passed >= total * 0.75 else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))