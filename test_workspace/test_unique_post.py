#!/usr/bin/env python3
"""Test unique post creation."""

import sys
import asyncio
import os
from pathlib import Path
from datetime import datetime

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "aetherpost_source"))

from platforms.core.platform_factory import platform_factory
from platforms.core.base_platform import Content, ContentType

async def test_unique_post():
    """Test posting with unique content."""
    print("🚀 Testing unique post creation...")
    
    # Load credentials
    credentials = {}
    with open('.env.aetherpost', 'r') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                credentials[key.strip()] = value.strip()
    
    twitter_creds = {
        'api_key': credentials.get('TWITTER_API_KEY'),
        'api_secret': credentials.get('TWITTER_API_SECRET'),
        'access_token': credentials.get('TWITTER_ACCESS_TOKEN'),
        'access_token_secret': credentials.get('TWITTER_ACCESS_TOKEN_SECRET')
    }
    
    platform = platform_factory.create_platform('twitter', twitter_creds)
    
    if await platform.authenticate():
        # Unique content with timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        unique_text = f"🚀 AetherPost is working! Social media automation made easy for developers! {timestamp} #AetherPost #DevTools"
        
        content = Content(
            content_type=ContentType.TEXT,
            text=unique_text,
            hashtags=['#AetherPost', '#DevTools']
        )
        
        print(f"📝 Posting: {unique_text}")
        result = await platform.post_content(content)
        
        if result.success:
            print(f'✅ New tweet posted successfully!')
            print(f'Post ID: {result.post_id}')
            print(f'URL: {result.post_url}')
        else:
            print(f'❌ Failed: {result.error_message}')
    else:
        print("❌ Authentication failed")
    
    await platform.cleanup()

if __name__ == "__main__":
    asyncio.run(test_unique_post())