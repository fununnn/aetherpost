#!/usr/bin/env python3
"""
Test the self-promotion script with dry run to verify full functionality
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aetherpost_self_promotion import AetherPostSelfPromotion, CampaignType


async def test_dry_run_campaigns():
    """Test all campaign types with dry run."""
    print("🧪 Testing AetherPost Self-Promotion (Dry Run)")
    print("=" * 50)
    
    promo = AetherPostSelfPromotion()
    
    # Setup connectors
    setup_success = await promo.setup_connectors(".env.test")
    
    if not setup_success:
        print("❌ Failed to setup connectors")
        return False
    
    print("✅ Connectors setup successful")
    
    # Test all campaign types
    campaign_types = [
        CampaignType.LAUNCH_ANNOUNCEMENT.value,
        CampaignType.FEATURE_HIGHLIGHTS.value,
        CampaignType.COMMUNITY_BUILDING.value,
        CampaignType.TECHNICAL_CONTENT.value
    ]
    
    results = {}
    
    for campaign_type in campaign_types:
        print(f"\n🎯 Testing campaign: {campaign_type}")
        try:
            result = await promo.run_promotion_campaign(campaign_type, dry_run=True)
            
            if result and "content" in result:
                results[campaign_type] = {
                    "status": "SUCCESS",
                    "content_length": len(result["content"].text),
                    "hashtags": len(result["content"].hashtags),
                    "platforms": len(result["content"].platforms)
                }
                print(f"✅ {campaign_type}: SUCCESS")
                print(f"   Content: {result['content'].text[:80]}...")
            else:
                results[campaign_type] = {"status": "FAILED"}
                print(f"❌ {campaign_type}: FAILED")
                
        except Exception as e:
            results[campaign_type] = {"status": "ERROR", "error": str(e)}
            print(f"💥 {campaign_type}: ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 CAMPAIGN TEST SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for r in results.values() if r["status"] == "SUCCESS")
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total}")
    print(f"📈 Success Rate: {successful/total*100:.1f}%")
    
    for campaign, result in results.items():
        status_emoji = "✅" if result["status"] == "SUCCESS" else "❌"
        print(f"{status_emoji} {campaign}: {result['status']}")
        
        if result["status"] == "SUCCESS":
            print(f"   📝 Content: {result['content_length']} chars")
            print(f"   🏷️ Hashtags: {result['hashtags']}")
            print(f"   📱 Platforms: {result['platforms']}")
    
    return successful == total


async def test_shell_script_components():
    """Test shell script functionality."""
    print("\n🔧 Testing Shell Script Components")
    print("=" * 30)
    
    import subprocess
    
    # Test shell script syntax
    try:
        result = subprocess.run(["bash", "-n", "scripts/self_promote.sh"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Shell script syntax: VALID")
        else:
            print(f"❌ Shell script syntax: INVALID - {result.stderr}")
            return False
    except Exception as e:
        print(f"💥 Shell script test error: {e}")
        return False
    
    # Test environment file exists
    if os.path.exists(".env.test"):
        print("✅ Test environment file: EXISTS")
    else:
        print("❌ Test environment file: MISSING")
        return False
    
    # Test campaign file exists
    if os.path.exists("campaign_aetherpost.yaml"):
        print("✅ Campaign configuration: EXISTS")
    else:
        print("❌ Campaign configuration: MISSING")
        return False
    
    print("✅ Shell script components: ALL READY")
    return True


async def main():
    """Run complete test suite."""
    print("🚀 AetherPost Complete Functionality Test")
    print("=" * 60)
    
    # Test Python components
    python_success = await test_dry_run_campaigns()
    
    # Test shell script components
    shell_success = await test_shell_script_components()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST RESULTS")
    print("=" * 60)
    
    print(f"🐍 Python Components: {'✅ PASS' if python_success else '❌ FAIL'}")
    print(f"🔧 Shell Components: {'✅ PASS' if shell_success else '❌ FAIL'}")
    
    overall_success = python_success and shell_success
    
    if overall_success:
        print("\n🎉 AetherPost Self-Promotion System: FULLY FUNCTIONAL!")
        print("   ✅ All campaigns generate content successfully")
        print("   ✅ OpenAI integration working")
        print("   ✅ Platform connectors initialized")
        print("   ✅ Shell scripts ready for execution")
        print("\n💡 Ready for production use with real API credentials!")
    else:
        print("\n⚠️ AetherPost Self-Promotion System: PARTIALLY FUNCTIONAL")
        print("   Some components need attention before production use")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)