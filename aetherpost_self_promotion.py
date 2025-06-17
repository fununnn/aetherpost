#!/usr/bin/env python3
"""
AetherPost Self-Promotion Script

Uses AetherPost's own features to promote AetherPost itself.
A meta-example of dogfooding the product.

Usage:
    python aetherpost_self_promotion.py
    ./scripts/self_promote.sh

Requires:
    - .env file with platform credentials
    - Optional: OpenAI API key for enhanced content generation
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import random

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aetherpost.core.content.generator import ContentGenerator
from aetherpost.plugins.connectors.twitter.connector import TwitterConnector
from aetherpost.plugins.connectors.bluesky.connector import BlueskyConnector
from aetherpost.plugins.connectors.mastodon.connector import MastodonConnector
from aetherpost.plugins.connectors.reddit.connector import RedditConnector


class CampaignType(Enum):
    """Available promotion campaign types."""
    LAUNCH_ANNOUNCEMENT = "launch_announcement"
    FEATURE_HIGHLIGHTS = "feature_highlights"
    COMMUNITY_BUILDING = "community_building"
    TECHNICAL_CONTENT = "technical_content"


@dataclass
class PromotionContent:
    """Generated promotional content with metadata."""
    text: str
    hashtags: List[str]
    platforms: List[str]
    campaign_type: str
    generated_at: datetime


@dataclass
class PostResult:
    """Result of posting to a platform."""
    platform: str
    status: str  # 'published', 'failed', 'skipped'
    url: Optional[str] = None
    error: Optional[str] = None


class PlatformConnectorManager:
    """Manages platform connectors and credentials."""
    
    def __init__(self):
        self.connectors: Dict[str, Any] = {}
        self._required_credentials = {
            "twitter": ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"],
            "bluesky": ["BLUESKY_IDENTIFIER", "BLUESKY_PASSWORD"],
            "mastodon": ["MASTODON_ACCESS_TOKEN"],
            "reddit": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]
        }
    
    async def setup_connectors(self, credentials_file: str = ".env") -> bool:
        """Setup platform connectors using environment variables.
        
        Args:
            credentials_file: Path to environment file
            
        Returns:
            True if at least one connector was setup successfully
        """
        print("🔧 Setting up platform connectors...")
        
        try:
            from dotenv import load_dotenv
            load_dotenv(credentials_file)
            
            await self._setup_twitter()
            await self._setup_bluesky()
            await self._setup_mastodon()
            await self._setup_reddit()
            
            if not self.connectors:
                print("❌ No platform credentials found. Please check your .env file.")
                return False
            
            print(f"✅ Setup {len(self.connectors)} platform connector(s)")
            return True
        
        except Exception as e:
            print(f"❌ Error setting up connectors: {e}")
            return False
    
    async def _setup_twitter(self) -> None:
        """Setup Twitter connector if credentials are available."""
        if self._has_credentials("twitter"):
            self.connectors["twitter"] = TwitterConnector({
                "api_key": os.getenv("TWITTER_API_KEY"),
                "api_secret": os.getenv("TWITTER_API_SECRET"),
                "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
                "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
            })
            print("✅ Twitter connector ready")
    
    async def _setup_bluesky(self) -> None:
        """Setup Bluesky connector if credentials are available."""
        if self._has_credentials("bluesky"):
            self.connectors["bluesky"] = BlueskyConnector({
                "identifier": os.getenv("BLUESKY_IDENTIFIER"),
                "password": os.getenv("BLUESKY_PASSWORD")
            })
            print("✅ Bluesky connector ready")
    
    async def _setup_mastodon(self) -> None:
        """Setup Mastodon connector if credentials are available."""
        if os.getenv("MASTODON_ACCESS_TOKEN"):
            self.connectors["mastodon"] = MastodonConnector({
                "access_token": os.getenv("MASTODON_ACCESS_TOKEN"),
                "api_base_url": os.getenv("MASTODON_API_BASE_URL", "https://mastodon.social")
            })
            print("✅ Mastodon connector ready")
    
    async def _setup_reddit(self) -> None:
        """Setup Reddit connector if credentials are available."""
        if self._has_credentials("reddit"):
            self.connectors["reddit"] = RedditConnector({
                "client_id": os.getenv("REDDIT_CLIENT_ID"),
                "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
                "username": os.getenv("REDDIT_USERNAME"),
                "password": os.getenv("REDDIT_PASSWORD")
            })
            print("✅ Reddit connector ready")
    
    def _has_credentials(self, platform: str) -> bool:
        """Check if all required credentials are available for a platform."""
        required = self._required_credentials.get(platform, [])
        return all(os.getenv(key) for key in required)
    
    def get_available_platforms(self) -> List[str]:
        """Get list of platforms with active connectors."""
        return list(self.connectors.keys())


class PromotionCampaignManager:
    """Manages promotion campaign templates and content generation."""
    
    def __init__(self):
        self.campaigns = self._load_campaign_templates()
    
    def _load_campaign_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined campaign templates."""
        return {
            CampaignType.LAUNCH_ANNOUNCEMENT.value: {
                "concept": "AetherPost - The developer-friendly social media automation tool",
                "themes": [
                    "🚀 Open source social media automation for developers",
                    "🤖 AI-powered content generation with OpenAI integration",
                    "📱 Multi-platform posting: Twitter, Bluesky, Mastodon, Reddit",
                    "⚡ Simple CLI interface - no complex dashboards needed",
                    "🔒 Privacy-first - run entirely on your own infrastructure",
                    "💻 Built by developers, for developers",
                    "🆓 Free and open source - no vendor lock-in"
                ],
                "platforms": ["twitter", "bluesky", "mastodon", "reddit"],
                "tone": "casual",
                "hashtags": ["#OpenSource", "#SocialMediaAutomation", "#Developer", "#CLI", "#Python"]
            },
            CampaignType.FEATURE_HIGHLIGHTS.value: {
                "concept": "AetherPost key features that solve real problems",
                "themes": [
                    "🎯 Reddit optimization: automatically finds relevant subreddits and adapts content",
                    "🧠 Smart content generation: AI creates platform-specific posts",
                    "📊 Built-in analytics: track performance without external tools",
                    "🔧 Developer-friendly: YAML configuration, Git-compatible",
                    "🚀 Quick setup: 'aetherpost init' and you're ready to go",
                    "🌐 Multi-platform: one content, multiple platforms automatically",
                    "💡 HackerNews integration: stay on top of tech trends"
                ],
                "platforms": ["twitter", "reddit"],
                "tone": "technical",
                "hashtags": ["#DevTools", "#Automation", "#ProductivityTools", "#OpenSource"]
            },
            CampaignType.COMMUNITY_BUILDING.value: {
                "concept": "Building the AetherPost community and gathering feedback",
                "themes": [
                    "📢 What features would you like to see in AetherPost?",
                    "🤝 Looking for contributors to help build the future of social media automation",
                    "💬 Join our community - we're building something cool together",
                    "🐛 Found a bug? Feature request? We're all ears!",
                    "⭐ If AetherPost helped you, a GitHub star would mean the world",
                    "📖 Check out our docs and examples at docs.aetherpost.dev",
                    "🎉 Success story: How are you using AetherPost?"
                ],
                "platforms": ["twitter", "bluesky", "mastodon", "reddit"],
                "tone": "friendly",
                "hashtags": ["#Community", "#OpenSource", "#Feedback", "#GitHub"]
            },
            CampaignType.TECHNICAL_CONTENT.value: {
                "concept": "Technical deep-dives and tutorials for AetherPost",
                "themes": [
                    "🔧 Tutorial: Setting up Reddit automation with AetherPost",
                    "⚙️ How AetherPost's subreddit optimization algorithm works",
                    "🤖 Integrating OpenAI for smarter content generation",
                    "📱 Multi-platform content strategy with AetherPost",
                    "🛠️ Contributing to AetherPost: Developer's guide",
                    "🚀 Deploying AetherPost: From local to production",
                    "📊 Measuring social media ROI with AetherPost analytics"
                ],
                "platforms": ["reddit", "twitter"],
                "tone": "technical",
                "hashtags": ["#Tutorial", "#HowTo", "#DevTools", "#API", "#Automation"]
            }
        }
    
    def get_campaign(self, campaign_type: str) -> Dict[str, Any]:
        """Get campaign template by type."""
        return self.campaigns.get(campaign_type, self.campaigns[CampaignType.LAUNCH_ANNOUNCEMENT.value])
    
    def get_random_theme(self, campaign_type: str) -> str:
        """Get a random theme from the specified campaign."""
        campaign = self.get_campaign(campaign_type)
        return random.choice(campaign["themes"])
    
    def list_campaigns(self) -> List[Tuple[str, str]]:
        """List available campaigns with their concepts."""
        return [(key, campaign["concept"]) for key, campaign in self.campaigns.items()]


