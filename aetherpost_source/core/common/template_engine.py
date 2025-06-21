"""Unified template engine for all AetherPost content generation."""

import re
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

from .base_models import Platform, ContentType, TemplateContext
from .utils import truncate_smart, extract_hashtags

logger = logging.getLogger(__name__)


class TemplateStyle(Enum):
    """Template style variations."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    CASUAL = "casual"


@dataclass
class TemplateMetadata:
    """Metadata for templates."""
    name: str
    description: str
    platforms: List[Platform]
    content_types: List[ContentType]
    styles: List[TemplateStyle]
    tags: List[str] = field(default_factory=list)
    author: str = "AetherPost"
    version: str = "1.0"
    min_char_length: Optional[int] = None
    max_char_length: Optional[int] = None


@dataclass
class Template:
    """Universal template structure."""
    id: str
    metadata: TemplateMetadata
    template_string: str
    style_variants: Dict[TemplateStyle, str] = field(default_factory=dict)
    conditional_blocks: Dict[str, str] = field(default_factory=dict)
    post_processors: List[Callable[[str, Dict], str]] = field(default_factory=list)
    
    def render(self, context: TemplateContext, style: TemplateStyle = TemplateStyle.FRIENDLY,
               platform: Optional[Platform] = None) -> str:
        """Render template with context and style."""
        # Choose template variant
        if style in self.style_variants:
            template_text = self.style_variants[style]
        else:
            template_text = self.template_string
        
        # Process conditional blocks
        template_text = self._process_conditionals(template_text, context)
        
        # Apply style-specific formatting
        template_text = self._apply_style_formatting(template_text, style, platform)
        
        # Fill in template variables
        try:
            rendered = template_text.format(**context.to_dict())
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            # Try partial rendering
            rendered = self._safe_format(template_text, context.to_dict())
        
        # Apply post-processors
        for processor in self.post_processors:
            rendered = processor(rendered, context.to_dict())
        
        return rendered.strip()
    
    def _process_conditionals(self, template_text: str, context: TemplateContext) -> str:
        """Process conditional blocks in template."""
        # Pattern: {if:condition}content{/if}
        conditional_pattern = r'\{if:(\w+)\}(.*?)\{/if\}'
        
        def replace_conditional(match):
            condition = match.group(1)
            content = match.group(2)
            
            # Check if condition is met
            context_dict = context.to_dict()
            if condition in context_dict and context_dict[condition]:
                return content
            elif condition in self.conditional_blocks:
                return self.conditional_blocks[condition]
            else:
                return ""
        
        return re.sub(conditional_pattern, replace_conditional, template_text, flags=re.DOTALL)
    
    def _apply_style_formatting(self, template_text: str, style: TemplateStyle, 
                              platform: Optional[Platform]) -> str:
        """Apply style-specific formatting."""
        if style == TemplateStyle.PROFESSIONAL:
            # Remove excessive emojis, formal tone
            template_text = re.sub(r'[🎉🔥💯🚀]{2,}', '🚀', template_text)
            template_text = template_text.replace("awesome", "excellent")
            template_text = template_text.replace("amazing", "impressive")
        
        elif style == TemplateStyle.CREATIVE:
            # Add more emojis and expressive language
            template_text = re.sub(r'([.!])', r'\1 ✨', template_text)
            template_text = template_text.replace("good", "amazing")
            template_text = template_text.replace("nice", "fantastic")
        
        elif style == TemplateStyle.TECHNICAL:
            # Focus on technical aspects
            template_text = re.sub(r'[🎉🎊💖]', '', template_text)  # Remove non-technical emojis
            template_text = template_text.replace("users", "developers")
            template_text = template_text.replace("people", "engineers")
        
        # Platform-specific adjustments
        if platform == Platform.LINKEDIN:
            # More professional tone
            template_text = template_text.replace("Hey!", "Hello,")
            template_text = template_text.replace("guys", "professionals")
        
        elif platform == Platform.TIKTOK:
            # More energetic and trendy
            template_text = template_text.replace("Check out", "OMG look at")
            template_text = template_text.replace(".", "!!!")
        
        return template_text
    
    def _safe_format(self, template_text: str, context_dict: Dict[str, Any]) -> str:
        """Safely format template, handling missing variables."""
        # Find all template variables
        variables = re.findall(r'\{(\w+)\}', template_text)
        
        # Replace missing variables with placeholders or defaults
        for var in variables:
            if var not in context_dict:
                if var == "app_name":
                    context_dict[var] = "AetherPost"
                elif var == "author":
                    context_dict[var] = "AetherPost Team"
                elif var == "description":
                    context_dict[var] = "Social media automation for developers"
                else:
                    context_dict[var] = f"[{var}]"
        
        return template_text.format(**context_dict)


class TemplateEngine:
    """Unified template engine for all AetherPost features."""
    
    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self.template_registry: Dict[str, List[str]] = {}  # category -> template_ids
        self._load_core_templates()
    
    def register_template(self, template: Template, category: str = "general") -> None:
        """Register a new template."""
        self.templates[template.id] = template
        
        if category not in self.template_registry:
            self.template_registry[category] = []
        self.template_registry[category].append(template.id)
        
        logger.info(f"Registered template: {template.id} in category: {category}")
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def find_templates(self, platform: Optional[Platform] = None, 
                      content_type: Optional[ContentType] = None,
                      style: Optional[TemplateStyle] = None,
                      category: Optional[str] = None) -> List[Template]:
        """Find templates matching criteria."""
        templates = []
        
        # Start with category filter if specified
        if category and category in self.template_registry:
            template_ids = self.template_registry[category]
        else:
            template_ids = list(self.templates.keys())
        
        for template_id in template_ids:
            template = self.templates[template_id]
            
            # Apply filters
            if platform and platform not in template.metadata.platforms:
                continue
            if content_type and content_type not in template.metadata.content_types:
                continue
            if style and style not in template.metadata.styles:
                continue
            
            templates.append(template)
        
        return templates
    
    def render_template(self, template_id: str, context: TemplateContext,
                       style: TemplateStyle = TemplateStyle.FRIENDLY,
                       platform: Optional[Platform] = None,
                       max_length: Optional[int] = None) -> str:
        """Render template with context."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        rendered = template.render(context, style, platform)
        
        # Apply length constraints if specified
        if max_length and len(rendered) > max_length:
            rendered = truncate_smart(rendered, max_length)
        
        return rendered
    
    def _load_core_templates(self) -> None:
        """Load core templates used across AetherPost."""
        
        # Social Media Post Templates
        self._register_social_templates()
        
        # Profile Templates
        self._register_profile_templates()
        
        # Campaign Templates
        self._register_campaign_templates()
        
        # Blog Templates
        self._register_blog_templates()
        
        # Notification Templates
        self._register_notification_templates()
    
    def _register_social_templates(self) -> None:
        """Register social media post templates."""
        
        # Announcement Template
        announcement_template = Template(
            id="social_announcement",
            metadata=TemplateMetadata(
                name="Social Media Announcement",
                description="General announcement template for social platforms",
                platforms=[Platform.TWITTER, Platform.INSTAGRAM, Platform.LINKEDIN],
                content_types=[ContentType.ANNOUNCEMENT],
                styles=[TemplateStyle.PROFESSIONAL, TemplateStyle.FRIENDLY, TemplateStyle.CREATIVE]
            ),
            template_string="🚀 {announcement_title}\n\n{description}\n\n{call_to_action}",
            style_variants={
                TemplateStyle.PROFESSIONAL: "📢 {announcement_title}\n\n{description}\n\n{call_to_action}",
                TemplateStyle.CREATIVE: "🎉✨ {announcement_title} ✨🎉\n\n{description}\n\n{call_to_action} 🔥",
                TemplateStyle.TECHNICAL: "🔧 {announcement_title}\n\n{description}\n\nTechnical details: {call_to_action}"
            }
        )
        self.register_template(announcement_template, "social")
        
        # Educational Content Template
        educational_template = Template(
            id="social_educational",
            metadata=TemplateMetadata(
                name="Educational Content",
                description="Template for educational and tutorial content",
                platforms=[Platform.TWITTER, Platform.LINKEDIN, Platform.YOUTUBE],
                content_types=[ContentType.EDUCATIONAL],
                styles=[TemplateStyle.FRIENDLY, TemplateStyle.TECHNICAL]
            ),
            template_string="💡 {tip_title}\n\n{tip_content}\n\n{learning_cta}",
            style_variants={
                TemplateStyle.TECHNICAL: "📚 {tip_title}\n\nTechnical breakdown:\n{tip_content}\n\n{learning_cta}",
                TemplateStyle.FRIENDLY: "🌟 {tip_title}\n\n{tip_content}\n\nHope this helps! {learning_cta}"
            }
        )
        self.register_template(educational_template, "social")
        
        # Community Engagement Template
        engagement_template = Template(
            id="social_engagement",
            metadata=TemplateMetadata(
                name="Community Engagement",
                description="Template for community interaction and discussion",
                platforms=[Platform.TWITTER, Platform.REDDIT, Platform.DISCORD],
                content_types=[ContentType.ENGAGEMENT, ContentType.COMMUNITY],
                styles=[TemplateStyle.FRIENDLY, TemplateStyle.CASUAL]
            ),
            template_string="💭 {question}\n\n{context}\n\nWhat do you think? Share your thoughts! 👇",
            style_variants={
                TemplateStyle.CASUAL: "Hey everyone! 👋\n\n{question}\n\n{context}\n\nLet me know what you think! 😊"
            }
        )
        self.register_template(engagement_template, "social")
    
    def _register_profile_templates(self) -> None:
        """Register profile bio templates."""
        
        # General Profile Bio
        profile_bio_template = Template(
            id="profile_bio_general",
            metadata=TemplateMetadata(
                name="General Profile Bio",
                description="Versatile bio template for most platforms",
                platforms=[Platform.TWITTER, Platform.INSTAGRAM, Platform.LINKEDIN],
                content_types=[ContentType.PROMOTIONAL],
                styles=[TemplateStyle.PROFESSIONAL, TemplateStyle.FRIENDLY, TemplateStyle.CREATIVE]
            ),
            template_string="Building {app_name} | {description} | {call_to_action}",
            style_variants={
                TemplateStyle.FRIENDLY: "👋 Building {app_name}! {description}. {call_to_action}",
                TemplateStyle.PROFESSIONAL: "Creator of {app_name} - {description}. {call_to_action}",
                TemplateStyle.CREATIVE: "🚀 {app_name} creator | {description} | {call_to_action} ✨"
            }
        )
        self.register_template(profile_bio_template, "profile")
        
        # Technical Profile Bio
        tech_bio_template = Template(
            id="profile_bio_technical",
            metadata=TemplateMetadata(
                name="Technical Profile Bio",
                description="Bio template focused on technical aspects",
                platforms=[Platform.GITHUB, Platform.LINKEDIN],
                content_types=[ContentType.TECHNICAL],
                styles=[TemplateStyle.TECHNICAL, TemplateStyle.PROFESSIONAL]
            ),
            template_string="Building {app_name} | {tech_stack} Developer | {description}",
            style_variants={
                TemplateStyle.TECHNICAL: "{tech_stack} Developer | Building {app_name} | Open Source Enthusiast"
            }
        )
        self.register_template(tech_bio_template, "profile")
    
    def _register_campaign_templates(self) -> None:
        """Register campaign-specific templates."""
        
        # Seasonal Campaign Template
        seasonal_template = Template(
            id="campaign_seasonal",
            metadata=TemplateMetadata(
                name="Seasonal Campaign",
                description="Template for seasonal events and holidays",
                platforms=[Platform.TWITTER, Platform.INSTAGRAM],
                content_types=[ContentType.SEASONAL],
                styles=[TemplateStyle.CREATIVE, TemplateStyle.FRIENDLY]
            ),
            template_string="{seasonal_emoji} {seasonal_greeting}\n\n{seasonal_message}\n\n{seasonal_cta}",
            conditional_blocks={
                "special_offer": "\n\n🎁 Special offer: {offer_details}"
            }
        )
        self.register_template(seasonal_template, "campaign")
        
        # Product Launch Campaign
        launch_template = Template(
            id="campaign_launch",
            metadata=TemplateMetadata(
                name="Product Launch",
                description="Template for product launches and major announcements",
                platforms=[Platform.TWITTER, Platform.LINKEDIN, Platform.REDDIT],
                content_types=[ContentType.ANNOUNCEMENT],
                styles=[TemplateStyle.PROFESSIONAL, TemplateStyle.CREATIVE]
            ),
            template_string="🎉 Introducing {product_name}!\n\n{product_description}\n\n✨ Key features:\n{feature_list}\n\n{launch_cta}",
            style_variants={
                TemplateStyle.PROFESSIONAL: "📢 We're excited to announce {product_name}.\n\n{product_description}\n\nKey capabilities:\n{feature_list}\n\n{launch_cta}"
            }
        )
        self.register_template(launch_template, "campaign")
    
    def _register_blog_templates(self) -> None:
        """Register blog content templates."""
        
        # Tutorial Blog Template
        tutorial_blog_template = Template(
            id="blog_tutorial",
            metadata=TemplateMetadata(
                name="Tutorial Blog Post",
                description="Template for tutorial and how-to blog posts",
                platforms=[Platform.LINKEDIN],  # Blog-style content
                content_types=[ContentType.EDUCATIONAL],
                styles=[TemplateStyle.FRIENDLY, TemplateStyle.TECHNICAL]
            ),
            template_string="📚 {tutorial_title}\n\nIn this guide, you'll learn:\n{learning_objectives}\n\n{tutorial_preview}\n\nRead the full tutorial: {blog_link}",
            style_variants={
                TemplateStyle.TECHNICAL: "🔧 {tutorial_title}\n\nTechnical overview:\n{learning_objectives}\n\n{tutorial_preview}\n\nFull implementation details: {blog_link}"
            }
        )
        self.register_template(tutorial_blog_template, "blog")
    
    def _register_notification_templates(self) -> None:
        """Register notification templates."""
        
        # Preview Notification Template
        preview_notification_template = Template(
            id="notification_preview",
            metadata=TemplateMetadata(
                name="Content Preview Notification",
                description="Template for content preview notifications",
                platforms=[Platform.SLACK, Platform.DISCORD],
                content_types=[ContentType.ANNOUNCEMENT],
                styles=[TemplateStyle.PROFESSIONAL]
            ),
            template_string="📋 Content Preview Ready: {campaign_name}\n\nPlatforms: {platform_count}\nEstimated Reach: {total_reach:,}\n\nReview and approve the content for publishing.",
        )
        self.register_template(preview_notification_template, "notification")


# Global template engine instance
template_engine = TemplateEngine()


# Utility functions for template creation
def create_simple_template(template_id: str, template_string: str, 
                          platforms: List[Platform], content_types: List[ContentType],
                          name: str = None, description: str = None) -> Template:
    """Create a simple template with minimal configuration."""
    return Template(
        id=template_id,
        metadata=TemplateMetadata(
            name=name or template_id.replace("_", " ").title(),
            description=description or f"Template for {template_id}",
            platforms=platforms,
            content_types=content_types,
            styles=[TemplateStyle.FRIENDLY]  # Default style
        ),
        template_string=template_string
    )


def register_custom_template(template_id: str, template_string: str,
                           platforms: List[str], content_types: List[str],
                           category: str = "custom", **kwargs) -> None:
    """Register a custom template from simple parameters."""
    platform_enums = [Platform(p) for p in platforms]
    content_type_enums = [ContentType(ct) for ct in content_types]
    
    template = create_simple_template(
        template_id, template_string, platform_enums, content_type_enums, **kwargs
    )
    
    template_engine.register_template(template, category)