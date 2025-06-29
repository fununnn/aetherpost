"""Content generation engine using AI providers."""

import asyncio
import hashlib
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..config.models import CampaignConfig, CredentialsConfig
from ..context import ProjectContextReader, ProjectDiffDetector


class ContentGenerator:
    """Generate social media content using AI providers."""
    
    def __init__(self, credentials: CredentialsConfig):
        self.credentials = credentials
        self.ai_providers = {}
        self.cache_dir = Path(".aetherpost/content_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize project context systems
        self.context_reader = ProjectContextReader()
        self.diff_detector = ProjectDiffDetector()
        
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup available AI providers using direct imports."""
        # Setup [AI Service] if credentials available
        if self.credentials.ai_service and self.credentials.ai_service.get("api_key"):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=self.credentials.ai_service["api_key"])
                self.ai_providers["anthropic"] = {
                    "client": client,
                    "type": "anthropic"
                }
            except ImportError:
                print("Anthropic library not available. Install with: pip install anthropic")
            except Exception as e:
                print(f"Failed to setup Anthropic provider: {e}")
        
        # Setup OpenAI if credentials available  
        if self.credentials.openai and self.credentials.openai.get("api_key"):
            try:
                import openai
                client = openai.OpenAI(api_key=self.credentials.openai["api_key"])
                self.ai_providers["openai"] = {
                    "client": client,
                    "type": "openai"
                }
            except ImportError:
                print("OpenAI library not available. Install with: pip install openai")
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
        language = config.content.language
        
        # Platform-specific constraints
        char_limit = self._get_platform_char_limit(platform)
        platform_features = self._get_platform_features(platform)
        
        # Build style-specific instructions
        style_instructions = self._get_style_instructions(style)
        
        # Language-specific instructions
        language_instructions = self._get_language_instructions(language)
        
        # Get project context and diff information
        project_context_text = self._get_project_context_text()
        project_diff_text = self._get_project_diff_text()
        
        # Build context-aware prompt
        base_prompt = f"""Create an engaging social media post for {platform} about the following:

App/Service: {config.name}
Description: {config.concept}
{f'URL: {config.url}' if config.url else ''}

{project_context_text}

{project_diff_text}

Style Guidelines:
- Tone: {style}
- Call to action: {action}
- Character limit: {char_limit}
- Platform: {platform}
- Language: Write ENTIRELY in {self._get_language_name(language)} ({language})

{language_instructions}

{style_instructions}

{platform_features}

Requirements:
- Write the ENTIRE post in {self._get_language_name(language)}
- Use the project context and recent changes to make the post specific and relevant
- If significant changes were detected, focus on those updates
- Make it engaging and shareable
- Include the call to action naturally
- {'Use appropriate hashtags' if platform != 'twitter' else 'Limit hashtags (Twitter style)'}
- Keep it authentic and not overly promotional
- Use culturally appropriate expressions for {self._get_language_name(language)} speakers
- Be specific about features, improvements, or recent developments when available

Generate only the post text, no explanations or additional commentary."""
        
        prompt = base_prompt
        
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
    
    def _get_language_name(self, language_code: str) -> str:
        """Get full language name from ISO code."""
        language_names = {
            'en': 'English',
            'ja': 'Japanese (日本語)',
            'es': 'Spanish (Español)',
            'fr': 'French (Français)',
            'de': 'German (Deutsch)',
            'it': 'Italian (Italiano)',
            'pt': 'Portuguese (Português)',
            'ru': 'Russian (Русский)',
            'ko': 'Korean (한국어)',
            'zh': 'Chinese (中文)',
            'ar': 'Arabic (العربية)',
            'hi': 'Hindi (हिन्दी)',
            'th': 'Thai (ไทย)',
            'vi': 'Vietnamese (Tiếng Việt)',
            'tr': 'Turkish (Türkçe)',
            'nl': 'Dutch (Nederlands)',
            'sv': 'Swedish (Svenska)',
            'da': 'Danish (Dansk)',
            'no': 'Norwegian (Norsk)',
            'fi': 'Finnish (Suomi)'
        }
        return language_names.get(language_code, language_code.upper())
    
    def _get_language_instructions(self, language_code: str) -> str:
        """Get language-specific writing instructions."""
        instructions = {
            'en': """Language Instructions for ENGLISH:
- Use natural, native English expressions
- Follow standard English grammar and punctuation
- Use appropriate English idioms and phrases""",
            
            'ja': """Language Instructions for JAPANESE (日本語):
- 自然な日本語表現を使用してください
- 適切な敬語・丁寧語を使用してください
- カタカナ、ひらがな、漢字を適切に混在させてください
- 日本の文化に適した表現を使用してください
- ハッシュタグは英語でも日本語でも適切な方を選択してください""",
            
            'es': """Language Instructions for SPANISH (Español):
- Use natural Spanish expressions and idioms
- Follow proper Spanish grammar and accent marks
- Use appropriate formal/informal register
- Consider regional variations if applicable""",
            
            'fr': """Language Instructions for FRENCH (Français):
- Use natural French expressions and idioms
- Follow proper French grammar and accent marks
- Use appropriate formal/informal register
- Consider cultural nuances in French-speaking regions""",
            
            'de': """Language Instructions for GERMAN (Deutsch):
- Use natural German expressions and compound words
- Follow proper German grammar and capitalization
- Use appropriate formal/informal register (Sie/du)
- Consider Austrian/Swiss variations if applicable""",
            
            'ko': """Language Instructions for KOREAN (한국어):
- 자연스러운 한국어 표현을 사용해주세요
- 적절한 존댓말/반말을 사용해주세요
- 한국 문화에 맞는 표현을 사용해주세요
- 한글과 영어를 적절히 혼용해주세요""",
            
            'zh': """Language Instructions for CHINESE (中文):
- 使用自然的中文表达方式
- 遵循正确的中文语法和标点符号
- 使用适当的正式/非正式语调
- 考虑简体中文的使用习惯""",
            
            'pt': """Language Instructions for PORTUGUESE (Português):
- Use natural Portuguese expressions and idioms
- Follow proper Portuguese grammar and accent marks
- Consider Brazilian vs European Portuguese variations
- Use appropriate formal/informal register""",
            
            'ru': """Language Instructions for RUSSIAN (Русский):
- Используйте естественные русские выражения
- Следуйте правильной русской грамматике
- Используйте соответствующий формальный/неформальный регистр
- Учитывайте культурные особенности""",
            
            'ar': """Language Instructions for ARABIC (العربية):
- استخدم التعبيرات العربية الطبيعية
- اتبع القواعد النحوية العربية الصحيحة
- استخدم الأسلوب الرسمي/غير الرسمي المناسب
- راع الاختلافات الثقافية في المنطقة العربية"""
        }
        
        return instructions.get(language_code, instructions['en'])
    
    async def _generate_text(self, 
                           prompt: str, 
                           config: CampaignConfig, 
                           platform: str) -> str:
        """Generate text content using AI providers."""
        
        # Try providers in order of preference
        providers_to_try = ["anthropic", "openai"]
        
        for provider_name in providers_to_try:
            if provider_name in self.ai_providers:
                try:
                    provider = self.ai_providers[provider_name]
                    client = provider["client"]
                    provider_type = provider["type"]
                    
                    # Generate text based on provider type
                    if provider_type == "anthropic":
                        response = client.messages.create(
                            model="claude-3-haiku-20240307",
                            max_tokens=min(300, self._get_platform_char_limit(platform) + 50),
                            temperature=0.0,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        text = response.content[0].text
                    
                    elif provider_type == "openai":
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            max_tokens=min(300, self._get_platform_char_limit(platform) + 50),
                            temperature=0.0,
                            seed=42,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        text = response.choices[0].message.content
                    
                    else:
                        continue
                    
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
                client = provider["client"]
                
                # Build image prompt
                image_prompt = f"Create a promotional image for {config.name}: {config.concept}. Modern, clean design, suitable for social media."
                
                # Generate image using DALL-E
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=image_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                
                # Download the image
                import requests
                image_url = response.data[0].url
                image_response = requests.get(image_url)
                
                if image_response.status_code == 200:
                    # Save image
                    media_dir = Path("media")
                    media_dir.mkdir(exist_ok=True)
                    
                    image_path = media_dir / f"{config.name}_{platform}_generated.png"
                    with open(image_path, "wb") as f:
                        f.write(image_response.content)
                    
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
            "max_length": config.content.max_length,
            "language": config.content.language
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
    
    def _get_project_context_text(self) -> str:
        """
        Get project context information for AI prompt.
        
        Returns:
            Formatted project context text or empty string
        """
        try:
            # Read project context
            context = self.context_reader.read_project_context()
            
            if not context or not context.files:
                return ""
            
            # Get context summary
            summary = self.context_reader.get_file_summary(context)
            
            # Format context for AI prompt
            context_text = "Project Context:\n"
            
            if "file_contents" in summary:
                # For small projects, include actual file contents
                context_text += "Recent project files:\n"
                for file_path, content in summary["file_contents"].items():
                    context_text += f"\n{file_path}:\n```\n{content}\n```\n"
            elif "file_structure" in summary:
                # For larger projects, include structure
                context_text += f"Project structure ({summary['total_files']} files):\n"
                context_text += "\n".join(f"- {path}" for path in summary["file_structure"][:10])
                if summary['total_files'] > 10:
                    context_text += f"\n... and {summary['total_files'] - 10} more files"
            
            # Add file type information
            if summary.get("file_types"):
                context_text += "\n\nProject composition:\n"
                for ext, count in summary["file_types"].items():
                    if ext == "no_extension":
                        context_text += f"- {count} files without extension\n"
                    else:
                        context_text += f"- {count} {ext} files\n"
            
            return context_text
            
        except Exception as e:
            # If context reading fails, continue without context
            return ""
    
    def _get_project_diff_text(self) -> str:
        """
        Get project difference information for AI prompt.
        
        Returns:
            Formatted project diff text or empty string
        """
        try:
            # Detect changes since last run
            diff = self.diff_detector.detect_changes()
            
            if not diff or not diff.has_significant_changes:
                return ""
            
            # Get diff summary
            summary = self.diff_detector.get_changes_summary(diff)
            
            # Format diff information for AI prompt
            diff_text = "Recent Changes:\n"
            
            if summary.get("first_scan"):
                diff_text += "This is the first scan of the project.\n"
            else:
                time_info = summary.get("time_since_last_scan", {})
                if time_info.get("hours", 0) < 24:
                    diff_text += f"Changes detected in the last {time_info.get('hours', 0):.1f} hours:\n"
                else:
                    diff_text += f"Changes detected in the last {time_info.get('days', 0):.1f} days:\n"
            
            # Add change statistics
            change_types = summary.get("change_types", {})
            if change_types.get("added", 0) > 0:
                diff_text += f"- {change_types['added']} new files added\n"
            if change_types.get("modified", 0) > 0:
                diff_text += f"- {change_types['modified']} files modified\n"
            if change_types.get("deleted", 0) > 0:
                diff_text += f"- {change_types['deleted']} files deleted\n"
            
            # Add detailed changes for small changesets
            if "detailed_changes" in summary:
                diff_text += "\nSpecific changes:\n"
                for change in summary["detailed_changes"]:
                    file_name = change["file"]
                    change_type = change["type"]
                    diff_text += f"- {file_name} ({change_type})\n"
            elif "affected_files" in summary:
                # For larger changesets, list some affected files
                affected = summary["affected_files"]
                if affected.get("added"):
                    diff_text += f"\nNew files: {', '.join(affected['added'])}"
                    if affected.get("added_truncated"):
                        diff_text += f" {affected['added_truncated']}"
                    diff_text += "\n"
                if affected.get("modified"):
                    diff_text += f"Modified files: {', '.join(affected['modified'])}"
                    if affected.get("modified_truncated"):
                        diff_text += f" {affected['modified_truncated']}"
                    diff_text += "\n"
            
            return diff_text
            
        except Exception as e:
            # If diff detection fails, continue without diff info
            return ""