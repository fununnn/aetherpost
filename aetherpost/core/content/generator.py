"""Content generation engine using AI providers."""

import asyncio
import hashlib
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..config.models import CampaignConfig, CredentialsConfig
from ...plugins.manager import plugin_manager


class ContentGenerator:
    """Generate social media content using AI providers."""
    
    def __init__(self, credentials: CredentialsConfig):
        self.credentials = credentials
        self.ai_providers = {}
        self.cache_dir = Path(".aetherpost/content_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup available AI providers."""
        # Setup [AI Service] if credentials available
        if self.credentials.ai_service and self.credentials.ai_service.get("api_key"):
            try:
                ai_provider = plugin_manager.load_ai_provider(
                    "ai_service", 
                    self.credentials.ai_service
                )
                self.ai_providers["[AI Service]"] = ai_provider
            except Exception as e:
                print(f"Failed to setup [AI Service] provider: {e}")
        
        # Setup OpenAI if credentials available  
        if self.credentials.openai and self.credentials.openai.get("api_key"):
            try:
                openai_provider = plugin_manager.load_ai_provider(
                    "openai",
                    self.credentials.openai
                )
                self.ai_providers["openai"] = openai_provider
            except Exception as e:
                print(f"Failed to setup OpenAI provider: {e}")
    
    async def generate_content(self, 
                             config: CampaignConfig, 
                             platform: str,
                             variant_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate content for a specific platform."""
        
        # Check cache first for idempotency
        cache_key = self._get_cache_key(config, platform, variant_id)
        cached_content = self._get_cached_content(cache_key)
        
        if cached_content:
            return cached_content
        
        # Build prompt based on config and platform
        prompt = self._build_prompt(config, platform, variant_id)
        
        # Generate text content
        text = await self._generate_text(prompt, config, platform)
        
        # Generate or prepare media if needed
        media = await self._prepare_media(config, platform)
        
        # Generate hashtags if needed
        hashtags = self._generate_hashtags(config, platform)
        
        content = {
            "text": text,
            "media": media,
            "hashtags": hashtags,
            "platform": platform,
            "variant_id": variant_id
        }
        
        # Cache the result for idempotency
        self._cache_content(cache_key, content)
        
        return content
    
    def _build_prompt(self, 
                     config: CampaignConfig, 
                     platform: str,
                     variant_id: Optional[str] = None) -> str:
        """Build AI prompt for content generation."""
        
        # Get variant-specific settings if applicable
        variant_config = None
        if variant_id and config.experiments:
            for variant in config.experiments.variants:
                if variant.get("id") == variant_id:
                    variant_config = variant
                    break
        
        # Use variant settings or defaults
        style = variant_config.get("style") if variant_config else config.content.style
        action = variant_config.get("action") if variant_config else config.content.action
        
        # Platform-specific constraints
        char_limit = self._get_platform_char_limit(platform)
        platform_features = self._get_platform_features(platform)
        
        # Build style-specific instructions
        style_instructions = self._get_style_instructions(style)
        
        prompt = f"""Create an engaging social media post for {platform} about the following:

App/Service: {config.name}
Description: {config.concept}
{f'URL: {config.url}' if config.url else ''}

Style Guidelines:
- Tone: {style}
- Call to action: {action}
- Character limit: {char_limit}
- Platform: {platform}

{style_instructions}

{platform_features}

Requirements:
- Make it engaging and shareable
- Include the call to action naturally
- {'Use appropriate hashtags' if platform != 'twitter' else 'Limit hashtags (Twitter style)'}
- Keep it authentic and not overly promotional

Generate only the post text, no explanations or additional commentary."""
        
        return prompt
    
    def _get_platform_char_limit(self, platform: str) -> int:
        """Get character limit for platform."""
        limits = {
            "twitter": 280,
            "bluesky": 300,
            "mastodon": 500,
            "linkedin": 1300,
            "discord": 2000
        }
        return limits.get(platform, 280)
    
    def _get_platform_features(self, platform: str) -> str:
        """Get platform-specific feature guidelines."""
        features = {
            "twitter": "- Use threads if content is longer\n- Hashtags are less important\n- Retweets and engagement are key",
            "bluesky": "- Similar to Twitter but slightly more relaxed\n- Community-focused\n- Less corporate tone works well",
            "mastodon": "- Longer posts allowed\n- Community and tech-focused audience\n- Content warnings if applicable",
            "linkedin": "- Professional tone required\n- Industry insights valued\n- Longer, more detailed posts work well",
            "discord": "- Casual, community tone\n- Interactive and engaging\n- Can be longer and more conversational"
        }
        return features.get(platform, "")
    
    def _get_style_instructions(self, style: str) -> str:
        """Get detailed instructions for specific writing styles."""
        style_guides = {
            "casual": """Style Instructions for CASUAL tone:
- Use friendly, conversational language
- Include 2-3 emojis strategically placed
- Use contractions (we're, it's, you'll)
- Sound like talking to a friend
- Be enthusiastic but not overly excited
- Use simple, accessible vocabulary""",
            
            "professional": """Style Instructions for PROFESSIONAL tone:
- Use formal, business-appropriate language
- Avoid emojis entirely
- Use complete sentences with proper grammar
- Focus on value proposition and benefits
- Use industry-standard terminology
- Be authoritative and confident
- Avoid casual expressions or slang""",
            
            "technical": """Style Instructions for TECHNICAL tone:
- Use developer/technical terminology appropriately
- Focus on features, capabilities, and specifications
- Be precise and specific about functionality
- Use minimal emojis (1 max, if any)
- Mention technical benefits or architecture
- Appeal to technically-minded audience
- Be informative and detailed within character limits""",
            
            "humorous": """Style Instructions for HUMOROUS tone:
- Use wit, wordplay, or light humor
- Make relatable jokes about the problem you solve
- Use playful language and unexpected metaphors
- Include 1-2 fun emojis that add to the humor
- Be self-aware but not self-deprecating
- Make the audience smile or chuckle
- Keep humor appropriate and inclusive"""
        }
        
        return style_guides.get(style, style_guides["casual"])
    
    async def _generate_text(self, 
                           prompt: str, 
                           config: CampaignConfig, 
                           platform: str) -> str:
        """Generate text content using AI providers."""
        
        # Try providers in order of preference
        providers_to_try = ["[AI Service]", "openai"]
        
        for provider_name in providers_to_try:
            if provider_name in self.ai_providers:
                try:
                    provider = self.ai_providers[provider_name]
                    
                    # Configure generation parameters for deterministic output (idempotency)
                    generation_config = {
                        "max_tokens": min(300, self._get_platform_char_limit(platform) + 50),
                        "temperature": 0.0,  # Deterministic generation for idempotency
                        "seed": 42  # Fixed seed for consistent results
                    }
                    
                    text = await provider.generate_text(prompt, generation_config)
                    
                    # Validate length
                    char_limit = self._get_platform_char_limit(platform)
                    if len(text) <= char_limit:
                        return text.strip()
                    else:
                        # Try to trim if slightly over limit
                        if len(text) <= char_limit + 20:
                            sentences = text.split('. ')
                            trimmed = '. '.join(sentences[:-1])
                            if len(trimmed) <= char_limit:
                                return trimmed.strip()
                
                except Exception as e:
                    print(f"Failed to generate with {provider_name}: {e}")
                    continue
        
        # Fallback to template-based generation
        return self._generate_fallback_content(config, platform)
    
    def _generate_fallback_content(self, config: CampaignConfig, platform: str) -> str:
        """Generate fallback content using style-appropriate templates."""
        templates = {
            "casual": "🚀 Introducing {name} - {concept}! {action} ✨",
            "professional": "Announcing {name}: {concept}. {action}.",
            "technical": "New release: {name}. {concept}. {action}",
            "humorous": "Meet {name} - the app that finally gets it! {concept} 😄 {action} (You're welcome!)"
        }
        
        template = templates.get(config.content.style, templates["casual"])
        
        content = template.format(
            name=config.name,
            concept=config.concept,
            action=config.content.action
        )
        
        # Add URL if provided and fits
        if config.url:
            test_content = f"{content}\n\n{config.url}"
            if len(test_content) <= self._get_platform_char_limit(platform):
                content = test_content
        
        return content
    
    async def _prepare_media(self, config: CampaignConfig, platform: str) -> List[str]:
        """Prepare media files for posting."""
        media_files = []
        
        if not config.image:
            return media_files
        
        if config.image == "generate":
            # Generate image using AI
            media_file = await self._generate_image(config, platform)
            if media_file:
                media_files.append(media_file)
        
        elif config.image == "auto":
            # Auto-discover screenshots or images
            media_files = self._discover_media_files()
        
        elif config.image.startswith("./") or Path(config.image).exists():
            # Use specific file
            if Path(config.image).exists():
                media_files.append(config.image)
        
        return media_files
    
    async def _generate_image(self, config: CampaignConfig, platform: str) -> Optional[str]:
        """Generate image using AI providers."""
        
        # Try OpenAI DALL-E if available
        if "openai" in self.ai_providers:
            try:
                provider = self.ai_providers["openai"]
                
                # Build image prompt
                image_prompt = f"Create a promotional image for {config.name}: {config.concept}. Modern, clean design, suitable for social media."
                
                # Generate image
                image_data = await provider.generate_image(image_prompt, {
                    "size": "1024x1024",
                    "quality": "standard"
                })
                
                # Save image
                media_dir = Path("media")
                media_dir.mkdir(exist_ok=True)
                
                image_path = media_dir / f"{config.name}_{platform}_generated.png"
                with open(image_path, "wb") as f:
                    f.write(image_data)
                
                return str(image_path)
            
            except Exception as e:
                print(f"Failed to generate image: {e}")
        
        return None
    
    def _discover_media_files(self) -> List[str]:
        """Auto-discover media files in common locations."""
        media_files = []
        
        # Common screenshot/media directories
        search_dirs = [Path("."), Path("screenshots"), Path("media"), Path("assets")]
        extensions = [".png", ".jpg", ".jpeg", ".gif", ".mp4"]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for ext in extensions:
                    files = list(search_dir.glob(f"*{ext}"))
                    media_files.extend([str(f) for f in files[:2]])  # Limit to 2 files
        
        return media_files[:4]  # Most platforms limit to 4 media items
    
    def _generate_hashtags(self, config: CampaignConfig, platform: str) -> List[str]:
        """Generate or use configured hashtags."""
        hashtags = []
        
        # Use configured hashtags if available
        if config.content.hashtags:
            hashtags.extend(config.content.hashtags)
        else:
            # Generate basic hashtags based on config
            if "AI" in config.concept or "ai" in config.concept.lower():
                hashtags.append("#AI")
            
            if "app" in config.concept.lower():
                hashtags.append("#app")
            
            if "productivity" in config.concept.lower():
                hashtags.append("#productivity")
            
            # Add generic launch hashtag
            hashtags.append("#launch")
        
        # Platform-specific hashtag limits
        if platform == "twitter":
            hashtags = hashtags[:2]  # Twitter works better with fewer hashtags
        elif platform == "instagram":
            hashtags = hashtags[:10]  # Instagram allows more
        
        return hashtags
    
    def _get_cache_key(self, config: CampaignConfig, platform: str, variant_id: Optional[str] = None) -> str:
        """Generate cache key based on config parameters for idempotency."""
        # Create a deterministic hash based on relevant config parameters
        cache_data = {
            "name": config.name,
            "concept": config.concept,
            "url": config.url,
            "platform": platform,
            "variant_id": variant_id,
            "style": config.content.style,
            "action": config.content.action,
            "hashtags": config.content.hashtags,
            "max_length": config.content.max_length
        }
        
        # Convert to JSON string and hash for consistent key
        cache_str = json.dumps(cache_data, sort_keys=True, ensure_ascii=True)
        return hashlib.md5(cache_str.encode('utf-8')).hexdigest()
    
    def _get_cached_content(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached content if available."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Remove corrupted cache file
                cache_file.unlink(missing_ok=True)
        
        return None
    
    def _cache_content(self, cache_key: str, content: Dict[str, Any]) -> None:
        """Cache generated content for future idempotent access."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        except IOError:
            # If caching fails, continue without caching
            pass