class AetherPostSelfPromotion:
    """Self-promotion engine for AetherPost using its own capabilities.
    
    This class orchestrates the entire self-promotion workflow:
    1. Setup platform connectors
    2. Generate promotional content
    3. Post to multiple platforms
    4. Track results and metrics
    """
    
    def __init__(self):
        self.connector_manager = PlatformConnectorManager()
        self.campaign_manager = PromotionCampaignManager()
        self.content_generator = None  # Will be initialized after credentials are loaded
        self._rate_limit_delay = 2  # seconds between posts
    
    async def setup_connectors(self, credentials_file: str = ".env") -> bool:
        """Setup platform connectors and content generator.
        
        Args:
            credentials_file: Path to environment file
            
        Returns:
            True if setup was successful
        """
        # Setup platform connectors
        connector_success = await self.connector_manager.setup_connectors(credentials_file)
        
        # Setup content generator with minimal credentials for testing
        try:
            from dotenv import load_dotenv
            load_dotenv(credentials_file)
            
            # Create minimal credentials config for content generator
            from aetherpost.core.config.models import CredentialsConfig
            
            credentials = CredentialsConfig()
            
            # Add OpenAI credentials if available
            if os.getenv("OPENAI_API_KEY"):
                credentials.openai = {"api_key": os.getenv("OPENAI_API_KEY")}
            
            self.content_generator = ContentGenerator(credentials)
            
        except Exception as e:
            print(f"⚠️ Content generator setup failed: {e}")
            # Create a simple fallback content generator
            self.content_generator = None
        
        return connector_success
    
    async def generate_promotion_content(self, campaign_type: str = CampaignType.LAUNCH_ANNOUNCEMENT.value) -> PromotionContent:
        """Generate promotional content for AetherPost.
        
        Args:
            campaign_type: Type of campaign to generate content for
            
        Returns:
            Generated promotional content with metadata
        """
        print(f"🤖 Generating content for campaign: {campaign_type}")
        
        campaign = self.campaign_manager.get_campaign(campaign_type)
        theme = self.campaign_manager.get_random_theme(campaign_type)
        
        try:
            content_text = await self._generate_ai_content(campaign, theme)
        except Exception as e:
            print(f"⚠️ AI generation failed, using template: {e}")
            content_text = theme
        
        return PromotionContent(
            text=content_text,
            hashtags=campaign["hashtags"][:3],  # Limit hashtags for readability
            platforms=campaign["platforms"],
            campaign_type=campaign_type,
            generated_at=datetime.now()
        )
    
    async def _generate_ai_content(self, campaign: Dict[str, Any], theme: str) -> str:
        """Generate AI-powered content if OpenAI is available."""
        if not os.getenv("OPENAI_API_KEY") or self.content_generator is None:
            return theme
        
        try:
            # Create a simple prompt for content generation
            prompt = f"Create a {campaign['tone']} social media post about: {theme}"
            
            # Use the new OpenAI client
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ AI content generation failed: {e}")
            return theme
    
    async def post_to_platforms(self, content: PromotionContent, target_platforms: Optional[List[str]] = None) -> List[PostResult]:
        """Post content to specified platforms.
        
        Args:
            content: Content to post
            target_platforms: Specific platforms to post to (defaults to all available)
            
        Returns:
            List of post results for each platform
        """
        if target_platforms is None:
            target_platforms = self.connector_manager.get_available_platforms()
        
        # Filter platforms to only those that are available and requested
        available_platforms = set(self.connector_manager.get_available_platforms())
        platforms_to_use = [p for p in target_platforms if p in available_platforms and p in content.platforms]
        
        results = []
        
        for platform in platforms_to_use:
            result = await self._post_to_single_platform(platform, content)
            results.append(result)
            
            # Rate limiting between posts
            await asyncio.sleep(self._rate_limit_delay)
        
        return results
    
    async def _post_to_single_platform(self, platform: str, content: PromotionContent) -> PostResult:
        """Post content to a single platform."""
        try:
            print(f"📤 Posting to {platform}...")
            
            connector = self.connector_manager.connectors[platform]
            
            # Authenticate if needed
            if hasattr(connector, 'authenticate'):
                await connector.authenticate(connector.credentials)
            
            # Prepare post data
            post_data = {
                "text": content.text,
                "hashtags": content.hashtags,
                "type": "text"
            }
            
            # Post content
            result = await connector.post(post_data)
            
            if result.get("status") == "published":
                print(f"✅ Posted to {platform}: {result.get('url', 'Success')}")
                return PostResult(
                    platform=platform,
                    status="published",
                    url=result.get('url')
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ Failed to post to {platform}: {error_msg}")
                return PostResult(
                    platform=platform,
                    status="failed",
                    error=error_msg
                )
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error posting to {platform}: {error_msg}")
            return PostResult(
                platform=platform,
                status="failed",
                error=error_msg
            )
    
    async def run_promotion_campaign(self, campaign_type: str = CampaignType.LAUNCH_ANNOUNCEMENT.value, dry_run: bool = False) -> Dict[str, Any]:
        """Run a complete self-promotion campaign.
        
        Args:
            campaign_type: Type of campaign to run
            dry_run: If True, generate content but don't post
            
        Returns:
            Campaign results with content and posting metrics
        """
        print(f"🚀 Running AetherPost self-promotion campaign: {campaign_type}")
        print("=" * 60)
        
        # Generate content
        content = await self.generate_promotion_content(campaign_type)
        
        # Display generated content
        self._display_content_preview(content)
        
        if dry_run:
            print("\n🧪 DRY RUN - Content generated but not posted")
            return {"content": content, "results": [], "success_rate": 0.0}
        
        # Confirm posting
        if not self._confirm_posting():
            print("❌ Posting cancelled")
            return {"content": content, "results": [], "success_rate": 0.0}
        
        # Post to platforms
        results = await self.post_to_platforms(content)
        
        # Display results
        success_rate = self._display_campaign_results(results)
        
        return {
            "content": content,
            "results": results,
            "success_rate": success_rate
        }
    
    def _display_content_preview(self, content: PromotionContent) -> None:
        """Display generated content preview."""
        print(f"\n📝 Generated content:")
        print(f"Text: {content.text}")
        print(f"Hashtags: {' '.join(content.hashtags)}")
        print(f"Target platforms: {', '.join(content.platforms)}")
        print(f"Campaign type: {content.campaign_type}")
    
    def _confirm_posting(self) -> bool:
        """Ask user to confirm posting."""
        try:
            confirm = input("\n📤 Post this content? (y/N): ").lower().strip()
            return confirm == 'y'
        except EOFError:
            # Handle non-interactive environments (like automated tests)
            print("\n⚠️ Non-interactive environment detected - skipping posting")
            return False
    
    def _display_campaign_results(self, results: List[PostResult]) -> float:
        """Display campaign results and return success rate."""
        print(f"\n📊 Campaign Results:")
        
        successful_posts = sum(1 for r in results if r.status == "published")
        total_posts = len(results)
        success_rate = successful_posts / total_posts if total_posts > 0 else 0.0
        
        print(f"✅ Successful posts: {successful_posts}/{total_posts}")
        print(f"📈 Success rate: {success_rate:.1%}")
        
        # Display individual results
        for result in results:
            status_emoji = "✅" if result.status == "published" else "❌"
            status_text = result.url if result.url else result.error or result.status
            print(f"  {status_emoji} {result.platform}: {status_text}")
        
        return success_rate
    
    def create_promotion_schedule(self) -> Dict[str, List[str]]:
        """Create a sustainable promotion schedule.
        
        Returns:
            Structured schedule with daily, weekly, and monthly tasks
        """
        return {
            "daily_tasks": [
                "Share one feature highlight",
                "Engage with community responses",
                "Monitor mentions and feedback"
            ],
            "weekly_tasks": [
                "Post technical tutorial or deep-dive",
                "Share community success stories",
                "Update documentation highlights"
            ],
            "monthly_tasks": [
                "Major feature announcements",
                "Community survey and feedback collection",
                "Partnership and collaboration posts"
            ],
            "content_rotation": [
                "Monday: Feature highlights",
                "Tuesday: Technical content",
                "Wednesday: Community building",
                "Thursday: Tutorials/How-tos",
                "Friday: Weekly roundup",
                "Weekend: Casual community engagement"
            ]
        }
    
class SelfPromotionCLI:
    """Command-line interface for AetherPost self-promotion."""
    
    def __init__(self):
        self.promo = AetherPostSelfPromotion()
    
    async def run_interactive_session(self) -> None:
        """Run interactive promotion session."""
        print("🚀 AetherPost Self-Promotion Tool")
        print("Using AetherPost to promote AetherPost!")
        print("=" * 50)
        
        # Setup connectors
        if not await self.promo.setup_connectors():
            self._show_setup_instructions()
            return
        
        # Show available campaigns
        campaign_type = self._select_campaign()
        
        # Dry run option
        dry_run = self._ask_dry_run()
        
        # Run campaign
        result = await self.promo.run_promotion_campaign(campaign_type, dry_run=dry_run)
        
        # Show final results
        if not dry_run and result.get("success_rate", 0) > 0:
            self._show_success_summary(result)
    
    def _show_setup_instructions(self) -> None:
        """Show setup instructions for missing credentials."""
        print("\n💡 To use this tool:")
        print("1. Copy .env.example to .env")
        print("2. Add your social media credentials")
        print("3. Run this script again")
    
    def _select_campaign(self) -> str:
        """Interactive campaign selection."""
        print(f"\n📋 Available promotion campaigns:")
        campaigns = self.promo.campaign_manager.list_campaigns()
        
        for i, (key, concept) in enumerate(campaigns, 1):
            print(f"{i}. {key}: {concept}")
        
        try:
            choice = input(f"\nSelect campaign (1-{len(campaigns)}) or 'all' for random: ").strip()
        except EOFError:
            # Handle non-interactive environments
            choice = 'all'
            print(f"\n⚠️ Non-interactive environment - using random selection")
        
        if choice.lower() == 'all':
            campaign_type = random.choice([key for key, _ in campaigns])
            print(f"🎲 Randomly selected: {campaign_type}")
            return campaign_type
        
        try:
            campaign_keys = [key for key, _ in campaigns]
            return campaign_keys[int(choice) - 1]
        except (ValueError, IndexError):
            default_campaign = CampaignType.LAUNCH_ANNOUNCEMENT.value
            print(f"🔄 Using default: {default_campaign}")
            return default_campaign
    
    def _ask_dry_run(self) -> bool:
        """Ask if user wants to do a dry run."""
        try:
            response = input("🧪 Dry run? (Y/n): ").lower().strip()
            return response in ['', 'y', 'yes']
        except EOFError:
            # Handle non-interactive environments - default to dry run
            print("\n⚠️ Non-interactive environment - defaulting to dry run")
            return True
    
    def _show_success_summary(self, result: Dict[str, Any]) -> None:
        """Show final success summary and next steps."""
        print(f"\n🎉 Successfully promoted AetherPost using AetherPost itself!")
        print(f"📈 Success rate: {result['success_rate']:.1%}")
        
        # Show promotion schedule
        print(f"\n📅 Suggested promotion schedule:")
        schedule = self.promo.create_promotion_schedule()
        for day in schedule["content_rotation"]:
            print(f"  {day}")


async def main() -> None:
    """Main execution function."""
    cli = SelfPromotionCLI()
    await cli.run_interactive_session()


if __name__ == "__main__":
    asyncio.run(main())