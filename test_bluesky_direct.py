#!/usr/bin/env python3
"""Direct test of Bluesky profile update functionality."""

import asyncio
import sys
import os
sys.path.insert(0, '/home/ubuntu/.asdf/installs/python/3.12.3/lib/python3.12/site-packages')

from aetherpost_source.plugins.connectors.bluesky.connector import BlueskyConnector

async def test_bluesky_update():
    """Test Bluesky profile update directly."""
    
    # Load credentials from environment
    from dotenv import load_dotenv
    load_dotenv('/home/ubuntu/doc/autopromo/aetherpost_promo/.env.aetherpost')
    
    credentials = {
        'identifier': os.getenv('BLUESKY_IDENTIFIER'),
        'password': os.getenv('BLUESKY_PASSWORD'),
        'base_url': 'https://bsky.social'
    }
    
    print(f"Using credentials: identifier={credentials['identifier']}")
    
    # Create connector
    connector = BlueskyConnector(credentials)
    
    # Test authentication
    auth_result = await connector.authenticate(credentials)
    print(f"Authentication result: {auth_result}")
    
    if auth_result:
        # Test profile update
        profile_data = {
            'display_name': 'AetherPost 🌐',
            'bio': '👋 Building AetherPost! Social media automation for developers - like Terraform for social platforms. Love connecting with fellow builders! #community #opentoconnect',
            'website_url': 'https://aether-post.com',
            'github_url': 'https://github.com/fununnn/aetherpost'
        }
        
        print("Attempting profile update...")
        result = await connector.update_profile(profile_data)
        print(f"Profile update result: {result}")
        
        return result
    else:
        print("Authentication failed")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_bluesky_update())
    print(f"Final result: {result}")