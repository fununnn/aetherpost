#!/usr/bin/env python3
"""
Fix Twitter API authentication issues by testing different approaches
"""

import os
import sys
from dotenv import load_dotenv
import tweepy

# Load test environment
load_dotenv('.env.test')

def test_twitter_credentials():
    """Test Twitter credentials with different authentication methods."""
    
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    
    print("🔍 Debugging Twitter API Authentication")
    print("=" * 50)
    
    # Test 1: OAuth 1.0a User Authentication
    print("\n1. Testing OAuth 1.0a User Authentication...")
    try:
        auth = tweepy.OAuth1UserHandler(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
        
        # Test with verify_credentials
        user = api_v1.verify_credentials()
        print(f"✅ OAuth 1.0a Success: @{user.screen_name}")
        return True, api_v1, None
        
    except Exception as e:
        print(f"❌ OAuth 1.0a Failed: {e}")
    
    # Test 2: Client with v2 API
    print("\n2. Testing Twitter v2 Client...")
    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )
        
        # Test with get_me
        me = client.get_me()
        if me.data:
            print(f"✅ v2 Client Success: @{me.data.username}")
            return True, None, client
        else:
            print("❌ v2 Client Failed: No user data")
            
    except Exception as e:
        print(f"❌ v2 Client Failed: {e}")
    
    # Test 3: Check credential format
    print("\n3. Checking credential formats...")
    print(f"API Key length: {len(api_key) if api_key else 0}")
    print(f"API Secret length: {len(api_secret) if api_secret else 0}")
    print(f"Access Token length: {len(access_token) if access_token else 0}")
    print(f"Access Token Secret length: {len(access_token_secret) if access_token_secret else 0}")
    
    # Check if access token looks valid
    if access_token and '-' in access_token:
        user_id = access_token.split('-')[0]
        print(f"User ID from token: {user_id}")
    
    return False, None, None

def test_actual_posting(api_v1=None, client=None):
    """Test actual posting functionality."""
    print("\n🐦 Testing Actual Tweet Posting...")
    
    test_content = "🧪 AetherPost functionality test - testing Twitter API integration. This is an automated test post. #AetherPostTest #TwitterAPI"
    
    if client:
        try:
            print("Attempting to post with v2 Client...")
            response = client.create_tweet(text=test_content)
            print(f"✅ Tweet posted successfully with v2! Tweet ID: {response.data['id']}")
            return True
        except Exception as e:
            print(f"❌ v2 Tweet failed: {e}")
    
    if api_v1:
        try:
            print("Attempting to post with v1.1 API...")
            tweet = api_v1.update_status(test_content)
            print(f"✅ Tweet posted successfully with v1.1! Tweet ID: {tweet.id}")
            return True
        except Exception as e:
            print(f"❌ v1.1 Tweet failed: {e}")
    
    return False

def main():
    """Main testing function."""
    success, api_v1, client = test_twitter_credentials()
    
    if success:
        print("\n🎯 Credentials are valid! Testing actual posting...")
        
        # Ask user if they want to test actual posting
        response = input("\n⚠️ Do you want to test ACTUAL posting to Twitter? (y/N): ").strip().lower()
        
        if response == 'y':
            post_success = test_actual_posting(api_v1, client)
            if post_success:
                print("\n🎉 Twitter integration is FULLY FUNCTIONAL!")
            else:
                print("\n❌ Posting failed - check API permissions")
        else:
            print("\n✅ Credentials verified - skipping actual posting")
            
        return True
    else:
        print("\n🚨 Twitter credentials are NOT working")
        print("Possible issues:")
        print("1. Invalid API keys")
        print("2. App not approved for posting")
        print("3. Incorrect access level")
        print("4. API keys revoked/expired")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)