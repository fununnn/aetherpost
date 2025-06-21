"""Content strategy and platform-specific messaging."""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content types for different purposes."""
    ANNOUNCEMENT = "announcement"        # 新機能、リリース、重要な更新
    MAINTENANCE = "maintenance"          # メンテナンス、アップデート、お知らせ
    ENGAGEMENT = "engagement"           # コミュニティ交流、質問、ディスカッション
    EDUCATIONAL = "educational"         # チュートリアル、Tips、How-to
    PROMOTIONAL = "promotional"         # サービス紹介、機能アピール
    PERIODIC = "periodic"              # 定期投稿、習慣的なコンテンツ
    BEHIND_SCENES = "behind_scenes"    # 開発の様子、チーム紹介
    COMMUNITY = "community"            # ユーザー紹介、成功事例
    STATUS = "status"                  # システム状況、稼働状況


class PostingSchedule(Enum):
    """Posting frequency schedules."""
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ON_DEMAND = "on_demand"


@dataclass
class ContentTemplate:
    """Template for content generation."""
    content_type: ContentType
    platform: str
    template: str
    tone: str
    hashtags: List[str]
    optimal_time: Optional[str] = None
    max_length: Optional[int] = None
    requires_media: bool = False
    schedule: Optional[PostingSchedule] = None


class PlatformContentStrategy:
    """Platform-specific content strategy and generation."""
    
    def __init__(self):
        self.templates = self._load_platform_templates()
        self.content_guidelines = self._load_content_guidelines()
    
    def _load_platform_templates(self) -> Dict[str, Dict[ContentType, ContentTemplate]]:
        """Load platform-specific content templates."""
        return {
            "twitter": {
                ContentType.ANNOUNCEMENT: ContentTemplate(
                    content_type=ContentType.ANNOUNCEMENT,
                    platform="twitter",
                    template="🚀 {title}\n\n{description}\n\n{call_to_action}",
                    tone="excited_professional",
                    hashtags=["#AetherPost", "#DevTools", "#Launch"],
                    max_length=280,
                    optimal_time="09:00,13:00,18:00"
                ),
                ContentType.MAINTENANCE: ContentTemplate(
                    content_type=ContentType.MAINTENANCE,
                    platform="twitter",
                    template="🔧 Maintenance Update\n\n{maintenance_type}: {description}\n\n⏰ {schedule}\n📊 {impact}\n\nWe'll keep you posted!",
                    tone="informative_friendly",
                    hashtags=["#MaintenanceUpdate", "#AetherPost"],
                    max_length=280,
                    schedule=PostingSchedule.ON_DEMAND
                ),
                ContentType.ENGAGEMENT: ContentTemplate(
                    content_type=ContentType.ENGAGEMENT,
                    platform="twitter",
                    template="💭 {question}\n\n{context}\n\nShare your thoughts below! 👇",
                    tone="casual_friendly",
                    hashtags=["#DevCommunity", "#Discussion"],
                    max_length=280,
                    schedule=PostingSchedule.WEEKLY
                ),
                ContentType.EDUCATIONAL: ContentTemplate(
                    content_type=ContentType.EDUCATIONAL,
                    platform="twitter",
                    template="💡 Quick Tip: {tip_title}\n\n{tip_content}\n\n🧵 Thread for more details:",
                    tone="helpful_expert",
                    hashtags=["#DevTips", "#Tutorial", "#AetherPost"],
                    max_length=280,
                    schedule=PostingSchedule.BIWEEKLY
                ),
                ContentType.PERIODIC: ContentTemplate(
                    content_type=ContentType.PERIODIC,
                    platform="twitter",
                    template="📊 Weekly Update:\n\n✅ {accomplishments}\n🔄 {in_progress}\n🎯 {next_week}\n\n#WeeklyUpdate",
                    tone="progress_update",
                    hashtags=["#WeeklyUpdate", "#Progress"],
                    max_length=280,
                    schedule=PostingSchedule.WEEKLY,
                    optimal_time="17:00"  # Friday evening
                )
            },
            
            "instagram": {
                ContentType.ANNOUNCEMENT: ContentTemplate(
                    content_type=ContentType.ANNOUNCEMENT,
                    platform="instagram",
                    template="🎉 {title}\n\n{detailed_description}\n\n{benefits}\n\n{call_to_action}\n\n---\n{story_prompt}",
                    tone="visual_storytelling",
                    hashtags=["#AetherPost", "#DevTools", "#SocialMediaAutomation", "#TechLaunch", "#Innovation"],
                    max_length=2200,
                    requires_media=True
                ),
                ContentType.BEHIND_SCENES: ContentTemplate(
                    content_type=ContentType.BEHIND_SCENES,
                    platform="instagram",
                    template="👨‍💻 Behind the Scenes\n\n{development_story}\n\n{challenges_overcome}\n\n{team_insights}\n\nWhat would you like to see next? 💭",
                    tone="authentic_personal",
                    hashtags=["#BehindTheScenes", "#DevLife", "#TeamWork", "#Building"],
                    max_length=2200,
                    requires_media=True,
                    schedule=PostingSchedule.MONTHLY
                ),
                ContentType.EDUCATIONAL: ContentTemplate(
                    content_type=ContentType.EDUCATIONAL,
                    platform="instagram",
                    template="📚 Tutorial: {tutorial_title}\n\n{step_by_step}\n\n💡 Pro Tips:\n{pro_tips}\n\n🔗 Full guide in bio",
                    tone="educational_approachable",
                    hashtags=["#Tutorial", "#DevEducation", "#LearnToCode", "#AetherPost"],
                    max_length=2200,
                    requires_media=True,
                    schedule=PostingSchedule.WEEKLY
                )
            },
            
            "youtube": {
                ContentType.EDUCATIONAL: ContentTemplate(
                    content_type=ContentType.EDUCATIONAL,
                    platform="youtube",
                    template="{tutorial_title}\n\nIn this video:\n{video_outline}\n\n⏰ Timestamps:\n{timestamps}\n\n🔗 Resources:\n{resources}",
                    tone="educational_expert",
                    hashtags=["tutorial", "automation", "developers", "productivity"],
                    max_length=5000,
                    requires_media=True,
                    schedule=PostingSchedule.WEEKLY
                ),
                ContentType.ANNOUNCEMENT: ContentTemplate(
                    content_type=ContentType.ANNOUNCEMENT,
                    platform="youtube",
                    template="{title}\n\n🚀 What's New:\n{description}\n\n📈 Why This Matters:\n{benefits}\n\n🎯 How to Get Started:\n{call_to_action}",
                    tone="professional_excited",
                    hashtags=["aetherpost", "update", "features", "social_media"],
                    max_length=5000,
                    requires_media=True
                )
            },
            
            "reddit": {
                ContentType.ANNOUNCEMENT: ContentTemplate(
                    content_type=ContentType.ANNOUNCEMENT,
                    platform="reddit",
                    template="I built {title} - {description}\n\n**What it does:**\n{benefits}\n\n**Why I built this:**\n{motivation}\n\n**What's next:**\n{call_to_action}\n\nHappy to answer questions!",
                    tone="community_sharing",
                    hashtags=[],  # Reddit doesn't use hashtags
                    max_length=40000,
                    schedule=PostingSchedule.ON_DEMAND
                ),
                ContentType.COMMUNITY: ContentTemplate(
                    content_type=ContentType.COMMUNITY,
                    platform="reddit",
                    template="**Community Spotlight:** {user_story}\n\n{implementation_details}\n\n**Results:**\n{results}\n\n**Lessons learned:**\n{lessons}\n\nGreat work by u/{username}!",
                    tone="community_recognition",
                    hashtags=[],
                    max_length=40000,
                    schedule=PostingSchedule.MONTHLY
                )
            },
            
            "tiktok": {
                ContentType.EDUCATIONAL: ContentTemplate(
                    content_type=ContentType.EDUCATIONAL,
                    platform="tiktok",
                    template="💡 {tip_title}\n\n{tip_content}\n\n#DevTips #TechTok",
                    tone="energetic_quick",
                    hashtags=["#DevTips", "#CodingHacks", "#TechTok", "#Programming"],
                    max_length=300,
                    requires_media=True,
                    schedule=PostingSchedule.BIWEEKLY
                ),
                ContentType.BEHIND_SCENES: ContentTemplate(
                    content_type=ContentType.BEHIND_SCENES,
                    platform="tiktok",
                    template="POV: {development_story}\n\n{outcome}\n\n#DevLife #BuildInPublic",
                    tone="trendy_relatable",
                    hashtags=["#DevLife", "#CodingLife", "#TechTok", "#BuildInPublic"],
                    max_length=300,
                    requires_media=True,
                    schedule=PostingSchedule.WEEKLY
                ),
                ContentType.ANNOUNCEMENT: ContentTemplate(
                    content_type=ContentType.ANNOUNCEMENT,
                    platform="tiktok",
                    template="🚀 {title}\n\n{description}\n\n{call_to_action}\n\n#TechTok #NewTech",
                    tone="energetic_excited",
                    hashtags=["#TechTok", "#NewTech", "#Automation", "#DevTools"],
                    max_length=300,
                    requires_media=True
                )
            }
        }
    
    def _load_content_guidelines(self) -> Dict[str, Dict[str, Any]]:
        """Load platform-specific content guidelines."""
        return {
            "twitter": {
                "best_practices": [
                    "Keep tweets concise and punchy",
                    "Use relevant hashtags (2-3 max)",
                    "Include call-to-action",
                    "Tweet at optimal times",
                    "Engage with replies quickly"
                ],
                "avoid": [
                    "Too many hashtags",
                    "Overly promotional tone",
                    "Long threads for simple updates",
                    "Posting during low-engagement hours"
                ],
                "tone_guidelines": {
                    "announcements": "Excited but professional",
                    "maintenance": "Transparent and apologetic if needed",
                    "engagement": "Casual and friendly",
                    "educational": "Helpful and approachable"
                }
            },
            
            "instagram": {
                "best_practices": [
                    "High-quality visuals are essential",
                    "Use all 30 hashtags strategically",
                    "Tell stories in captions",
                    "Use Stories for behind-the-scenes",
                    "Engage with comments meaningfully"
                ],
                "avoid": [
                    "Low-quality images",
                    "Purely text-based posts",
                    "Overly corporate language",
                    "Ignoring visual aesthetics"
                ],
                "visual_requirements": {
                    "posts": "High-res images, consistent filter/style",
                    "stories": "Vertical 9:16 format",
                    "reels": "Trending audio, quick cuts"
                }
            },
            
            "youtube": {
                "best_practices": [
                    "Detailed, searchable titles",
                    "Comprehensive descriptions with timestamps",
                    "Custom thumbnails",
                    "Consistent upload schedule",
                    "Engage with comments"
                ],
                "content_focus": {
                    "educational": "Step-by-step tutorials with clear outcomes",
                    "announcements": "Demo the new features in action",
                    "behind_scenes": "Development process and decision-making"
                }
            },
            
            "reddit": {
                "best_practices": [
                    "Provide value to the community first",
                    "Be transparent about being the creator",
                    "Engage genuinely in discussions",
                    "Follow each subreddit's rules",
                    "Use appropriate subreddits"
                ],
                "avoid": [
                    "Overly promotional posts",
                    "Posting same content to many subreddits",
                    "Ignoring community feedback",
                    "Not participating in discussions"
                ],
                "subreddit_strategy": {
                    "r/sideproject": "Focus on building journey and lessons",
                    "r/devtools": "Emphasize technical benefits and features",
                    "r/programming": "Technical deep-dives and implementation details"
                }
            },
            
            "tiktok": {
                "best_practices": [
                    "Hook viewers in first 3 seconds",
                    "Use trending sounds and effects",
                    "Keep it entertaining and educational",
                    "Post consistently",
                    "Use trending hashtags strategically"
                ],
                "content_style": {
                    "educational": "Quick tips with visual demonstrations",
                    "behind_scenes": "Day-in-the-life developer content",
                    "trends": "Adapt coding content to trending formats"
                }
            }
        }
    
    def generate_content(self, content_type: ContentType, platform: str, 
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate platform-specific content based on type and context."""
        
        if platform not in self.templates:
            raise ValueError(f"Platform {platform} not supported")
        
        if content_type not in self.templates[platform]:
            # Fallback to announcement if specific type not available
            content_type = ContentType.ANNOUNCEMENT
        
        template = self.templates[platform][content_type]
        
        # Generate content based on template and context
        content = self._fill_template(template, context)
        
        return {
            "text": content["text"],
            "hashtags": content["hashtags"],
            "media_requirements": content["media_requirements"],
            "optimal_time": template.optimal_time,
            "tone": template.tone,
            "platform_guidelines": self.content_guidelines.get(platform, {}),
            "schedule_recommendation": template.schedule.value if template.schedule else None
        }
    
    def _fill_template(self, template: ContentTemplate, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fill template with context data."""
        
        # Extract relevant context based on content type
        if template.content_type == ContentType.ANNOUNCEMENT:
            filled_text = template.template.format(
                title=context.get("title", "New Update Available"),
                description=context.get("description", "We've made improvements to AetherPost"),
                call_to_action=context.get("call_to_action", "Check it out!"),
                detailed_description=context.get("detailed_description", context.get("description", "")),
                benefits=context.get("benefits", "• Improved performance\n• Better user experience"),
                story_prompt=context.get("story_prompt", "Share this in your stories!"),
                motivation=context.get("motivation", "To help developers save time on social media")
            )
        
        elif template.content_type == ContentType.MAINTENANCE:
            filled_text = template.template.format(
                maintenance_type=context.get("maintenance_type", "Scheduled Maintenance"),
                description=context.get("description", "System updates and improvements"),
                schedule=context.get("schedule", "Today 2:00-4:00 AM UTC"),
                impact=context.get("impact", "Minimal service interruption expected")
            )
        
        elif template.content_type == ContentType.ENGAGEMENT:
            filled_text = template.template.format(
                question=context.get("question", "What's your biggest social media automation challenge?"),
                context=context.get("context", "We're always looking to improve AetherPost based on real developer needs.")
            )
        
        elif template.content_type == ContentType.EDUCATIONAL:
            filled_text = template.template.format(
                tip_title=context.get("tip_title", "Automation Best Practices"),
                tip_content=context.get("tip_content", "Start small, then scale your automation strategy."),
                tutorial_title=context.get("tutorial_title", "How to Automate Social Media"),
                step_by_step=context.get("step_by_step", "1. Set up your accounts\n2. Configure AetherPost\n3. Create your first campaign"),
                pro_tips=context.get("pro_tips", "• Test before automating\n• Monitor engagement\n• Adjust based on results"),
                video_outline=context.get("video_outline", "• Introduction\n• Setup process\n• Best practices\n• Q&A"),
                timestamps=context.get("timestamps", "0:00 - Intro\n2:30 - Setup\n8:45 - Demo"),
                resources=context.get("resources", "GitHub: github.com/fununnn/aetherpost\nDocs: aether-post.com")
            )
        
        elif template.content_type == ContentType.PERIODIC:
            filled_text = template.template.format(
                accomplishments=context.get("accomplishments", "Bug fixes and performance improvements"),
                in_progress=context.get("in_progress", "New platform integrations"),
                next_week=context.get("next_week", "Enhanced analytics dashboard")
            )
        
        elif template.content_type == ContentType.BEHIND_SCENES:
            filled_text = template.template.format(
                development_story=context.get("development_story", "Building AetherPost has been an incredible journey"),
                challenges_overcome=context.get("challenges_overcome", "API rate limits and authentication flows"),
                team_insights=context.get("team_insights", "We've learned so much about developer workflows"),
                development_scenario=context.get("development_scenario", "You're building a social media automation tool"),
                process_reveal=context.get("process_reveal", "Here's how we handle multi-platform posting"),
                outcome=context.get("outcome", "Seamless automation across all platforms")
            )
        
        elif template.content_type == ContentType.COMMUNITY:
            filled_text = template.template.format(
                user_story=context.get("user_story", "Developer saves 10 hours/week with AetherPost"),
                implementation_details=context.get("implementation_details", "Custom automation workflows"),
                results=context.get("results", "• 300% more engagement\n• 50% time savings"),
                lessons=context.get("lessons", "Consistency is key to social media success"),
                username=context.get("username", "awesome_developer")
            )
        
        else:
            # Generic template filling
            filled_text = template.template.format(**context)
        
        # Ensure content fits platform limits
        if template.max_length and len(filled_text) > template.max_length:
            # Smart truncation while preserving important parts
            filled_text = self._smart_truncate(filled_text, template.max_length)
        
        return {
            "text": filled_text,
            "hashtags": template.hashtags,
            "media_requirements": {
                "required": template.requires_media,
                "type": "image" if template.platform in ["instagram", "tiktok"] else "optional",
                "style": self._get_media_style(template.content_type, template.platform)
            }
        }
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Smart truncation that preserves important parts."""
        if len(text) <= max_length:
            return text
        
        # Find good truncation points (sentences, paragraphs)
        truncation_points = [
            text.rfind('.', 0, max_length - 3),
            text.rfind('\n', 0, max_length - 3),
            text.rfind(' ', 0, max_length - 3)
        ]
        
        best_point = max([p for p in truncation_points if p > max_length * 0.8])
        
        if best_point > 0:
            return text[:best_point] + "..."
        else:
            return text[:max_length - 3] + "..."
    
    def _get_media_style(self, content_type: ContentType, platform: str) -> str:
        """Get recommended media style for content type and platform."""
        media_styles = {
            ("announcement", "instagram"): "product_showcase",
            ("announcement", "twitter"): "logo_with_text",
            ("educational", "instagram"): "step_by_step_visual",
            ("educational", "youtube"): "tutorial_thumbnail",
            ("behind_scenes", "instagram"): "candid_development",
            ("behind_scenes", "tiktok"): "screen_recording_with_face",
            ("maintenance", "twitter"): "status_graphic",
            ("engagement", "instagram"): "question_graphic",
        }
        
        return media_styles.get((content_type.value, platform), "generic_branded")
    
    def get_posting_schedule(self, content_type: ContentType, platform: str) -> Optional[PostingSchedule]:
        """Get recommended posting schedule for content type and platform."""
        if platform in self.templates and content_type in self.templates[platform]:
            return self.templates[platform][content_type].schedule
        return None
    
    def get_optimal_times(self, platform: str) -> List[str]:
        """Get optimal posting times for platform."""
        optimal_times = {
            "twitter": ["09:00", "13:00", "17:00"],
            "instagram": ["11:00", "14:00", "17:00", "20:00"],
            "youtube": ["14:00", "18:00", "20:00"],
            "reddit": ["10:00", "14:00", "19:00"],
            "tiktok": ["06:00", "09:00", "19:00", "21:00"]
        }
        
        return optimal_times.get(platform, ["12:00", "18:00"])
    
    def validate_content_appropriateness(self, content: str, platform: str, 
                                       content_type: ContentType) -> Dict[str, Any]:
        """Validate if content is appropriate for platform and type."""
        guidelines = self.content_guidelines.get(platform, {})
        
        validation_result = {
            "is_appropriate": True,
            "warnings": [],
            "suggestions": []
        }
        
        # Platform-specific validation
        if platform == "twitter":
            if len(content) > 280:
                validation_result["warnings"].append("Content exceeds Twitter character limit")
            
            hashtag_count = content.count('#')
            if hashtag_count > 3:
                validation_result["warnings"].append("Too many hashtags for Twitter (max 3 recommended)")
        
        elif platform == "instagram":
            if not any(word in content.lower() for word in ["visual", "image", "photo", "see"]):
                validation_result["suggestions"].append("Consider adding visual elements reference")
        
        elif platform == "reddit":
            if content_type == ContentType.PROMOTIONAL and "buy" in content.lower():
                validation_result["warnings"].append("Overly promotional content may be rejected by Reddit")
        
        elif platform == "tiktok":
            if len(content) < 50:
                validation_result["suggestions"].append("TikTok content can be more descriptive")
        
        return validation_result