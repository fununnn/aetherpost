#!/usr/bin/env python3
"""プロフィール生成の自然性テスト"""

import yaml
from aetherpost_source.core.profiles.generator import ProfileGenerator

def test_natural_profile_generation():
    # テスト用キャンペーンデータ
    campaign_data = {
        'name': 'MyAwesomeApp',
        'concept': '生産性向上ツール',
        'description': '開発者向けタスク管理アプリ',
        'urls': {
            'main': 'https://myapp.example.com',
            'github': 'https://github.com/user/myawesomeapp',
            'docs': 'https://docs.myapp.example.com'
        }
    }
    
    generator = ProfileGenerator()
    
    # 各プラットフォームでテスト
    platforms = ['twitter', 'bluesky', 'instagram', 'github']
    
    for platform in platforms:
        print(f"\n{'='*50}")
        print(f"🔍 {platform.upper()} プロフィール生成テスト")
        print(f"{'='*50}")
        
        profile = generator.generate_profile(platform, campaign_data)
        
        print(f"📱 Display Name: {profile.display_name}")
        print(f"📝 Bio ({profile.character_count}/{profile.character_limit} chars):")
        print(f"   {profile.bio}")
        print(f"🔗 Website: {profile.website_url}")
        
        if profile.additional_links:
            print(f"🔗 Additional Links:")
            for link in profile.additional_links:
                print(f"   - {link['title']}: {link['url']}")
        
        # 自然性チェック
        print(f"\n🔍 自然性チェック:")
        bio_lower = profile.bio.lower()
        
        # AetherPost関連の強制的な言及がないかチェック
        aetherpost_mentions = ['aetherpost', 'ai-generated', 'generated with', 'powered by aetherpost']
        forced_mentions = [mention for mention in aetherpost_mentions if mention in bio_lower]
        
        if forced_mentions:
            print(f"   ❌ 強制的なAetherPost言及を検出: {forced_mentions}")
        else:
            print(f"   ✅ AetherPostの強制言及なし")
        
        # キャンペーンURLが自然に含まれているかチェック
        urls_mentioned = []
        for url_type, url in campaign_data['urls'].items():
            if url in profile.bio or (profile.website_url and url in profile.website_url):
                urls_mentioned.append(url_type)
        
        if profile.additional_links:
            for link in profile.additional_links:
                for url_type, url in campaign_data['urls'].items():
                    if url == link['url']:
                        urls_mentioned.append(f"{url_type} (additional)")
        
        print(f"   📌 含まれるキャンペーンURL: {urls_mentioned}")
        
        if urls_mentioned:
            print(f"   ✅ ユーザー製品のURL自然挿入")
        else:
            print(f"   ⚠️  キャンペーンURLが含まれていない")

if __name__ == "__main__":
    test_natural_profile_generation()