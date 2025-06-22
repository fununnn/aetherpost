"""Social media profile and bio generation for consistent branding."""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import requests

import logging

logger = logging.getLogger(__name__)

@dataclass
class ProfileTemplate:
    """Template for social media profile generation."""
    platform: str
    bio_max_length: int
    name_max_length: int
    supports_links: bool
    supports_location: bool
    supports_website: bool
    supports_pinned_post: bool
    emoji_friendly: bool
    hashtag_friendly: bool
    link_in_bio_culture: bool  # Platforms where "link in bio" is common
    professional_tone: bool
    required_elements: List[str] = field(default_factory=list)
    optional_elements: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set default elements based on platform."""
        if not self.required_elements:
            self.required_elements = ["description", "call_to_action"]
        if not self.optional_elements:
            self.optional_elements = ["location", "website", "contact", "skills"]

@dataclass
class ProfileContent:
    """Generated profile content for a platform."""
    platform: str
    display_name: str
    bio: str
    website_url: Optional[str]
    location: Optional[str]
    pinned_post: Optional[str]
    profile_image_suggestion: Optional[str]
    cover_image_suggestion: Optional[str]
    additional_links: List[Dict[str, str]] = field(default_factory=list)
    character_count: int = 0
    character_limit: int = 0
    
    def __post_init__(self):
        """Calculate character count."""
        self.character_count = len(self.bio)

class ProfileGenerator:
    """Generate optimized social media profiles for different platforms."""
    
    def __init__(self):
        self.platform_configs = self._load_platform_configs()
        self.style_variations = self._load_style_variations()
    
    def _load_platform_configs(self) -> Dict[str, ProfileTemplate]:
        """Load platform-specific profile configurations."""
        return {
            "twitter": ProfileTemplate(
                platform="twitter",
                bio_max_length=160,
                name_max_length=50,
                supports_links=True,
                supports_location=True,
                supports_website=True,
                supports_pinned_post=True,
                emoji_friendly=True,
                hashtag_friendly=True,
                link_in_bio_culture=False,
                professional_tone=False,
                required_elements=["description", "call_to_action"],
                optional_elements=["location", "website", "skills", "personality"]
            ),
            
            "instagram": ProfileTemplate(
                platform="instagram",
                bio_max_length=150,
                name_max_length=30,
                supports_links=True,  # Link in bio
                supports_location=False,
                supports_website=True,
                supports_pinned_post=True,
                emoji_friendly=True,
                hashtag_friendly=False,  # Hashtags in bio not recommended
                link_in_bio_culture=True,
                professional_tone=False,
                required_elements=["description", "call_to_action"],
                optional_elements=["personality", "contact", "link_reference"]
            ),
            
            "linkedin": ProfileTemplate(
                platform="linkedin",
                bio_max_length=220,  # Headline
                name_max_length=100,
                supports_links=True,
                supports_location=True,
                supports_website=True,
                supports_pinned_post=True,
                emoji_friendly=False,
                hashtag_friendly=True,
                link_in_bio_culture=False,
                professional_tone=True,
                required_elements=["professional_description", "value_proposition"],
                optional_elements=["experience", "skills", "contact"]
            ),
            
            "github": ProfileTemplate(
                platform="github",
                bio_max_length=160,
                name_max_length=39,
                supports_links=True,
                supports_location=True,
                supports_website=True,
                supports_pinned_post=True,  # Pinned repositories
                emoji_friendly=True,
                hashtag_friendly=False,
                link_in_bio_culture=False,
                professional_tone=True,
                required_elements=["technical_description", "current_work"],
                optional_elements=["tech_stack", "contact", "fun_fact"]
            ),
            
            "youtube": ProfileTemplate(
                platform="youtube",
                bio_max_length=1000,
                name_max_length=100,
                supports_links=True,
                supports_location=False,
                supports_website=True,
                supports_pinned_post=True,  # Channel trailer
                emoji_friendly=True,
                hashtag_friendly=True,
                link_in_bio_culture=False,
                professional_tone=False,
                required_elements=["channel_description", "content_schedule"],
                optional_elements=["social_links", "contact", "community_guidelines"]
            ),
            
            "tiktok": ProfileTemplate(
                platform="tiktok",
                bio_max_length=80,
                name_max_length=30,
                supports_links=True,
                supports_location=False,
                supports_website=True,
                supports_pinned_post=True,
                emoji_friendly=True,
                hashtag_friendly=False,
                link_in_bio_culture=True,
                professional_tone=False,
                required_elements=["short_description"],
                optional_elements=["personality", "content_type"]
            ),
            
            "reddit": ProfileTemplate(
                platform="reddit",
                bio_max_length=200,
                name_max_length=20,
                supports_links=False,
                supports_location=False,
                supports_website=False,
                supports_pinned_post=False,
                emoji_friendly=True,
                hashtag_friendly=False,
                link_in_bio_culture=False,
                professional_tone=False,
                required_elements=["community_description"],
                optional_elements=["interests", "subreddit_activity"]
            ),
            
            "discord": ProfileTemplate(
                platform="discord",
                bio_max_length=190,
                name_max_length=32,
                supports_links=False,
                supports_location=False,
                supports_website=False,
                supports_pinned_post=False,
                emoji_friendly=True,
                hashtag_friendly=False,
                link_in_bio_culture=False,
                professional_tone=False,
                required_elements=["personality"],
                optional_elements=["gaming_interests", "current_status"]
            ),
            
            "bluesky": ProfileTemplate(
                platform="bluesky",
                bio_max_length=256,
                name_max_length=64,
                supports_links=True,
                supports_location=False,
                supports_website=True,
                supports_pinned_post=True,
                emoji_friendly=True,
                hashtag_friendly=True,
                link_in_bio_culture=False,
                professional_tone=False,
                required_elements=["description", "call_to_action"],
                optional_elements=["interests", "website", "contact"]
            )
        }
    
    def _load_style_variations(self) -> Dict[str, Dict[str, Any]]:
        """Load different style variations for profiles."""
        return {
            "professional": {
                "tone": "formal",
                "emoji_usage": "minimal",
                "focus": "expertise_and_results",
                "call_to_action": "professional"
            },
            "friendly": {
                "tone": "casual",
                "emoji_usage": "moderate",
                "focus": "approachability_and_community",
                "call_to_action": "welcoming"
            },
            "creative": {
                "tone": "playful",
                "emoji_usage": "heavy",
                "focus": "innovation_and_personality",
                "call_to_action": "engaging"
            },
            "technical": {
                "tone": "expert",
                "emoji_usage": "minimal",
                "focus": "technical_expertise",
                "call_to_action": "collaborative"
            }
        }
    
    def extract_project_info(self, project_path: Optional[str] = None, github_url: Optional[str] = None) -> Dict[str, Any]:
        """Extract project information from various sources."""
        project_info = {
            "name": "AetherPost",
            "description": "Social media automation for developers",
            "tech_stack": [],
            "github_url": github_url,
            "website_url": None,
            "license": "MIT",
            "language": "Python",
            "features": [],
            "target_audience": "developers"
        }
        
        # Try to extract from package.json
        if project_path:
            package_json = Path(project_path) / "package.json"
            if package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        data = json.load(f)
                        project_info.update({
                            "name": data.get("name", project_info["name"]),
                            "description": data.get("description", project_info["description"]),
                            "website_url": data.get("homepage"),
                            "language": "JavaScript"
                        })
                        
                        # Extract dependencies as tech stack
                        deps = data.get("dependencies", {})
                        dev_deps = data.get("devDependencies", {})
                        tech_stack = list(deps.keys())[:5] + list(dev_deps.keys())[:3]
                        project_info["tech_stack"] = tech_stack
                except Exception as e:
                    logger.warning(f"Could not parse package.json: {e}")
        
        # Try to extract from pyproject.toml
        if project_path:
            pyproject = Path(project_path) / "pyproject.toml"
            if pyproject.exists():
                try:
                    import tomli
                    with open(pyproject, 'rb') as f:
                        data = tomli.load(f)
                        project_data = data.get("project", {})
                        project_info.update({
                            "name": project_data.get("name", project_info["name"]),
                            "description": project_data.get("description", project_info["description"]),
                            "language": "Python"
                        })
                        
                        # Extract dependencies
                        deps = project_data.get("dependencies", [])
                        project_info["tech_stack"] = [dep.split(">=")[0].split("==")[0] for dep in deps[:8]]
                except Exception as e:
                    logger.warning(f"Could not parse pyproject.toml: {e}")
        
        # Extract from GitHub API if URL provided
        if github_url:
            try:
                # Parse GitHub URL
                match = re.match(r"https://github\.com/([^/]+)/([^/]+)", github_url)
                if match:
                    owner, repo = match.groups()
                    api_url = f"https://api.github.com/repos/{owner}/{repo}"
                    
                    response = requests.get(api_url, timeout=5)
                    if response.status_code == 200:
                        repo_data = response.json()
                        project_info.update({
                            "name": repo_data.get("name", project_info["name"]),
                            "description": repo_data.get("description", project_info["description"]),
                            "website_url": repo_data.get("homepage"),
                            "language": repo_data.get("language", project_info["language"]),
                            "license": repo_data.get("license", {}).get("name", "MIT") if repo_data.get("license") else "MIT",
                            "stars": repo_data.get("stargazers_count", 0),
                            "forks": repo_data.get("forks_count", 0)
                        })
                        
                        # Extract topics as features
                        project_info["features"] = repo_data.get("topics", [])[:5]
            except Exception as e:
                logger.warning(f"Could not fetch GitHub data: {e}")
        
        return project_info
    
    def generate_profile(self, platform: str, project_info: Dict[str, Any], 
                        style: str = "friendly", custom_elements: Optional[Dict[str, str]] = None) -> ProfileContent:
        """Generate optimized profile for specific platform."""
        
        config = self.platform_configs.get(platform)
        if not config:
            raise ValueError(f"Platform {platform} not supported")
        
        style_config = self.style_variations.get(style, self.style_variations["friendly"])
        
        # Merge custom elements and AetherPost promotion info
        context = project_info.copy()
        if custom_elements:
            context.update(custom_elements)
        
        # Always include campaign URLs for promotion
        context = self._add_campaign_urls(context)
        
        # Generate platform-specific content
        if platform == "twitter":
            return self._generate_twitter_profile(config, context, style_config)
        elif platform == "instagram":
            return self._generate_instagram_profile(config, context, style_config)
        elif platform == "linkedin":
            return self._generate_linkedin_profile(config, context, style_config)
        elif platform == "github":
            return self._generate_github_profile(config, context, style_config)
        elif platform == "youtube":
            return self._generate_youtube_profile(config, context, style_config)
        elif platform == "tiktok":
            return self._generate_tiktok_profile(config, context, style_config)
        elif platform == "reddit":
            return self._generate_reddit_profile(config, context, style_config)
        elif platform == "discord":
            return self._generate_discord_profile(config, context, style_config)
        elif platform == "bluesky":
            return self._generate_bluesky_profile(config, context, style_config)
        else:
            return self._generate_generic_profile(config, context, style_config)
    
    def _add_campaign_urls(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add campaign URLs to context for user's product promotion."""
        
        # Use campaign URLs for user's product promotion
        urls = context.get("urls", {})
        
        # Add all available URLs as promotion links
        if "additional_promotion_links" not in context:
            context["additional_promotion_links"] = []
        
        # Add each URL from campaign.yaml
        for url_type, url_value in urls.items():
            if url_value:
                title = {
                    "main": "Website",
                    "github": "GitHub",
                    "docs": "Documentation",
                    "demo": "Demo",
                    "download": "Download"
                }.get(url_type, url_type.title())
                
                context["additional_promotion_links"].append({
                    "title": title,
                    "url": url_value
                })
        
        return context
    
    def _generate_twitter_profile(self, config: ProfileTemplate, context: Dict[str, Any], style: Dict[str, Any]) -> ProfileContent:
        """Generate Twitter profile."""
        app_name = context.get("name", "AetherPost")
        description = context.get("description", "Social media automation for developers")
        
        # Generate bio variations based on style
        if style["tone"] == "professional":
            bio = f"Building {app_name} - {description}. Helping users achieve their goals."
        elif style["tone"] == "creative":
            emoji_prefix = "🚀 " if style["emoji_usage"] != "minimal" else ""
            bio = f"{emoji_prefix}Creator of {app_name} | {description} | Making it happen!"
        else:  # friendly
            bio = f"👋 Building {app_name}! {description}. Join me on this journey!"
        
        # Add call to action based on style
        if style["call_to_action"] == "professional":
            bio += f" | Links ⬇️"
        elif style["call_to_action"] == "engaging":
            bio += f" | Check it out! 👇"
        else:  # welcoming
            bio += f" | Come say hi! 🤝"
        
        # Ensure bio fits within limit
        if len(bio) > config.bio_max_length:
            bio = bio[:config.bio_max_length-3] + "..."
        
        # Create additional links from campaign URLs
        additional_links = []
        if context.get("additional_promotion_links"):
            additional_links.extend(context["additional_promotion_links"])
        
        # Use main website URL or first available URL
        urls = context.get("urls", {})
        website_url = urls.get("main") or urls.get("github") or context.get("website_url")
        
        return ProfileContent(
            platform="twitter",
            display_name=f"{app_name} 🚀" if style["emoji_usage"] != "minimal" else app_name,
            bio=bio,
            website_url=website_url,
            location=context.get("location"),
            pinned_post=f"🎉 Introducing {app_name}! {description}. Thread 🧵",
            profile_image_suggestion="Logo with clean background, high contrast",
            cover_image_suggestion=f"Branded header showcasing {app_name} features",
            additional_links=additional_links,
            character_count=len(bio),
            character_limit=config.bio_max_length
        )
    
    def _generate_instagram_profile(self, config: ProfileTemplate, context: Dict[str, Any], style: Dict[str, Any]) -> ProfileContent:
        """Generate Instagram profile."""
        app_name = context.get("name", "AetherPost")
        description = context.get("description", "Social media automation for developers")
        
        # Instagram bio with visual elements
        bio_lines = []
        
        # Add emoji opener
        if style["emoji_usage"] != "minimal":
            # Use first words of description for category
            desc_words = description.split()[:2]
            bio_lines.append(f"🚀 {' '.join(desc_words).title()}")
            if len(desc_words) > 1:
                bio_lines.append(f"✨ {app_name}")
        else:
            bio_lines.append(f"{app_name}")
            bio_lines.append(description.title())
        
        # Add features
        features = context.get("features", ["innovative", "powerful", "user-friendly"])[:3]
        for feature in features:
            emoji = "✨" if style["emoji_usage"] != "minimal" else "•"
            bio_lines.append(f"{emoji} {feature.replace('-', ' ').title()}")
        
        # Add call to action
        if config.link_in_bio_culture:
            bio_lines.append("👇 Links below")
        
        bio = "\n".join(bio_lines)
        
        # Ensure bio fits
        if len(bio) > config.bio_max_length:
            # Remove features until it fits
            while len(bio) > config.bio_max_length and len(bio_lines) > 3:
                bio_lines.pop(-2)  # Remove feature lines
                bio = "\n".join(bio_lines)
        
        # Create additional links from campaign URLs
        additional_links = []
        if context.get("additional_promotion_links"):
            additional_links.extend(context["additional_promotion_links"])
        
        # Use main website URL or first available URL
        urls = context.get("urls", {})
        website_url = urls.get("main") or urls.get("website") or context.get("website_url")
        
        return ProfileContent(
            platform="instagram",
            display_name=app_name,
            bio=bio,
            website_url=website_url,
            location=None,
            pinned_post=f"Story highlight: 'Getting Started with {app_name}'",
            profile_image_suggestion="Square logo, vibrant colors, minimal text",
            cover_image_suggestion="Not applicable for Instagram",
            additional_links=additional_links,
            character_count=len(bio),
            character_limit=config.bio_max_length
        )
    
    def _generate_linkedin_profile(self, config: ProfileTemplate, context: Dict[str, Any], style: Dict[str, Any]) -> ProfileContent:
        """Generate LinkedIn profile."""
        app_name = context.get("name", "AetherPost")
        
        # Professional headline
        headline = f"Building {app_name} | Social Media Automation for Developers | Making Dev Marketing Effortless"
        
        if len(headline) > config.bio_max_length:
            headline = f"Creator of {app_name} | Developer Tools | Social Media Automation"
        
        # About section (for pinned post suggestion)
        about_section = f"""Building the future of developer marketing with {app_name}.

🎯 What we do: Help developers automate their social media presence
🚀 Why it matters: More time coding, less time on marketing
💡 How we're different: Built by developers, for developers

Key features:
• Multi-platform automation
• AI-powered content generation  
• Git integration
• Developer-friendly CLI

Always excited to connect with fellow developers and discuss the intersection of code and community building."""
        
        return ProfileContent(
            platform="linkedin",
            display_name=f"Founder & Developer at {app_name}",
            bio=headline,
            website_url=context.get("website_url") or context.get("github_url"),
            location=context.get("location", "San Francisco, CA"),
            pinned_post=about_section,
            profile_image_suggestion="Professional headshot or company logo",
            cover_image_suggestion=f"Professional banner showcasing {app_name} value proposition",
            character_count=len(headline),
            character_limit=config.bio_max_length
        )
    
    def _generate_github_profile(self, config: ProfileTemplate, context: Dict[str, Any], style: Dict[str, Any]) -> ProfileContent:
        """Generate GitHub profile."""
        app_name = context.get("name", "AetherPost")
        language = context.get("language", "Python")
        
        # Technical bio
        bio = f"Building {app_name} | {language} Developer | Open Source Enthusiast"
        
        # README.md content suggestion
        urls = context.get("urls", {})
        readme_content = f"""# Hi there 👋

I'm building **{app_name}** - {context.get('description', 'an awesome project')}.

## 🔭 Current Projects
- [{app_name}]({urls.get('github', context.get('github_url', '#'))}) - {context.get('description', 'My latest project')}

## 🌱 Tech Stack
{', '.join(context.get('tech_stack', [language])[:8])}

## 📫 How to reach me
- Website: {urls.get('main', context.get('website_url', 'Coming soon'))}
- Twitter: [@{app_name.lower()}](https://twitter.com/{app_name.lower()})"""

        # Add docs link if available
        if urls.get('docs'):
            readme_content += f"\n- Documentation: [{urls.get('docs')}]({urls.get('docs')})"
        
        readme_content += f"""

## ⚡ Fun fact
Always excited to connect with fellow developers and share cool projects!"""
        
        return ProfileContent(
            platform="github",
            display_name=app_name,
            bio=bio,
            website_url=urls.get('main') or context.get('website_url'),
            location=context.get("location"),
            pinned_post=readme_content,
            profile_image_suggestion="Professional avatar or logo, GitHub-friendly",
            cover_image_suggestion="Not applicable for GitHub",
            character_count=len(bio),
            character_limit=config.bio_max_length
        )
    
    def _generate_youtube_profile(self, config: ProfileTemplate, context: Dict[str, Any], style: Dict[str, Any]) -> ProfileContent:
        """Generate YouTube profile."""
        app_name = context.get("name", "AetherPost")
        
        bio = f"""Welcome to the {app_name} channel! 🚀

We're building the ultimate social media automation tool for developers. Here you'll find:

📚 Tutorials on automating your social media
🛠️ Behind-the-scenes development content  
💡 Tips for developer marketing
🎥 Product demos and feature announcements

New videos every Tuesday and Friday!

🔗 Links:
GitHub: {context.get('github_url', 'github.com/user/repo')}
Website: {context.get('website_url', 'Coming soon')}
Discord: Join our dev community

Subscribe for developer-focused content that saves you time! 🔔"""
        
        return ProfileContent(
            platform="youtube",
            display_name=f"{app_name} - Developer Tools",
            bio=bio,
            website_url=context.get("website_url") or context.get("github_url"),
            location=None,
            pinned_post="Channel trailer: 'Why Every Developer Needs Social Media Automation'",
            profile_image_suggestion="Clean logo design, video-friendly",
            cover_image_suggestion="2560x1440 banner with upload schedule and key topics",
            character_count=len(bio),
            character_limit=config.bio_max_length
        )
    
    def _generate_tiktok_profile(self, config: ProfileTemplate, context: Dict[str, Any], style: Dict[str, Any]) -> ProfileContent:
        """Generate TikTok profile."""
        app_name = context.get("name", "AetherPost")
        
        # Very short bio for TikTok
        bio = f"🚀 {app_name} creator\n💻 Dev tools & automation\n📱 Link below!"
        
        return ProfileContent(
            platform="tiktok",
            display_name=app_name,
            bio=bio,
            website_url=context.get("website_url") or context.get("github_url"),
            location=None,
            pinned_post="Pinned video: '60 Second Setup: Automate Your Social Media'",
            profile_image_suggestion="Eye-catching logo, bright colors",
            cover_image_suggestion="Not applicable for TikTok",
            character_count=len(bio),
            character_limit=config.bio_max_length
        )
    
    def _generate_reddit_profile(self, config: ProfileTemplate, context: Dict[str, Any], style: Dict[str, Any]) -> ProfileContent:
        """Generate Reddit profile."""
        app_name = context.get("name", "AetherPost")
        
        bio = f"Building {app_name} - social media automation for devs. Open to feedback and discussions about developer tools!"
        
        return ProfileContent(
            platform="reddit",
            display_name=f"u/{app_name.lower()}_dev",
            bio=bio,
            website_url=None,  # Reddit doesn't support website links in profile
            location=None,
            pinned_post="Active in r/programming, r/webdev, r/sideproject",
            profile_image_suggestion="Simple avatar or logo",
            cover_image_suggestion="Not applicable for Reddit",
            character_count=len(bio),
            character_limit=config.bio_max_length
        )
    
    def _generate_discord_profile(self, config: ProfileTemplate, context: Dict[str, Any], style: Dict[str, Any]) -> ProfileContent:
        """Generate Discord profile."""
        app_name = context.get("name", "AetherPost")
        powered_by = context.get("powered_by_text", "Built with AetherPost")
        
        bio = f"🛠️ Building {app_name} | 💻 Python Developer | 🤖 {powered_by} | Always happy to chat about dev tools!"
        
        return ProfileContent(
            platform="discord",
            display_name=f"{app_name} Dev",
            bio=bio,
            website_url=None,
            location=None,
            pinned_post=f"Custom status: 'Working on {app_name} with AetherPost'",
            profile_image_suggestion="Animated avatar or branded logo",
            cover_image_suggestion="Not applicable for Discord",
            character_count=len(bio),
            character_limit=config.bio_max_length
        )
    
    def _generate_bluesky_profile(self, config: ProfileTemplate, context: Dict[str, Any], style: Dict[str, Any]) -> ProfileContent:
        """Generate Bluesky profile."""
        app_name = context.get("name", "AetherPost")
        description = context.get("description", "Social media automation for developers")
        
        # Generate bio variations based on style
        if style["tone"] == "professional":
            bio = f"Building {app_name} - {description}. Always excited to share progress and connect with others. #innovation"
        elif style["tone"] == "creative":
            emoji_prefix = "🚀 " if style["emoji_usage"] != "minimal" else ""
            bio = f"{emoji_prefix}Creator of {app_name} | {description} | Making magic happen! ✨ #create #build"
        else:  # friendly
            bio = f"👋 Building {app_name}! {description}. Love connecting with fellow builders! #community #opentoconnect"
        
        # Ensure bio fits within limit
        if len(bio) > config.bio_max_length:
            bio = bio[:config.bio_max_length-3] + "..."
        
        # Create additional links from campaign URLs
        additional_links = []
        if context.get("additional_promotion_links"):
            additional_links.extend(context["additional_promotion_links"])
            
        # Use main website URL or first available URL
        urls = context.get("urls", {})
        website_url = urls.get("main") or urls.get("github") or context.get("website_url")
        
        return ProfileContent(
            platform="bluesky",
            display_name=f"{app_name} 🌐" if style["emoji_usage"] != "minimal" else app_name,
            bio=bio,
            website_url=website_url,
            location=None,
            pinned_post=f"🎉 Just launched {app_name}! {description}. Excited to share this with everyone!",
            profile_image_suggestion="Clean logo with blue sky theme",
            cover_image_suggestion="Not applicable for Bluesky",
            additional_links=additional_links,
            character_count=len(bio),
            character_limit=config.bio_max_length
        )
    
    def _generate_generic_profile(self, config: ProfileTemplate, context: Dict[str, Any], style: Dict[str, Any]) -> ProfileContent:
        """Generate generic profile for unknown platforms."""
        app_name = context.get("name", "AetherPost")
        description = context.get("description", "Social media automation for developers")
        
        bio = f"Building {app_name} - {description}. Connect with me to learn more!"
        
        return ProfileContent(
            platform=config.platform,
            display_name=app_name,
            bio=bio,
            website_url=context.get("website_url") or context.get("github_url"),
            location=context.get("location"),
            pinned_post=f"Check out {app_name} for automated social media management!",
            profile_image_suggestion="Professional logo or avatar",
            cover_image_suggestion="Branded banner if supported",
            character_count=len(bio),
            character_limit=config.bio_max_length
        )
    
    def generate_multiple_variations(self, platform: str, project_info: Dict[str, Any], 
                                   styles: List[str] = None) -> List[ProfileContent]:
        """Generate multiple profile variations for A/B testing."""
        if styles is None:
            styles = ["professional", "friendly", "creative"]
        
        variations = []
        for style in styles:
            try:
                profile = self.generate_profile(platform, project_info, style)
                variations.append(profile)
            except Exception as e:
                logger.warning(f"Could not generate {style} variation for {platform}: {e}")
        
        return variations
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms."""
        return list(self.platform_configs.keys())
    
    def get_platform_requirements(self, platform: str) -> Optional[ProfileTemplate]:
        """Get platform requirements and limitations."""
        return self.platform_configs.get(platform)