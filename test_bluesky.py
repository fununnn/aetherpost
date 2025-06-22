#!/usr/bin/env python3

import asyncio
import aiohttp
from datetime import datetime

async def post_to_bluesky():
    """直接BlueskyAPIに投稿してテストする"""
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
            if response.status != 200:
                print('❌ Authentication failed')
                return
            
            auth_result = await response.json()
            access_token = auth_result.get('accessJwt')
            did = auth_result.get('did')
            print(f'✅ Authenticated as {auth_result.get("handle")}')
        
        # 投稿内容
        post_text = '🚀 AetherPost v1.7.0 is live! Terraform-style social media automation for developers. One setup, full automation. ✨\n\nhttps://aether-post.com\n\n#OpenSource #DevTools #Automation'
        
        post_data = {
            'repo': did,
            'collection': 'app.bsky.feed.post',
            'record': {
                'text': post_text,
                'createdAt': datetime.utcnow().isoformat() + 'Z'
            }
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # 投稿実行
        async with session.post(
            'https://bsky.social/xrpc/com.atproto.repo.createRecord',
            json=post_data,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                post_uri = result.get('uri')
                post_id = post_uri.split('/')[-1] if post_uri else None
                print('✅ Post successful!')
                print(f'📱 View at: https://bsky.app/profile/aetherpost.bsky.social/post/{post_id}')
                return True
            else:
                error = await response.text()
                print(f'❌ Post failed: {response.status} - {error}')
                return False

if __name__ == "__main__":
    asyncio.run(post_to_bluesky())