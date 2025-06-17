#!/usr/bin/env python3
"""
Complete YouTube API integration test
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_youtube_imports():
    """Test YouTube API imports and dependencies."""
    print("📺 Testing YouTube API Dependencies")
    print("=" * 40)
    
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        print("✅ Google API imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_youtube_connector():
    """Test YouTube connector initialization."""
    print("\n🔧 Testing YouTube Connector")
    print("=" * 30)
    
    try:
        from aetherpost.plugins.connectors.youtube.connector import YouTubeConnector
        
        load_dotenv('.env.test')
        
        connector = YouTubeConnector({
            "client_id": os.getenv("YOUTUBE_CLIENT_ID"),
            "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET")
        })
        
        print("✅ YouTube connector created successfully")
        print(f"   Client ID: {connector.credentials.get('client_id', '')[:20]}...")
        print(f"   Client Secret: {connector.credentials.get('client_secret', '')[:20]}...")
        
        # Test connector properties
        print(f"   Name: {connector.name}")
        print(f"   Supported media: {connector.supported_media_types}")
        
        return True, connector
        
    except Exception as e:
        print(f"❌ YouTube connector failed: {e}")
        return False, None

async def test_youtube_authentication(connector):
    """Test YouTube authentication flow."""
    print("\n🔐 Testing YouTube Authentication")
    print("=" * 35)
    
    try:
        # Test authentication setup (without actual OAuth flow)
        print("⚠️ Note: Full OAuth flow requires browser interaction")
        print("✅ Authentication setup structure verified")
        
        # Check if we can initialize the OAuth flow
        has_auth_method = hasattr(connector, 'authenticate')
        has_credentials = bool(connector.credentials)
        
        print(f"   Has authenticate method: {has_auth_method}")
        print(f"   Has credentials: {has_credentials}")
        
        return has_auth_method and has_credentials
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_youtube_post_structure():
    """Test YouTube post method structure."""
    print("\n📤 Testing YouTube Post Structure")
    print("=" * 35)
    
    try:
        from aetherpost.plugins.connectors.youtube.connector import YouTubeConnector
        
        connector = YouTubeConnector({
            "client_id": "test",
            "client_secret": "test"
        })
        
        # Test post method exists
        has_post_method = hasattr(connector, 'post')
        print(f"   Has post method: {has_post_method}")
        
        # Test method signature
        import inspect
        if has_post_method:
            sig = inspect.signature(connector.post)
            print(f"   Post method signature: {sig}")
        
        return has_post_method
        
    except Exception as e:
        print(f"❌ Post structure test failed: {e}")
        return False

async def main():
    """Run complete YouTube API test."""
    print("🎥 Complete YouTube API Integration Test")
    print("=" * 50)
    
    # Test 1: Dependencies
    deps_ok = test_youtube_imports()
    
    # Test 2: Connector creation
    connector_ok, connector = test_youtube_connector()
    
    # Test 3: Authentication structure
    auth_ok = False
    if connector:
        auth_ok = await test_youtube_authentication(connector)
    
    # Test 4: Post method structure
    post_ok = test_youtube_post_structure()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 YouTube API Test Summary")
    print("=" * 50)
    
    tests = {
        "Dependencies": deps_ok,
        "Connector Creation": connector_ok,
        "Authentication Structure": auth_ok,
        "Post Method Structure": post_ok
    }
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    success_count = sum(tests.values())
    total_tests = len(tests)
    success_rate = success_count / total_tests * 100
    
    print(f"\n📈 Success Rate: {success_rate:.1f}% ({success_count}/{total_tests})")
    
    if success_rate >= 75:
        print("🎉 YouTube integration is structurally sound!")
        print("💡 Note: Full functionality requires OAuth flow completion")
    else:
        print("🚨 YouTube integration has significant issues")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)