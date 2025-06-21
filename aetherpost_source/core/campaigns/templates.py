"""Campaign templates for seasonal events and marketing campaigns."""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import logging

logger = logging.getLogger(__name__)

class CampaignType(Enum):
    """Types of marketing campaigns."""
    SEASONAL = "seasonal"          # Halloween, Christmas, etc.
    PRODUCT_LAUNCH = "product_launch"
    MILESTONE = "milestone"        # Company anniversary, user milestones
    AWARENESS = "awareness"        # Brand awareness, educational
    PROMOTION = "promotion"        # Sales, discounts, special offers
    COMMUNITY = "community"        # User-generated content, contests
    EDUCATIONAL = "educational"    # Tutorials, tips, knowledge sharing

class CampaignPhase(Enum):
    """Phases of a campaign."""
    TEASER = "teaser"             # Build anticipation (2-3 weeks before)
    ANNOUNCEMENT = "announcement"  # Official announcement (1 week before)
    BUILD_UP = "build_up"         # Increase excitement (3-5 days before)
    EVENT_DAY = "event_day"       # Day of the event
    FOLLOW_UP = "follow_up"       # Thank you, results (1-3 days after)
    REFLECTION = "reflection"     # Lessons learned, next steps (1 week after)

@dataclass
class CampaignContent:
    """Content for a specific campaign phase."""
    phase: CampaignPhase
    platform: str
    content_type: str
    text_template: str
    hashtags: List[str]
    visual_elements: Dict[str, Any]
    optimal_time: Optional[str] = None
    priority: int = 1  # 1=high, 2=medium, 3=low
    
    def format_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Format template with context variables."""
        try:
            formatted_text = self.text_template.format(**context)
            return {
                "text": formatted_text,
                "hashtags": [tag.format(**context) if "{" in tag else tag for tag in self.hashtags],
                "visual_elements": self.visual_elements,
                "platform": self.platform,
                "phase": self.phase.value,
                "priority": self.priority
            }
        except KeyError as e:
            logger.warning(f"Missing context variable: {e}")
            return {
                "text": self.text_template,
                "hashtags": self.hashtags,
                "visual_elements": self.visual_elements,
                "platform": self.platform,
                "phase": self.phase.value,
                "priority": self.priority
            }

@dataclass
class CampaignTemplate:
    """Template for a complete marketing campaign."""
    name: str
    campaign_type: CampaignType
    description: str
    duration_days: int
    target_date: Optional[datetime] = None
    content_pieces: List[CampaignContent] = field(default_factory=list)
    theme_colors: List[str] = field(default_factory=list)
    key_hashtags: List[str] = field(default_factory=list)
    target_audience: str = "general"
    success_metrics: List[str] = field(default_factory=list)
    
    def get_content_for_phase(self, phase: CampaignPhase, platform: Optional[str] = None) -> List[CampaignContent]:
        """Get content for specific phase and optionally platform."""
        content = [c for c in self.content_pieces if c.phase == phase]
        if platform:
            content = [c for c in content if c.platform == platform]
        return sorted(content, key=lambda x: x.priority)
    
    def get_campaign_schedule(self, event_date: datetime) -> Dict[str, List[Dict[str, Any]]]:
        """Generate posting schedule based on event date."""
        schedule = {}
        
        # Define phase timing relative to event date
        phase_offsets = {
            CampaignPhase.TEASER: -21,        # 3 weeks before
            CampaignPhase.ANNOUNCEMENT: -7,    # 1 week before  
            CampaignPhase.BUILD_UP: -3,       # 3 days before
            CampaignPhase.EVENT_DAY: 0,       # Day of event
            CampaignPhase.FOLLOW_UP: 1,       # 1 day after
            CampaignPhase.REFLECTION: 7       # 1 week after
        }
        
        for phase, offset in phase_offsets.items():
            phase_date = event_date + timedelta(days=offset)
            phase_content = self.get_content_for_phase(phase)
            
            schedule[phase_date.strftime('%Y-%m-%d')] = [
                {
                    "content": content,
                    "scheduled_time": phase_date.strftime('%Y-%m-%d'),
                    "phase": phase.value
                }
                for content in phase_content
            ]
        
        return schedule

class CampaignTemplateLibrary:
    """Library of pre-built campaign templates."""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, CampaignTemplate]:
        """Load all campaign templates."""
        templates = {}
        
        # Halloween Campaign
        templates["halloween"] = self._create_halloween_template()
        
        # Christmas Campaign
        templates["christmas"] = self._create_christmas_template()
        
        # New Year Campaign - use milestone template as base
        new_year_template = self._create_milestone_template()
        new_year_template.name = "new_year"
        new_year_template.display_name = "New Year Celebration"
        new_year_template.description = "Celebrate the new year with your community"
        new_year_template.duration_days = 7
        templates["new_year"] = new_year_template
        
        # Product Launch Campaign
        templates["product_launch"] = self._create_product_launch_template()
        
        # Milestone Campaign
        templates["milestone"] = self._create_milestone_template()
        
        # Community Appreciation
        templates["community_appreciation"] = self._create_community_template()
        
        # Educational Series
        templates["educational_series"] = self._create_educational_template()
        
        # Back to School
        templates["back_to_school"] = self._create_back_to_school_template()
        
        # Spring Launch
        templates["spring_launch"] = self._create_spring_template()
        
        # Summer Update
        templates["summer_update"] = self._create_summer_template()
        
        return templates
    
    def _create_halloween_template(self) -> CampaignTemplate:
        """Create Halloween campaign template."""
        content_pieces = [
            # Teaser Phase
            CampaignContent(
                phase=CampaignPhase.TEASER,
                platform="twitter",
                content_type="teaser",
                text_template="🎃 Something spooky is coming to {app_name}... 👻\n\nCan you guess what we're cooking up for Halloween? 🕷️\n\n#ComingSoon #Mystery",
                hashtags=["Halloween2024", "ComingSoon", "Spooky", "{app_name}"],
                visual_elements={"theme": "dark_orange", "emojis": ["🎃", "👻", "🕷️", "🦇"]},
                optimal_time="18:00"
            ),
            
            CampaignContent(
                phase=CampaignPhase.TEASER,
                platform="instagram", 
                content_type="teaser",
                text_template="🦇 The veil between worlds grows thin... and so does the barrier between you and our upcoming Halloween surprise! 🎃\n\nSomething wickedly awesome is brewing in the {app_name} cauldron. Our developers have been working by candlelight (okay, maybe just RGB lighting) to conjure up something special.\n\n👻 What do you think it could be?\n• Spooky new features?\n• Haunted UI themes?\n• Ghostly automation tricks?\n\nDrop your guesses below! 🕸️\n\n#Halloween2024 #ComingSoon #SpookyTech #Developers",
                hashtags=["Halloween2024", "ComingSoon", "SpookyTech", "Developers", "{app_name}", "CodingLife"],
                visual_elements={"theme": "dark_orange", "style": "spooky", "mood": "mysterious"},
                optimal_time="20:00"
            ),
            
            # Announcement Phase
            CampaignContent(
                phase=CampaignPhase.ANNOUNCEMENT,
                platform="twitter",
                content_type="announcement",
                text_template="🎃 TRICK OR TREAT! 🍬\n\nIntroducing {feature_name} - our spookiest feature yet! Perfect for developers who want to automate their social media while dressed as code wizards 🧙‍♂️\n\n👻 Available now in {app_name}\n🦇 Limited time Halloween theme\n\n#Halloween2024 #NewFeature",
                hashtags=["Halloween2024", "NewFeature", "TrickOrTreat", "{app_name}"],
                visual_elements={"theme": "orange_black", "emojis": ["🎃", "🍬", "👻", "🦇"]},
                optimal_time="10:00",
                priority=1
            ),
            
            CampaignContent(
                phase=CampaignPhase.ANNOUNCEMENT,
                platform="reddit",
                content_type="announcement", 
                text_template="🎃 Happy Halloween from {app_name}! Introducing {feature_name}\n\n**Trick or Treat?** Definitely treat! We've been working on this spooky good feature that makes social media automation even more magical.\n\n**What's new:**\n• {feature_description}\n• Halloween-themed UI (limited time!)\n• Spooky automation templates\n• Ghostly performance improvements\n\n**Perfect for:**\n• Developers who want automated social media\n• Teams running Halloween campaigns\n• Anyone who loves seasonal themes\n\n**GitHub:** {github_url}\n\nHappy coding, and Happy Halloween! 🦇👻\n\nWhat's your favorite Halloween coding tradition?",
                hashtags=[],  # Reddit doesn't use hashtags
                visual_elements={"theme": "halloween", "mood": "friendly_spooky"},
                optimal_time="14:00",
                priority=1
            ),
            
            # Build-up Phase
            CampaignContent(
                phase=CampaignPhase.BUILD_UP,
                platform="twitter",
                content_type="engagement",
                text_template="🕷️ 2 days until Halloween! 🎃\n\nOur {feature_name} is ready to haunt your workflow (in the best way)! \n\n👻 Who's planning spooky social media posts this weekend?\n\n#Halloween2024 #SocialMedia #Automation",
                hashtags=["Halloween2024", "SocialMedia", "Automation", "WeekendVibes"],
                visual_elements={"countdown": True, "urgency": "medium"},
                optimal_time="15:00"
            ),
            
            # Event Day
            CampaignContent(
                phase=CampaignPhase.EVENT_DAY,
                platform="twitter",
                content_type="celebration",
                text_template="🎃 HAPPY HALLOWEEN! 👻\n\nThe spookiest day of the year deserves automated social media! Let {app_name} handle your posts while you handle the trick-or-treaters 🍬\n\n🦇 Use code SPOOKY for Halloween theme\n\n#Halloween2024 #TrickOrTreat",
                hashtags=["Halloween2024", "TrickOrTreat", "HappyHalloween"],
                visual_elements={"theme": "celebration", "energy": "high"},
                optimal_time="12:00",
                priority=1
            ),
            
            CampaignContent(
                phase=CampaignPhase.EVENT_DAY,
                platform="instagram",
                content_type="celebration",
                text_template="🎃👻 HAPPY HALLOWEEN! 🦇🕷️\n\nWhile you're out collecting candy (or giving it away), {app_name} is here to handle your social media automation! \n\nOur Halloween special features:\n🍬 Spooky content templates\n👻 Automated Halloween hashtags\n🎃 Seasonal posting schedules\n🦇 Dark theme (perfect for today!)\n\nWhether you're a coding witch, a DevOps wizard, or a full-stack phantom, we've got you covered!\n\nShow us your Halloween coding setup in the comments! 🧙‍♂️💻\n\n#Halloween2024 #CodingLife #Developers #SpookyTech #TrickOrTreat #HappyHalloween",
                hashtags=["Halloween2024", "CodingLife", "Developers", "SpookyTech", "TrickOrTreat", "HappyHalloween"],
                visual_elements={"theme": "celebration", "style": "festive"},
                optimal_time="16:00",
                priority=1
            ),
            
            # Follow-up Phase
            CampaignContent(
                phase=CampaignPhase.FOLLOW_UP,
                platform="twitter",
                content_type="gratitude",
                text_template="👻 Hope everyone had a spook-tacular Halloween! 🎃\n\nThank you to everyone who tried our Halloween features! The response has been boo-tiful 💀\n\nDid you automate any spooky posts yesterday? Share your favorites! 🦇",
                hashtags=["Halloween2024", "ThankYou", "Community"],
                visual_elements={"theme": "gratitude", "mood": "warm"},
                optimal_time="11:00"
            )
        ]
        
        return CampaignTemplate(
            name="Halloween Campaign",
            campaign_type=CampaignType.SEASONAL,
            description="Spooky seasonal campaign for Halloween with automation theme",
            duration_days=30,
            content_pieces=content_pieces,
            theme_colors=["#FF6600", "#000000", "#8B4513"],  # Orange, Black, Brown
            key_hashtags=["Halloween2024", "SpookyTech", "TrickOrTreat"],
            target_audience="developers",
            success_metrics=["engagement_rate", "feature_adoption", "brand_sentiment"]
        )
    
    def _create_christmas_template(self) -> CampaignTemplate:
        """Create Christmas campaign template."""
        content_pieces = [
            CampaignContent(
                phase=CampaignPhase.TEASER,
                platform="twitter",
                content_type="teaser",
                text_template="🎄 Ho ho ho! Something merry is coming to {app_name}... 🎅\n\nSanta's elves have been busy coding! Can you guess what Christmas surprise we're wrapping up? 🎁\n\n#ChristmasIsComing #SantasCoders",
                hashtags=["Christmas2024", "ChristmasIsComing", "SantasCoders", "{app_name}"],
                visual_elements={"theme": "red_green", "emojis": ["🎄", "🎅", "🎁", "❄️"]},
                optimal_time="09:00"
            ),
            
            CampaignContent(
                phase=CampaignPhase.ANNOUNCEMENT,
                platform="twitter",
                content_type="announcement",
                text_template="🎅 HO HO HO! 🎄\n\n{app_name} Christmas Edition is here! 🎁\n\n✨ Holiday themes\n❄️ Festive automation\n🦌 Seasonal content templates\n\nMaking your social media merry and bright! \n\n#Christmas2024 #HolidayMagic",
                hashtags=["Christmas2024", "HolidayMagic", "ChristmasGift", "{app_name}"],
                visual_elements={"theme": "christmas", "mood": "festive"},
                optimal_time="10:00",
                priority=1
            ),
            
            CampaignContent(
                phase=CampaignPhase.EVENT_DAY,
                platform="twitter",
                content_type="celebration",
                text_template="🎄 MERRY CHRISTMAS! 🎅\n\nWishing all our amazing developers a holiday filled with bug-free code and infinite joy! \n\nMay your commits be merry and your deployments bright! ✨\n\n#MerryChristmas #DevCommunity",
                hashtags=["MerryChristmas", "DevCommunity", "Christmas2024", "HappyHolidays"],
                visual_elements={"theme": "celebration", "energy": "warm"},
                optimal_time="12:00",
                priority=1
            )
        ]
        
        return CampaignTemplate(
            name="Christmas Campaign",
            campaign_type=CampaignType.SEASONAL,
            description="Festive Christmas campaign with holiday themes",
            duration_days=25,
            content_pieces=content_pieces,
            theme_colors=["#DC143C", "#228B22", "#FFD700"],  # Red, Green, Gold
            key_hashtags=["Christmas2024", "HolidayMagic", "DevCommunity"],
            target_audience="developers",
            success_metrics=["engagement_rate", "holiday_sentiment", "community_growth"]
        )
    
    def _create_product_launch_template(self) -> CampaignTemplate:
        """Create product launch campaign template."""
        content_pieces = [
            CampaignContent(
                phase=CampaignPhase.TEASER,
                platform="twitter", 
                content_type="teaser",
                text_template="🚀 Big things are coming to {app_name}... \n\nWe've been working on something that will change how you think about {product_category}. \n\nStay tuned! 👀\n\n#ComingSoon #Innovation",
                hashtags=["ComingSoon", "Innovation", "{app_name}", "BigNews"],
                visual_elements={"theme": "anticipation", "energy": "building"},
                optimal_time="10:00"
            ),
            
            CampaignContent(
                phase=CampaignPhase.ANNOUNCEMENT,
                platform="twitter",
                content_type="announcement",
                text_template="🎉 INTRODUCING {product_name}! 🚀\n\n{product_description}\n\n✨ Key features:\n{feature_list}\n\n🔗 Try it now: {product_url}\n\n#LaunchDay #NewProduct",
                hashtags=["LaunchDay", "NewProduct", "{product_name}", "{app_name}"],
                visual_elements={"theme": "launch", "energy": "high"},
                optimal_time="09:00",
                priority=1
            )
        ]
        
        return CampaignTemplate(
            name="Product Launch",
            campaign_type=CampaignType.PRODUCT_LAUNCH,
            description="Complete product launch campaign with announcement sequence",
            duration_days=14,
            content_pieces=content_pieces,
            theme_colors=["#007BFF", "#28A745", "#FFC107"],
            key_hashtags=["LaunchDay", "NewProduct", "Innovation"],
            target_audience="general",
            success_metrics=["reach", "click_through_rate", "conversion_rate"]
        )
    
    def _create_milestone_template(self) -> CampaignTemplate:
        """Create milestone celebration campaign."""
        content_pieces = [
            CampaignContent(
                phase=CampaignPhase.ANNOUNCEMENT,
                platform="twitter",
                content_type="celebration",
                text_template="🎉 MILESTONE ALERT! 🎊\n\nWe just hit {milestone_number} {milestone_type}! \n\nThank you to our amazing community for making this possible! 💖\n\n{milestone_message}\n\n#Milestone #ThankYou",
                hashtags=["Milestone", "ThankYou", "{milestone_type}", "{app_name}"],
                visual_elements={"theme": "celebration", "mood": "grateful"},
                optimal_time="12:00",
                priority=1
            )
        ]
        
        return CampaignTemplate(
            name="Milestone Celebration",
            campaign_type=CampaignType.MILESTONE,
            description="Celebrate company or product milestones",
            duration_days=7,
            content_pieces=content_pieces,
            theme_colors=["#FF69B4", "#FFD700", "#32CD32"],
            key_hashtags=["Milestone", "ThankYou", "Community"],
            target_audience="community",
            success_metrics=["engagement_rate", "sentiment", "community_response"]
        )
    
    def _create_community_template(self) -> CampaignTemplate:
        """Create community appreciation campaign."""
        return CampaignTemplate(
            name="Community Appreciation",
            campaign_type=CampaignType.COMMUNITY,
            description="Show appreciation for the developer community",
            duration_days=7,
            content_pieces=[],
            theme_colors=["#6F42C1", "#20C997", "#FD7E14"],
            key_hashtags=["Community", "ThankYou", "Developers"],
            target_audience="developers",
            success_metrics=["community_engagement", "user_generated_content"]
        )
    
    def _create_educational_template(self) -> CampaignTemplate:
        """Create educational content series campaign."""
        return CampaignTemplate(
            name="Educational Series",
            campaign_type=CampaignType.EDUCATIONAL,
            description="Educational content series for skill building",
            duration_days=21,
            content_pieces=[],
            theme_colors=["#17A2B8", "#6C757D", "#28A745"],
            key_hashtags=["Education", "Learning", "Tips"],
            target_audience="learners",
            success_metrics=["content_consumption", "skill_acquisition"]
        )
    
    def _create_back_to_school_template(self) -> CampaignTemplate:
        """Create back to school campaign."""
        content_pieces = [
            CampaignContent(
                phase=CampaignPhase.ANNOUNCEMENT,
                platform="twitter",
                content_type="educational",
                text_template="📚 Back to School Special! 🎒\n\nWhether you're learning to code or teaching others, {app_name} can help automate your educational content!\n\n🍎 Student discount available\n📖 Education templates included\n\n#BackToSchool #Learning",
                hashtags=["BackToSchool", "Learning", "Education", "{app_name}"],
                visual_elements={"theme": "academic", "emojis": ["📚", "🎒", "🍎", "📖"]},
                optimal_time="08:00"
            )
        ]
        
        return CampaignTemplate(
            name="Back to School",
            campaign_type=CampaignType.SEASONAL,
            description="Back to school themed campaign for education sector",
            duration_days=14,
            content_pieces=content_pieces,
            theme_colors=["#FF6B35", "#004E89", "#009639"],
            key_hashtags=["BackToSchool", "Learning", "Education"],
            target_audience="students_educators",
            success_metrics=["educational_engagement", "student_signups"]
        )
    
    def _create_spring_template(self) -> CampaignTemplate:
        """Create spring campaign template."""
        return CampaignTemplate(
            name="Spring Launch",
            campaign_type=CampaignType.SEASONAL,
            description="Fresh spring campaign with renewal themes",
            duration_days=21,
            content_pieces=[],
            theme_colors=["#98D8C8", "#F7DC6F", "#F8C471"],
            key_hashtags=["SpringTime", "FreshStart", "Renewal"],
            target_audience="general",
            success_metrics=["seasonal_engagement", "renewal_rate"]
        )
    
    def _create_summer_template(self) -> CampaignTemplate:
        """Create summer campaign template."""
        return CampaignTemplate(
            name="Summer Update",
            campaign_type=CampaignType.SEASONAL,
            description="Summer-themed campaign with vacation and productivity balance",
            duration_days=30,
            content_pieces=[],
            theme_colors=["#FFE135", "#FF6B35", "#1E88E5"],
            key_hashtags=["SummerVibes", "WorkLifeBalance", "Productivity"],
            target_audience="professionals",
            success_metrics=["summer_engagement", "productivity_metrics"]
        )
    
    def get_template(self, template_name: str) -> Optional[CampaignTemplate]:
        """Get campaign template by name."""
        return self.templates.get(template_name.lower())
    
    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self.templates.keys())
    
    def get_templates_by_type(self, campaign_type: CampaignType) -> List[CampaignTemplate]:
        """Get templates filtered by campaign type."""
        return [t for t in self.templates.values() if t.campaign_type == campaign_type]
    
    def get_seasonal_templates(self) -> List[CampaignTemplate]:
        """Get all seasonal campaign templates."""
        return self.get_templates_by_type(CampaignType.SEASONAL)

# Global instance
campaign_library = CampaignTemplateLibrary()