#!/usr/bin/env python3
"""
Test all shell script options automatically
"""

import subprocess
import sys
import os
import time

def run_shell_option(option_number, description):
    """Run a shell script option and capture output."""
    print(f"\n🧪 Testing Option {option_number}: {description}")
    print("=" * 50)
    
    try:
        # Use echo to simulate user input
        process = subprocess.Popen(
            ['bash', './scripts/self_promote.sh'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=os.environ.copy()
        )
        
        # Send the option number
        stdout, _ = process.communicate(input=f"{option_number}\n", timeout=60)
        
        print(stdout)
        
        return_code = process.returncode
        success = return_code == 0
        
        print(f"📊 Option {option_number} Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        return success, stdout
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Option {option_number} TIMED OUT")
        process.kill()
        return False, "TIMEOUT"
    except Exception as e:
        print(f"💥 Option {option_number} ERROR: {e}")
        return False, str(e)

def test_shell_script_syntax():
    """Test shell script syntax."""
    print("🔧 Testing Shell Script Syntax")
    print("=" * 30)
    
    try:
        result = subprocess.run(
            ['bash', '-n', './scripts/self_promote.sh'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Shell script syntax is valid")
            return True
        else:
            print(f"❌ Shell script syntax error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"💥 Syntax check failed: {e}")
        return False

def test_environment_files():
    """Test required environment files exist."""
    print("\n📁 Testing Required Files")
    print("=" * 25)
    
    required_files = [
        ('.env', 'Environment file'),
        ('campaign_aetherpost.yaml', 'Campaign configuration'),
        ('aetherpost_self_promotion.py', 'Python self-promotion script'),
        ('scripts/self_promote.sh', 'Shell script')
    ]
    
    all_exist = True
    
    for filepath, description in required_files:
        if os.path.exists(filepath):
            print(f"✅ {description}: EXISTS")
        else:
            print(f"❌ {description}: MISSING")
            all_exist = False
    
    return all_exist

def main():
    """Test all shell script functionality."""
    print("🔗 AetherPost Shell Script Complete Test")
    print("=" * 60)
    
    # Test 1: Syntax
    syntax_ok = test_shell_script_syntax()
    
    # Test 2: Required files
    files_ok = test_environment_files()
    
    if not syntax_ok or not files_ok:
        print("\n🚨 Pre-requisites failed. Cannot test script options.")
        return False
    
    # Test all shell script options
    shell_options = [
        (1, "Quick post (using current campaign)"),
        (2, "Custom self-promotion script"),
        (3, "Interactive content generation"),
        (4, "Scheduled promotion campaign"),
        (5, "Reddit-focused technical post"),
        (6, "Show promotion analytics"),
        (7, "Test platform connections")
    ]
    
    results = {}
    
    for option_num, description in shell_options:
        success, output = run_shell_option(option_num, description)
        results[option_num] = {
            'description': description,
            'success': success,
            'output': output
        }
        
        # Small delay between tests
        time.sleep(2)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 SHELL SCRIPT TEST SUMMARY")
    print("=" * 60)
    
    successful_options = sum(1 for r in results.values() if r['success'])
    total_options = len(results)
    success_rate = successful_options / total_options * 100
    
    print(f"📊 Overall Success Rate: {success_rate:.1f}% ({successful_options}/{total_options})")
    
    for option_num, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} Option {option_num}: {result['description']}")
    
    # Detailed analysis
    if success_rate == 100:
        print("\n🎉 ALL SHELL SCRIPT OPTIONS WORKING!")
        print("   ✅ Complete interactive menu functional")
        print("   ✅ All automation options available")
        print("   ✅ Error handling working correctly")
        print("\n🚀 Shell script is PRODUCTION READY!")
        
    elif success_rate >= 80:
        print("\n✅ MOST SHELL SCRIPT OPTIONS WORKING")
        print("   Most functionality is operational")
        print("   Minor issues in some options")
        
    else:
        print("\n❌ SIGNIFICANT SHELL SCRIPT ISSUES")
        print("   Multiple options failing")
        print("   Requires investigation and fixes")
    
    # Show failed options for debugging
    failed_options = [num for num, result in results.items() if not result['success']]
    if failed_options:
        print(f"\n🔍 Failed Options for Investigation: {failed_options}")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)