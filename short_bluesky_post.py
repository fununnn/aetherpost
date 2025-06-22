#!/usr/bin/env python3

import asyncio
import aiohttp
from datetime import datetime

async def create_short_post():
    """短い投稿を作成"""
    auth_data = {
        'identifier': 'aetherpost.bsky.social',
        'password': 'dnvo-rq33-txsz-hnpj'
    }
    
    async with aiohttp.ClientSession() as session:
        # 認証
        async with session.post(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            json=auth_data
        ) as response:
            auth_result = await response.json()
            access_token = auth_result.get('accessJwt')
            did = auth_result.get('did')
        
        # 短い投稿（300文字以内）
        post_text = """🚀 AetherPost v1.7.0 is live!

Terraform-style social media automation for developers.
One setup, full automation across platforms.

pip install aetherpost && aetherpost init

https://aether-post.com

#OpenSource #DevTools #Automation"""
        
        print(f"Post length: {len(post_text)} characters")
        
        post_data = {
            'repo': did,
            'collection': 'app.bsky.feed.post',
            'record': {
                'text': post_text,
                'createdAt': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                '$type': 'app.bsky.feed.post'
            }
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        async with session.post(
            'https://bsky.social/xrpc/com.atproto.repo.createRecord',
            json=post_data,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                post_uri = result.get('uri')
                post_id = post_uri.split('/')[-1]
                print("✅ Post created successfully!")
                print(f"📱 View at: https://bsky.app/profile/aetherpost.bsky.social/post/{post_id}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Post failed: {response.status} - {error_text}")
                return False

if __name__ == "__main__":
    asyncio.run(create_short_post())