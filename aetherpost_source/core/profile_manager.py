"""Profile management for social media platforms."""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .config.models import CampaignConfig

logger = logging.getLogger(__name__)

# Platform character limits
PLATFORM_LIMITS = {
    "twitter": {"name": 50, "bio": 160},
    "bluesky": {"name": 64, "bio": 256},
    "reddit": {"name": 20, "bio": 200},
    "youtube": {"name": 100, "bio": 1000},
    "instagram": {"name": 30, "bio": 150},
    "mastodon": {"name": 30, "bio": 500},
    "discord": {"name": 32, "bio": 190}
}

class ProfileManager:
    """Manages profile updates across social media platforms."""
    
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
    
    def optimize_for_platform(self, platform: str, profile: Dict[str, str]) -> Dict[str, str]:
        """Optimize profile content for platform limits."""
        limits = PLATFORM_LIMITS.get(platform, {"name": 50, "bio": 200})
        
        optimized = {}
        
        # Optimize display name
        name = profile.get("display_name", "")
        if len(name) > limits["name"]:
            name = name[:limits["name"]-3] + "..."
        optimized["display_name"] = name
        
        # Optimize bio
        bio = profile.get("bio", "")
        if len(bio) > limits["bio"]:
            bio = bio[:limits["bio"]-3] + "..."
        optimized["bio"] = bio
        
        # Keep other fields
        if "website" in profile:
            optimized["website"] = profile["website"]
        
        return optimized
    
    async def sync_profile(self, platform: str, profile: Dict[str, str]) -> Dict[str, Any]:
        """Sync profile to specific platform."""
        optimized = self.optimize_for_platform(platform, profile)
        
        if platform == "bluesky":
            return await self._sync_bluesky(optimized)
        elif platform == "twitter":
            return await self._sync_twitter(optimized)
        elif platform == "mastodon":
            return await self._sync_mastodon(optimized)
        elif platform == "instagram":
            return await self._sync_instagram(optimized)
        elif platform == "discord":
            return await self._sync_discord(optimized)
        else:
            return {
                "success": False,
                "platform": platform,
                "message": f"Profile sync not implemented for {platform}",
                "optimized": optimized
            }
    
    async def _sync_bluesky(self, profile: Dict[str, str]) -> Dict[str, Any]:
        """Sync profile to Bluesky."""
        handle = self.credentials.get('BLUESKY_HANDLE')
        password = self.credentials.get('BLUESKY_PASSWORD')
        
        if not handle or not password:
            return {"success": False, "platform": "bluesky", "message": "Missing credentials"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Login
                login_data = {'identifier': handle, 'password': password}
                async with session.post('https://bsky.social/xrpc/com.atproto.server.createSession', 
                                      json=login_data) as resp:
                    if resp.status != 200:
                        return {"success": False, "platform": "bluesky", "message": "Authentication failed"}
                    
                    auth_data = await resp.json()
                    access_token = auth_data['accessJwt']
                    did = auth_data['did']
                    headers = {'Authorization': f'Bearer {access_token}'}
                    
                    # Get current profile
                    async with session.get(
                        f'https://bsky.social/xrpc/com.atproto.repo.getRecord?repo={did}&collection=app.bsky.actor.profile&rkey=self',
                        headers=headers
                    ) as profile_resp:
                        current_profile = {}
                        if profile_resp.status == 200:
                            profile_data = await profile_resp.json()
                            current_profile = profile_data['value']
                    
                    # Update profile
                    new_profile = {
                        **current_profile,
                        'displayName': profile['display_name'],
                        'description': profile['bio']
                    }
                    
                    update_data = {
                        'repo': did,
                        'collection': 'app.bsky.actor.profile',
                        'rkey': 'self',
                        'record': new_profile
                    }
                    
                    async with session.post('https://bsky.social/xrpc/com.atproto.repo.putRecord',
                                          json=update_data, headers=headers) as update_resp:
                        if update_resp.status == 200:
                            return {
                                "success": True,
                                "platform": "bluesky",
                                "message": "Profile updated successfully",
                                "profile": profile
                            }
                        else:
                            error = await update_resp.text()
                            return {"success": False, "platform": "bluesky", "message": f"Update failed: {error}"}
        
        except Exception as e:
            logger.error(f"Bluesky profile sync error: {e}")
            return {"success": False, "platform": "bluesky", "message": str(e)}
    
    async def sync_all_profiles(self, platforms: list, profile: Dict[str, str]) -> list:
        """Sync profile to all specified platforms."""
        tasks = []
        for platform in platforms:
            tasks.append(self.sync_profile(platform, profile))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    "success": False,
                    "platform": platforms[i],
                    "message": str(result)
                })
            else:
                final_results.append(result)
        
        return final_results
    
    async def _sync_twitter(self, profile: Dict[str, str]) -> Dict[str, Any]:
        """Sync profile to Twitter."""
        try:
            import tweepy
        except ImportError:
            return {"success": False, "platform": "twitter", "message": "tweepy library not installed"}
        
        # Get credentials
        api_key = self.credentials.get('TWITTER_API_KEY')
        api_secret = self.credentials.get('TWITTER_API_SECRET')
        access_token = self.credentials.get('TWITTER_ACCESS_TOKEN')
        access_token_secret = self.credentials.get('TWITTER_ACCESS_TOKEN_SECRET')
        
        if not all([api_key, api_secret, access_token, access_token_secret]):
            return {"success": False, "platform": "twitter", "message": "Missing Twitter credentials"}
        
        try:
            # Setup Twitter API client
            client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Update profile
            client.update_profile(
                name=profile['display_name'],
                description=profile['bio'],
                url=profile.get('website', '')
            )
            
            return {
                "success": True,
                "platform": "twitter",
                "message": "Profile updated successfully",
                "profile": profile
            }
            
        except Exception as e:
            logger.error(f"Twitter profile sync error: {e}")
            return {"success": False, "platform": "twitter", "message": str(e)}
    
    async def _sync_mastodon(self, profile: Dict[str, str]) -> Dict[str, Any]:
        """Sync profile to Mastodon."""
        instance_url = self.credentials.get('MASTODON_INSTANCE_URL')
        access_token = self.credentials.get('MASTODON_ACCESS_TOKEN')
        
        if not instance_url or not access_token:
            return {"success": False, "platform": "mastodon", "message": "Missing Mastodon credentials"}
        
        # Ensure instance URL has proper format
        if not instance_url.startswith(("http://", "https://")):
            instance_url = f"https://{instance_url}"
        
        try:
            from urllib.parse import urljoin
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Update profile data
            update_data = {
                "display_name": profile['display_name'],
                "note": profile['bio']
            }
            
            # Add website if provided
            if profile.get('website'):
                # Mastodon profile fields
                update_data["fields_attributes"] = [
                    {"name": "Website", "value": profile['website']}
                ]
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    urljoin(instance_url, "/api/v1/accounts/update_credentials"),
                    json=update_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "platform": "mastodon",
                            "message": "Profile updated successfully",
                            "profile": profile
                        }
                    else:
                        error = await response.text()
                        return {"success": False, "platform": "mastodon", "message": f"Update failed: {error}"}
        
        except Exception as e:
            logger.error(f"Mastodon profile sync error: {e}")
            return {"success": False, "platform": "mastodon", "message": str(e)}
    
    async def _sync_instagram(self, profile: Dict[str, str]) -> Dict[str, Any]:
        """Sync profile to Instagram."""
        access_token = self.credentials.get('INSTAGRAM_ACCESS_TOKEN')
        business_account_id = self.credentials.get('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        
        if not access_token or not business_account_id:
            return {"success": False, "platform": "instagram", "message": "Missing Instagram credentials"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Instagram Graph API endpoint for updating business profile
                url = f"https://graph.facebook.com/v18.0/{business_account_id}"
                
                # Instagram Business profile update data
                update_data = {
                    "biography": profile['bio'],
                    "access_token": access_token
                }
                
                # Add website if provided
                if profile.get('website'):
                    update_data["website"] = profile['website']
                
                async with session.post(url, data=update_data) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "platform": "instagram",
                            "message": "Profile updated successfully",
                            "profile": profile
                        }
                    else:
                        error = await response.text()
                        return {"success": False, "platform": "instagram", "message": f"Update failed: {error}"}
        
        except Exception as e:
            logger.error(f"Instagram profile sync error: {e}")
            return {"success": False, "platform": "instagram", "message": str(e)}
    
    async def _sync_discord(self, profile: Dict[str, str]) -> Dict[str, Any]:
        """Sync profile to Discord (Note: Discord has limited profile update capabilities)."""
        bot_token = self.credentials.get('DISCORD_BOT_TOKEN')
        
        if not bot_token:
            return {"success": False, "platform": "discord", "message": "Missing Discord bot token"}
        
        # Note: Discord doesn't support direct profile updates like other platforms
        # This is a placeholder for potential future Discord integrations
        # Discord bots can update their own username and status, but not bio/description
        
        try:
            headers = {
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json"
            }
            
            # Discord bot can only update its own username (limited to 2 times per hour)
            # This is mainly for bot profile updates, not user profiles
            update_data = {
                "username": profile['display_name'][:32]  # Discord username limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    "https://discord.com/api/v10/users/@me",
                    json=update_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "platform": "discord",
                            "message": "Bot profile updated successfully (note: Discord has limited profile update capabilities)",
                            "profile": profile,
                            "note": "Only bot username can be updated. Bio/description updates not supported by Discord API."
                        }
                    else:
                        error = await response.text()
                        return {"success": False, "platform": "discord", "message": f"Update failed: {error}"}
        
        except Exception as e:
            logger.error(f"Discord profile sync error: {e}")
            return {"success": False, "platform": "discord", "message": str(e)}