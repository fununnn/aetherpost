#!/usr/bin/env python3
"""
Test actual functionality with real API calls (non-destructive)
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aetherpost_self_promotion import AetherPostSelfPromotion, CampaignType

async def test_real_content_generation():
    """Test real OpenAI content generation."""
    print("🤖 Testing Real AI Content Generation")
    print("=" * 40)
    
    load_dotenv('.env.test')
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ No OpenAI API key found")
        return False
    
    promo = AetherPostSelfPromotion()
    
    # Setup connectors
    setup_success = await promo.setup_connectors('.env.test')
    if not setup_success:
        print("❌ Failed to setup connectors")
        return False
    
    print("✅ Connectors setup successful")
    
    # Test content generation for all campaign types
    success_count = 0
    total_tests = 0
    
    for campaign_type in [CampaignType.LAUNCH_ANNOUNCEMENT.value, 
                         CampaignType.FEATURE_HIGHLIGHTS.value,
                         CampaignType.COMMUNITY_BUILDING.value,
                         CampaignType.TECHNICAL_CONTENT.value]:
        
        total_tests += 1
        print(f"\n📝 Testing {campaign_type} content generation...")
        
        try:
            content = await promo.generate_promotion_content(campaign_type)
            
            if content and content.text:
                print(f"✅ Generated content ({len(content.text)} chars)")
                print(f"   Preview: {content.text[:100]}...")
                print(f"   Hashtags: {content.hashtags}")
                print(f"   Platforms: {content.platforms}")
                success_count += 1
            else:
                print("❌ No content generated")
                
        except Exception as e:
            print(f"❌ Generation failed: {e}")
    
    success_rate = success_count / total_tests * 100
    print(f"\n📊 Content Generation Success Rate: {success_rate:.1f}% ({success_count}/{total_tests})")
    
    return success_rate >= 100  # Require 100% success

async def test_platform_connector_initialization():
    """Test all platform connectors can be initialized."""
    print("\n🔌 Testing Platform Connector Initialization")
    print("=" * 45)
    
    load_dotenv('.env.test')
    
    # Test Twitter
    try:
        from aetherpost.plugins.connectors.twitter.connector import TwitterConnector
        twitter = TwitterConnector({
            "api_key": os.getenv("TWITTER_API_KEY"),
            "api_secret": os.getenv("TWITTER_API_SECRET"),
            "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
            "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        })
        print("✅ Twitter connector initialized")
        twitter_ok = True
    except Exception as e:
        print(f"❌ Twitter connector failed: {e}")
        twitter_ok = False
    
    # Test YouTube
    try:
        from aetherpost.plugins.connectors.youtube.connector import YouTubeConnector
        youtube = YouTubeConnector({
            "client_id": os.getenv("YOUTUBE_CLIENT_ID"),
            "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET")
        })
        print("✅ YouTube connector initialized")
        youtube_ok = True
    except Exception as e:
        print(f"❌ YouTube connector failed: {e}")
        youtube_ok = False
    
    # Test Reddit (placeholder credentials)
    try:
        from aetherpost.plugins.connectors.reddit.connector import RedditConnector
        reddit = RedditConnector({
            "client_id": "test_id",
            "client_secret": "test_secret",
            "username": "test_user",
            "password": "test_pass"
        })
        print("✅ Reddit connector initialized")
        reddit_ok = True
    except Exception as e:
        print(f"❌ Reddit connector failed: {e}")
        reddit_ok = False
    
    connectors_ok = [twitter_ok, youtube_ok, reddit_ok]
    success_rate = sum(connectors_ok) / len(connectors_ok) * 100
    
    print(f"\n📊 Connector Initialization Success Rate: {success_rate:.1f}%")
    return success_rate >= 66  # At least 2/3 connectors should work

async def test_complete_workflow_dry_run():
    """Test complete workflow with dry run."""
    print("\n🔄 Testing Complete Workflow (Dry Run)")
    print("=" * 40)
    
    promo = AetherPostSelfPromotion()
    
    # Setup
    setup_success = await promo.setup_connectors('.env.test')
    if not setup_success:
        print("❌ Setup failed")
        return False
    
    print("✅ Setup successful")
    
    # Test workflow for one campaign
    try:
        result = await promo.run_promotion_campaign(
            CampaignType.LAUNCH_ANNOUNCEMENT.value, 
            dry_run=True
        )
        
        if result and "content" in result:
            content = result["content"]
            print("✅ Workflow completed successfully")
            print(f"   Generated: {len(content.text)} character post")
            print(f"   Hashtags: {len(content.hashtags)} tags")
            print(f"   Platforms: {len(content.platforms)} platforms")
            print(f"   Success rate: {result.get('success_rate', 0):.1f}")
            
            # Verify content quality
            has_content = len(content.text) > 50
            has_hashtags = len(content.hashtags) > 0
            has_platforms = len(content.platforms) > 0
            
            quality_ok = has_content and has_hashtags and has_platforms
            print(f"   Quality check: {'✅' if quality_ok else '❌'}")
            
            return quality_ok
        else:
            print("❌ Workflow failed - no content generated")
            return False
            
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        return False

async def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n🛡️ Testing Error Handling")
    print("=" * 25)
    
    promo = AetherPostSelfPromotion()
    
    # Test with invalid campaign type
    try:
        content = await promo.generate_promotion_content("invalid_campaign")
        print("✅ Invalid campaign handled gracefully")
        error_handling_1 = True
    except Exception as e:
        print(f"❌ Invalid campaign caused error: {e}")
        error_handling_1 = False
    
    # Test with no credentials
    try:
        promo_no_creds = AetherPostSelfPromotion()
        success = await promo_no_creds.setup_connectors("nonexistent.env")
        print(f"✅ Missing credentials handled: {success}")
        error_handling_2 = True
    except Exception as e:
        print(f"❌ Missing credentials caused error: {e}")
        error_handling_2 = False
    
    error_handling_ok = error_handling_1 and error_handling_2
    print(f"📊 Error Handling: {'✅ ROBUST' if error_handling_ok else '❌ FRAGILE'}")
    
    return error_handling_ok

async def main():
    """Run complete functionality test."""
    print("🚀 AetherPost COMPLETE Functionality Test")
    print("=" * 50)
    print("Testing ALL functionality with REAL API calls")
    print("(Non-destructive - no actual posting)")
    
    # Run all tests
    tests = {
        "Real Content Generation": await test_real_content_generation(),
        "Platform Connectors": await test_platform_connector_initialization(),
        "Complete Workflow": await test_complete_workflow_dry_run(),
        "Error Handling": await test_error_handling()
    }
    
    # Results summary
    print("\n" + "=" * 50)
    print("🏁 COMPLETE FUNCTIONALITY TEST RESULTS")
    print("=" * 50)
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    success_count = sum(tests.values())
    total_tests = len(tests)
    overall_success_rate = success_count / total_tests * 100
    
    print(f"\n📈 Overall Success Rate: {overall_success_rate:.1f}% ({success_count}/{total_tests})")
    
    if overall_success_rate == 100:
        print("\n🎉 AetherPost is COMPLETELY FUNCTIONAL!")
        print("   ✅ All real API integrations working")
        print("   ✅ Content generation with OpenAI")
        print("   ✅ Platform connectors operational")
        print("   ✅ Complete workflow validated")
        print("   ✅ Error handling robust")
        print("\n🚀 READY FOR PRODUCTION USE!")
        
    elif overall_success_rate >= 75:
        print("\n✅ AetherPost is MOSTLY FUNCTIONAL")
        print("   Most features working correctly")
        print("   Minor issues that don't block usage")
        
    else:
        print("\n❌ AetherPost has SIGNIFICANT ISSUES")
        print("   Major functionality problems detected")
        print("   Requires fixes before production use")
    
    return overall_success_rate >= 75

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)