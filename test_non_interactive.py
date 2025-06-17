#!/usr/bin/env python3
"""
Test non-interactive functionality for automated environments
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aetherpost_self_promotion import AetherPostSelfPromotion, CampaignType

async def test_non_interactive_mode():
    """Test non-interactive mode functionality."""
    print("🤖 Testing Non-Interactive Mode")
    print("=" * 35)
    
    promo = AetherPostSelfPromotion()
    
    # Test setup in non-interactive environment
    setup_success = await promo.setup_connectors('.env.test')
    
    if not setup_success:
        print("❌ Setup failed")
        return False
    
    print("✅ Setup successful in non-interactive mode")
    
    # Test all campaign types in non-interactive mode
    campaign_results = {}
    
    for campaign_type in [CampaignType.LAUNCH_ANNOUNCEMENT.value,
                         CampaignType.FEATURE_HIGHLIGHTS.value,
                         CampaignType.COMMUNITY_BUILDING.value,
                         CampaignType.TECHNICAL_CONTENT.value]:
        
        print(f"\n📋 Testing {campaign_type} (non-interactive)...")
        
        try:
            # Force dry run mode (no user input required)
            result = await promo.run_promotion_campaign(campaign_type, dry_run=True)
            
            if result and "content" in result:
                print(f"✅ {campaign_type}: SUCCESS")
                print(f"   Content length: {len(result['content'].text)} chars")
                print(f"   Hashtags: {len(result['content'].hashtags)}")
                print(f"   Platforms: {len(result['content'].platforms)}")
                campaign_results[campaign_type] = True
            else:
                print(f"❌ {campaign_type}: FAILED - No content")
                campaign_results[campaign_type] = False
                
        except Exception as e:
            print(f"❌ {campaign_type}: ERROR - {e}")
            campaign_results[campaign_type] = False
    
    success_count = sum(campaign_results.values())
    total_campaigns = len(campaign_results)
    success_rate = success_count / total_campaigns * 100
    
    print(f"\n📊 Non-Interactive Campaign Success Rate: {success_rate:.1f}% ({success_count}/{total_campaigns})")
    
    return success_rate >= 100

def test_shell_script_non_interactive():
    """Test shell script options that don't require user input."""
    print("\n🔧 Testing Non-Interactive Shell Options")
    print("=" * 40)
    
    import subprocess
    
    # Test options that don't require user interaction
    non_interactive_options = [
        (4, "Scheduled promotion campaign"),
        (6, "Show promotion analytics"),
        (7, "Test platform connections")
    ]
    
    results = {}
    
    for option_num, description in non_interactive_options:
        print(f"\n🧪 Testing Option {option_num}: {description}")
        
        try:
            process = subprocess.Popen(
                ['bash', './scripts/self_promote.sh'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            stdout, _ = process.communicate(input=f"{option_num}\n", timeout=30)
            success = process.returncode == 0
            
            if success:
                print(f"✅ Option {option_num} completed successfully")
            else:
                print(f"❌ Option {option_num} failed")
                print(f"Output: {stdout[-200:]}")  # Last 200 chars
            
            results[option_num] = success
            
        except Exception as e:
            print(f"💥 Option {option_num} error: {e}")
            results[option_num] = False
    
    successful_options = sum(results.values())
    total_options = len(results)
    success_rate = successful_options / total_options * 100
    
    print(f"\n📊 Shell Script Success Rate: {success_rate:.1f}% ({successful_options}/{total_options})")
    
    return success_rate >= 100

async def test_complete_automation():
    """Test complete automation workflow."""
    print("\n🚀 Testing Complete Automation Workflow")
    print("=" * 40)
    
    try:
        # Simulate a complete automated promotion cycle
        promo = AetherPostSelfPromotion()
        
        # Setup
        setup_ok = await promo.setup_connectors('.env.test')
        if not setup_ok:
            print("❌ Automation setup failed")
            return False
        
        print("✅ Automation setup successful")
        
        # Generate content for multiple campaigns automatically
        automation_results = []
        
        campaigns_to_run = [
            CampaignType.LAUNCH_ANNOUNCEMENT.value,
            CampaignType.FEATURE_HIGHLIGHTS.value
        ]
        
        for campaign in campaigns_to_run:
            try:
                result = await promo.run_promotion_campaign(campaign, dry_run=True)
                automation_results.append(bool(result and "content" in result))
                print(f"✅ Automated {campaign} campaign")
            except Exception as e:
                print(f"❌ Automated {campaign} failed: {e}")
                automation_results.append(False)
        
        automation_success_rate = sum(automation_results) / len(automation_results) * 100
        print(f"\n📊 Automation Success Rate: {automation_success_rate:.1f}%")
        
        return automation_success_rate >= 100
        
    except Exception as e:
        print(f"💥 Automation error: {e}")
        return False

async def main():
    """Run complete non-interactive test suite."""
    print("🔄 AetherPost Non-Interactive Functionality Test")
    print("=" * 60)
    
    # Run all non-interactive tests
    tests = {
        "Non-Interactive Mode": await test_non_interactive_mode(),
        "Shell Script (Non-Interactive)": test_shell_script_non_interactive(),
        "Complete Automation": await test_complete_automation()
    }
    
    # Results summary
    print("\n" + "=" * 60)
    print("🏁 NON-INTERACTIVE TEST RESULTS")
    print("=" * 60)
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    success_count = sum(tests.values())
    total_tests = len(tests)
    overall_success_rate = success_count / total_tests * 100
    
    print(f"\n📈 Overall Success Rate: {overall_success_rate:.1f}% ({success_count}/{total_tests})")
    
    if overall_success_rate == 100:
        print("\n🎉 NON-INTERACTIVE MODE FULLY FUNCTIONAL!")
        print("   ✅ All automation features working")
        print("   ✅ Shell script compatibility verified")
        print("   ✅ Complete workflow automation ready")
        print("\n🤖 READY FOR AUTOMATED DEPLOYMENT!")
        
    elif overall_success_rate >= 75:
        print("\n✅ NON-INTERACTIVE MODE MOSTLY FUNCTIONAL")
        print("   Most automation features working")
        print("   Minor issues in some areas")
        
    else:
        print("\n❌ SIGNIFICANT NON-INTERACTIVE ISSUES")
        print("   Automation features have problems")
        print("   Requires fixes for production automation")
    
    return overall_success_rate >= 75

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)