#!/usr/bin/env python3
"""Simple Twitter API test script."""

import os
from dotenv import load_dotenv
import tweepy

# Load test environment
load_dotenv('.env.test')

# Get credentials
api_key = os.getenv("TWITTER_API_KEY")
api_secret = os.getenv("TWITTER_API_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

print("🐦 Testing Twitter API credentials...")
print(f"API Key: {api_key[:10]}..." if api_key else "❌ No API Key")
print(f"API Secret: {api_secret[:10]}..." if api_secret else "❌ No API Secret")
print(f"Access Token: {access_token[:10]}..." if access_token else "❌ No Access Token")
print(f"Access Token Secret: {access_token_secret[:10]}..." if access_token_secret else "❌ No Access Token Secret")

if not all([api_key, api_secret, access_token, access_token_secret]):
    print("❌ Missing credentials")
    exit(1)

try:
    # Test with v2 API
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        wait_on_rate_limit=True
    )
    
    # Try to get user info
    print("\n🔍 Testing API access...")
    me = client.get_me()
    
    if me.data:
        print(f"✅ Authentication successful!")
        print(f"   User: @{me.data.username}")
        print(f"   Name: {me.data.name}")
        print(f"   ID: {me.data.id}")
    else:
        print("❌ Authentication failed - no user data returned")
        
except tweepy.Unauthorized as e:
    print(f"❌ Unauthorized: {e}")
    print("   Check your API credentials and permissions")
except tweepy.Forbidden as e:
    print(f"❌ Forbidden: {e}")
    print("   Your app may not have the required permissions")
except Exception as e:
    print(f"❌ Error: {e}")
    print("   Please check your credentials and network connection")