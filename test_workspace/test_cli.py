#!/usr/bin/env python3
"""Test script for AetherPost CLI functionality."""

import sys
import os
from pathlib import Path

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

def test_basic_imports():
    """Test basic module imports."""
    print("🔧 Testing basic imports...")
    
    try:
        from core.config.models import CampaignConfig, CredentialsConfig
        print("✅ Config models import: OK")
    except Exception as e:
        print(f"❌ Config models import: {e}")
        return False
        
    try:
        from platforms.core.platform_registry import platform_registry
        print("✅ Platform registry import: OK")
    except Exception as e:
        print(f"❌ Platform registry import: {e}")
        return False
        
    try:
        from platforms.core.platform_factory import platform_factory
        print("✅ Platform factory import: OK")
    except Exception as e:
        print(f"❌ Platform factory import: {e}")
        return False
        
    return True

def test_platform_availability():
    """Test platform availability."""
    print("\n📱 Testing platform availability...")
    
    try:
        from platforms.core.platform_registry import platform_registry
        
        available_platforms = platform_registry.get_available_platforms()
        print(f"✅ Available platforms: {available_platforms}")
        
        expected_platforms = ["twitter", "bluesky", "instagram", "linkedin", "youtube"]
        missing = set(expected_platforms) - set(available_platforms)
        
        if missing:
            print(f"❌ Missing platforms: {missing}")
            return False
        else:
            print("✅ All expected platforms available")
            return True
            
    except Exception as e:
        print(f"❌ Platform availability test: {e}")
        return False

def test_content_generator():
    """Test content generator functionality."""
    print("\n📝 Testing content generator...")
    
    try:
        from core.content.generator import ContentGenerator
        from core.config.models import CredentialsConfig
        
        # Create test credentials
        credentials = CredentialsConfig(
            ai_service={"api_key": "test-key"},
            openai={"api_key": "test-key"}
        )
        
        generator = ContentGenerator(credentials)
        print("✅ Content generator initialization: OK")
        
        # Test provider setup
        providers = list(generator.ai_providers.keys())
        print(f"✅ AI providers detected: {providers}")
        
        return True
        
    except Exception as e:
        print(f"❌ Content generator test: {e}")
        return False

def test_configuration_loading():
    """Test configuration loading."""
    print("\n⚙️ Testing configuration loading...")
    
    try:
        from core.config.parser import ConfigLoader
        
        loader = ConfigLoader()
        print("✅ Config loader initialization: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading test: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 AetherPost Core System Tests\n")
    
    tests = [
        test_basic_imports,
        test_platform_availability,
        test_content_generator,
        test_configuration_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())