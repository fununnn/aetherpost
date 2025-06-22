#!/usr/bin/env python3

import asyncio
import aiohttp
from datetime import datetime
import json

async def update_bluesky_profile_and_post():
    """実際にBlueskyのプロフィールと投稿を更新する"""
    auth_data = {
        'identifier': 'aetherpost.bsky.social',
        'password': 'dnvo-rq33-txsz-hnpj'
    }
    
    async with aiohttp.ClientSession() as session:
        # 1. 認証
        print("🔐 Authenticating with Bluesky...")
        async with session.post(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            json=auth_data
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f'❌ Authentication failed: {response.status} - {error_text}')
                return False
            
            auth_result = await response.json()
            access_token = auth_result.get('accessJwt')
            did = auth_result.get('did')
            handle = auth_result.get('handle')
            print(f'✅ Authenticated as {handle}')
            print(f'   DID: {did}')
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # 2. 現在のプロフィールを取得
        print("\n📋 Getting current profile...")
        async with session.get(
            f'https://bsky.social/xrpc/app.bsky.actor.getProfile',
            params={'actor': did},
            headers=headers
        ) as response:
            if response.status == 200:
                current_profile = await response.json()
                print(f"   Current display name: {current_profile.get('displayName', 'None')}")
                print(f"   Current bio: {current_profile.get('description', 'None')}")
            else:
                print(f"❌ Failed to get profile: {response.status}")
                return False
        
        # 3. プロフィール更新
        print("\n🎭 Updating profile...")
        profile_record = {
            'displayName': 'AetherPost 🚀',
            'description': '👋 Building AetherPost! Social media automation for developers. Join me on this journey! | Come say hi! 🤝'
        }
        
        profile_data = {
            'repo': did,
            'collection': 'app.bsky.actor.profile',
            'rkey': 'self',
            'record': profile_record
        }
        
        async with session.post(
            'https://bsky.social/xrpc/com.atproto.repo.putRecord',
            json=profile_data,
            headers=headers
        ) as response:
            if response.status == 200:
                print("✅ Profile updated successfully!")
            else:
                error_text = await response.text()
                print(f"❌ Profile update failed: {response.status} - {error_text}")
        
        # 4. 投稿作成
        print("\n📝 Creating post...")
        post_text = """🚀 AetherPost v1.7.0 is now live!

Terraform-style social media automation for developers:
• One setup, full automation
• Multi-platform support (Twitter, Bluesky, Instagram, etc.)
• AI-powered content generation

pip install aetherpost
aetherpost init

https://aether-post.com

#OpenSource #DevTools #Automation #SocialMedia"""
        
        post_record = {
            'text': post_text,
            'createdAt': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            '$type': 'app.bsky.feed.post'
        }
        
        post_data = {
            'repo': did,
            'collection': 'app.bsky.feed.post',
            'record': post_record
        }
        
        async with session.post(
            'https://bsky.social/xrpc/com.atproto.repo.createRecord',
            json=post_data,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                post_uri = result.get('uri')
                if post_uri:
                    post_id = post_uri.split('/')[-1]
                    print("✅ Post created successfully!")
                    print(f"📱 View at: https://bsky.app/profile/aetherpost.bsky.social/post/{post_id}")
                    return True
            else:
                error_text = await response.text()
                print(f"❌ Post creation failed: {response.status} - {error_text}")
                return False
        
        # 5. 最終確認
        print("\n🔍 Verifying updates...")
        await asyncio.sleep(2)  # 少し待機
        
        async with session.get(
            f'https://bsky.social/xrpc/app.bsky.actor.getProfile',
            params={'actor': did},
            headers=headers
        ) as response:
            if response.status == 200:
                updated_profile = await response.json()
                print(f"   Updated display name: {updated_profile.get('displayName', 'None')}")
                print(f"   Updated bio: {updated_profile.get('description', 'None')}")
                print(f"   Posts count: {updated_profile.get('postsCount', 0)}")
            
        return True

if __name__ == "__main__":
    success = asyncio.run(update_bluesky_profile_and_post())
    if success:
        print("\n🎉 All updates completed! Please check https://bsky.app/profile/aetherpost.bsky.social")
    else:
        print("\n❌ Updates failed. Please check the errors above.")