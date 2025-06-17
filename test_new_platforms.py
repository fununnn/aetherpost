#!/usr/bin/env python3
"""Test script for Reddit and YouTube connectors."""

import asyncio
import os
import sys
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aetherpost.plugins.connectors.reddit.connector import RedditConnector
from aetherpost.plugins.connectors.youtube.connector import YouTubeConnector


async def test_reddit_connector():
    """Test Reddit connector functionality."""
    print("🔴 Testing Reddit Connector")
    print("=" * 50)
    
    # Mock credentials for testing (replace with real ones for actual testing)
    reddit_creds = {
        'client_id': 'your_reddit_client_id',
        'client_secret': 'your_reddit_client_secret',
        'username': 'your_reddit_username',
        'password': 'your_reddit_password',
        'user_agent': 'AetherPost/1.0 Test'
    }
    
    try:
        # Test connector initialization
        print("📋 Initializing Reddit connector...")
        connector = RedditConnector(reddit_creds)
        print("✅ Reddit connector initialized successfully")
        
        # Test subreddit finding
        print("\n🔍 Testing subreddit discovery...")
        test_content = "I built a new Python automation tool for developers that helps with API testing"
        subreddits = await connector._find_relevant_subreddits(test_content)
        print(f"✅ Found relevant subreddits: {subreddits}")
        
        # Test content optimization
        print("\n✏️ Testing content optimization...")
        optimized = await connector._optimize_for_subreddit(test_content, "programming", "text")
        print(f"✅ Optimized content:")
        print(f"   Title: {optimized['title']}")
        print(f"   Subreddit: {optimized['subreddit']}")
        print(f"   Flair: {optimized.get('flair', 'None')}")
        
        # Test mock posting (won't actually post without real credentials)
        print("\n📝 Testing mock posting...")
        post_result = await connector.post({
            'text': test_content,
            'type': 'text'
        })
        print(f"✅ Mock post result: {post_result['status']}")
        if post_result['status'] == 'published':
            print(f"   Posted to subreddits: {post_result.get('subreddits_posted', [])}")
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install with: pip install praw>=7.0.0")
    except Exception as e:
        print(f"❌ Reddit test failed: {e}")
    
    print()


async def test_youtube_connector():
    """Test YouTube connector functionality."""
    print("🔴 Testing YouTube Connector")
    print("=" * 50)
    
    # Mock credentials for testing
    youtube_creds = {
        'client_id': 'your_google_client_id',
        'client_secret': 'your_google_client_secret',
        'credentials_file': 'youtube_credentials.json',
        'token_file': 'youtube_token.json'
    }
    
    try:
        # Test connector initialization
        print("📋 Initializing YouTube connector...")
        connector = YouTubeConnector(youtube_creds)
        print("✅ YouTube connector initialized successfully")
        
        # Test video generation
        print("\n🎥 Testing video generation...")
        test_content = "Check out our new developer tool for automated testing!"
        video_path = await connector._generate_simple_video(test_content)
        print(f"✅ Generated video placeholder: {video_path}")
        
        # Clean up test file
        if os.path.exists(video_path):
            os.remove(video_path)
            print("🧹 Cleaned up test video file")
        
        # Test mock posting (won't actually post without real credentials)
        print("\n📝 Testing mock posting...")
        post_result = await connector.post({
            'text': test_content,
            'video_file': None  # Will trigger video generation
        })
        print(f"✅ Mock post result: {post_result['status']}")
        if post_result['status'] == 'failed':
            print(f"   Expected failure (no auth): {post_result.get('error', 'No error message')}")
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    except Exception as e:
        print(f"❌ YouTube test failed: {e}")
    
    print()


def test_configuration_models():
    """Test configuration models."""
    print("⚙️ Testing Configuration Models")
    print("=" * 50)
    
    try:
        # Test Reddit config
        from aetherpost.core.config.reddit import RedditConfig, RedditPostConfig
        
        print("📋 Testing Reddit configuration...")
        reddit_config = RedditConfig(
            client_id="test_id",
            client_secret="test_secret",
            username="test_user",
            password="test_pass"
        )
        print("✅ Reddit config validation passed")
        
        reddit_post = RedditPostConfig(
            subreddit="programming",
            title="Test Post",
            content="Test content"
        )
        print("✅ Reddit post config validation passed")
        
        # Test YouTube config
        from aetherpost.core.config.youtube import YouTubeConfig, YouTubeVideoConfig
        
        print("\n📋 Testing YouTube configuration...")
        youtube_config = YouTubeConfig(
            client_id="test_id",
            client_secret="test_secret"
        )
        print("✅ YouTube config validation passed")
        
        youtube_video = YouTubeVideoConfig(
            title="Test Video",
            description="Test description"
        )
        print("✅ YouTube video config validation passed")
        
        # Test platform validation
        from aetherpost.core.config.models import CampaignConfig
        
        print("\n📋 Testing platform validation...")
        campaign = CampaignConfig(
            name="Test Campaign",
            concept="Test concept",
            platforms=["twitter", "reddit", "youtube"]
        )
        print("✅ Platform validation passed (reddit, youtube now supported)")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
    
    print()


def check_dependencies():
    """Check if required dependencies are available."""
    print("📦 Checking Dependencies")
    print("=" * 50)
    
    dependencies = {
        'praw': 'Reddit API wrapper',
        'google.auth': 'Google authentication',
        'googleapiclient': 'Google API client',
        'google_auth_oauthlib': 'Google OAuth2 flow'
    }
    
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module} - {description}")
        except ImportError:
            print(f"❌ {module} - {description} (not installed)")
    
    print()


async def main():
    """Run all tests."""
    print("🚀 AetherPost New Platform Connectors Test")
    print("=" * 60)
    print()
    
    # Check dependencies first
    check_dependencies()
    
    # Test configuration models
    test_configuration_models()
    
    # Test connectors
    await test_reddit_connector()
    await test_youtube_connector()
    
    print("🎉 Testing completed!")
    print("\n💡 To use these connectors in production:")
    print("1. Install dependencies: pip install praw>=7.0.0 google-api-python-client")
    print("2. Set up Reddit app at: https://www.reddit.com/prefs/apps")
    print("3. Set up Google OAuth2 at: https://console.cloud.google.com/")
    print("4. Configure credentials in your .env file")


if __name__ == "__main__":
    asyncio.run(main())