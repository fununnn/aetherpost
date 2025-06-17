"""Enhanced Reddit automation and community engagement commands."""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from aetherpost.core.content.strategy import PlatformContentStrategy, ContentType
# import logging
# from aetherpost.cli.utils.ui import create_status_panel, print_success, print_error, print_warning
from aetherpost.cli.common.base_command import (
    ContentCommand, CommandMetadata, CommandCategory, CommandOption, 
    create_click_command
)
from aetherpost.core.common.base_models import Platform, ContentType as CommonContentType, OperationResult
from aetherpost.core.common.error_handler import handle_errors

logger = logging.getLogger(__name__)
console = Console()

@dataclass
class RedditSubreddit:
    """Reddit subreddit information."""
    name: str
    members: int
    description: str
    rules: List[str]
    optimal_post_times: List[str]
    content_preferences: List[str]
    moderation_level: str  # strict, moderate, relaxed

@dataclass
class RedditPost:
    """Reddit post data structure."""
    title: str
    content: str
    subreddit: str
    post_type: str  # text, link, image
    flair: Optional[str] = None
    scheduled_time: Optional[datetime] = None

class RedditEnhancedManager:
    """Enhanced Reddit automation and community management."""
    
    def __init__(self):
        self.strategy = PlatformContentStrategy()
        self.relevant_subreddits = self._load_relevant_subreddits()
        self.posting_history = []
    
    def _load_relevant_subreddits(self) -> List[RedditSubreddit]:
        """Load list of relevant subreddits for app promotion."""
        return [
            RedditSubreddit(
                name="r/sideproject",
                members=180000,
                description="Show off your side projects and get feedback",
                rules=[
                    "Must be your own project",
                    "Include 'Feedback Friday' tag for feedback",
                    "No duplicate posts within 30 days",
                    "Be active in comments"
                ],
                optimal_post_times=["10:00", "14:00", "19:00"],
                content_preferences=["building journey", "lessons learned", "honest feedback"],
                moderation_level="moderate"
            ),
            RedditSubreddit(
                name="r/devtools",
                members=25000,
                description="Tools and resources for developers",
                rules=[
                    "Must be relevant to developers",
                    "No pure promotional posts",
                    "Include technical details",
                    "Open source preferred"
                ],
                optimal_post_times=["09:00", "13:00", "16:00"],
                content_preferences=["technical benefits", "code examples", "open source"],
                moderation_level="strict"
            ),
            RedditSubreddit(
                name="r/programming",
                members=4200000,
                description="Computer programming discussion",
                rules=[
                    "High-quality technical content only",
                    "No self-promotion without value",
                    "Detailed technical explanations required",
                    "Community discussion focus"
                ],
                optimal_post_times=["08:00", "12:00", "17:00"],
                content_preferences=["technical deep-dives", "architecture", "algorithms"],
                moderation_level="strict"
            ),
            RedditSubreddit(
                name="r/webdev",
                members=800000,
                description="Web development community",
                rules=[
                    "Web development focus",
                    "Showcase projects welcome",
                    "Include technical stack info",
                    "Help others in community"
                ],
                optimal_post_times=["10:00", "15:00", "20:00"],
                content_preferences=["web technologies", "frameworks", "tools"],
                moderation_level="moderate"
            ),
            RedditSubreddit(
                name="r/opensource",
                members=180000,
                description="Open source software discussion",
                rules=[
                    "Must be open source",
                    "Include repository link",
                    "Explain project purpose clearly",
                    "Be responsive to questions"
                ],
                optimal_post_times=["11:00", "14:00", "18:00"],
                content_preferences=["open source", "community contribution", "collaboration"],
                moderation_level="relaxed"
            ),
            RedditSubreddit(
                name="r/node",
                members=150000,
                description="Node.js community",
                rules=[
                    "Node.js related content",
                    "Code examples encouraged",
                    "Help others with questions",
                    "Share learning resources"
                ],
                optimal_post_times=["09:00", "14:00", "19:00"],
                content_preferences=["node.js", "javascript", "npm packages"],
                moderation_level="moderate"
            ),
            RedditSubreddit(
                name="r/Python",
                members=1200000,
                description="Python programming community",
                rules=[
                    "Python related content",
                    "Include code examples",
                    "Educational value required",
                    "Be helpful to beginners"
                ],
                optimal_post_times=["10:00", "13:00", "16:00"],
                content_preferences=["python code", "libraries", "tutorials"],
                moderation_level="moderate"
            ),
            RedditSubreddit(
                name="r/automation",
                members=90000,
                description="Automation tools and techniques",
                rules=[
                    "Automation focus",
                    "Real-world examples",
                    "Explain benefits clearly",
                    "Share implementation details"
                ],
                optimal_post_times=["09:00", "12:00", "17:00"],
                content_preferences=["automation tools", "productivity", "time-saving"],
                moderation_level="relaxed"
            ),
            RedditSubreddit(
                name="r/socialmedia",
                members=75000,
                description="Social media marketing and strategy",
                rules=[
                    "Marketing focus allowed",
                    "Provide value to community",
                    "Case studies welcomed",
                    "No pure spam"
                ],
                optimal_post_times=["11:00", "15:00", "18:00"],
                content_preferences=["marketing strategies", "case studies", "tools"],
                moderation_level="moderate"
            ),
            RedditSubreddit(
                name="r/startups",
                members=850000,
                description="Startup community and discussion",
                rules=[
                    "Startup related content",
                    "Share journey and lessons",
                    "Provide value to entrepreneurs",
                    "No direct sales pitches"
                ],
                optimal_post_times=["10:00", "14:00", "19:00"],
                content_preferences=["startup journey", "lessons learned", "entrepreneurship"],
                moderation_level="moderate"
            )
        ]
    
    def analyze_subreddit_fit(self, subreddit: str, content_type: ContentType) -> Dict[str, Any]:
        """Analyze how well content fits a specific subreddit."""
        subreddit_data = next((s for s in self.relevant_subreddits if s.name.lower() == subreddit.lower()), None)
        
        if not subreddit_data:
            return {"fit_score": 0, "recommendations": ["Subreddit not in our database"]}
        
        fit_score = 0.5  # Base score
        recommendations = []
        
        # Analyze content type compatibility
        if content_type == ContentType.ANNOUNCEMENT:
            if "showcase" in subreddit_data.description.lower():
                fit_score += 0.3
            if subreddit_data.moderation_level == "strict":
                fit_score -= 0.2
                recommendations.append("Strict moderation - focus on technical value")
        
        elif content_type == ContentType.EDUCATIONAL:
            if any(word in subreddit_data.description.lower() for word in ["learning", "education", "tutorial"]):
                fit_score += 0.4
        
        # Check member count for reach potential
        if subreddit_data.members > 500000:
            fit_score += 0.1
            recommendations.append("Large audience - expect high competition")
        elif subreddit_data.members < 50000:
            recommendations.append("Smaller community - easier to get noticed")
        
        return {
            "fit_score": min(fit_score, 1.0),
            "recommendations": recommendations,
            "optimal_times": subreddit_data.optimal_post_times,
            "rules_to_follow": subreddit_data.rules,
            "content_preferences": subreddit_data.content_preferences
        }
    
    def generate_subreddit_specific_content(self, subreddit: str, context: Dict[str, Any]) -> RedditPost:
        """Generate content optimized for specific subreddit."""
        subreddit_data = next((s for s in self.relevant_subreddits if s.name.lower() == subreddit.lower()), None)
        
        if not subreddit_data:
            raise ValueError(f"Subreddit {subreddit} not supported")
        
        # Adjust content based on subreddit preferences
        adjusted_context = context.copy()
        
        if "technical" in subreddit_data.content_preferences:
            adjusted_context["include_technical"] = True
            adjusted_context["technical_details"] = context.get("technical_stack", "Node.js, Python, AWS")
        
        if "open source" in subreddit_data.content_preferences:
            adjusted_context["github_link"] = context.get("github_url", "https://github.com/fununnn/autopromo")
            adjusted_context["open_source_note"] = "This is an open source project - contributions welcome!"
        
        if "building journey" in subreddit_data.content_preferences:
            adjusted_context["journey_story"] = context.get("development_story", "Built this over 6 months to solve my own social media automation needs")
            adjusted_context["lessons"] = context.get("lessons_learned", "Learned so much about API integrations and rate limiting")
        
        # Generate base content
        content_data = self.strategy.generate_content(
            ContentType.ANNOUNCEMENT, 
            "reddit", 
            adjusted_context
        )
        
        # Customize for specific subreddit
        customized_content = self._customize_for_subreddit(content_data["text"], subreddit_data)
        
        return RedditPost(
            title=self._generate_title(subreddit_data, adjusted_context),
            content=customized_content,
            subreddit=subreddit,
            post_type="text"
        )
    
    def _customize_for_subreddit(self, base_content: str, subreddit_data: RedditSubreddit) -> str:
        """Customize content for specific subreddit culture and rules."""
        customizations = []
        
        if subreddit_data.name == "r/sideproject":
            customizations.append("\n\n**What I learned building this:**")
            customizations.append("• API rate limiting is tricky but manageable")
            customizations.append("• User feedback shapes the product roadmap")
            customizations.append("• Automation saves time but requires careful testing")
        
        elif subreddit_data.name == "r/devtools":
            customizations.append("\n\n**Technical Stack:**")
            customizations.append("• Backend: Python/FastAPI")
            customizations.append("• Frontend: React/TypeScript")
            customizations.append("• Infrastructure: AWS Lambda + DynamoDB")
            customizations.append("• Integrations: Twitter API v2, Instagram Basic Display, etc.")
        
        elif subreddit_data.name == "r/programming":
            customizations.append("\n\n**Interesting Technical Challenges:**")
            customizations.append("• Rate limiting across multiple APIs")
            customizations.append("• Content optimization algorithms")
            customizations.append("• Async processing for reliability")
            customizations.append("• Security considerations for OAuth flows")
        
        elif subreddit_data.name == "r/opensource":
            customizations.append("\n\n**Open Source Details:**")
            customizations.append("• MIT License")
            customizations.append("• GitHub: https://github.com/fununnn/autopromo")
            customizations.append("• Looking for contributors!")
            customizations.append("• Issues and PRs welcome")
        
        return base_content + "".join(customizations)
    
    def _generate_title(self, subreddit_data: RedditSubreddit, context: Dict[str, Any]) -> str:
        """Generate subreddit-appropriate title."""
        app_name = context.get("app_name", "AetherPost")
        
        title_templates = {
            "r/sideproject": f"Built {app_name} - Social media automation for developers [Seeking Feedback]",
            "r/devtools": f"{app_name}: CLI tool for automated social media posting",
            "r/programming": f"Architecture discussion: Building a multi-platform social media automation system",
            "r/webdev": f"Show HN: {app_name} - Automate your social media with code",
            "r/opensource": f"{app_name} - Open source social media automation (MIT License)",
            "r/node": f"{app_name}: Node.js-based social media automation CLI",
            "r/Python": f"Python tool for social media automation - {app_name}",
            "r/automation": f"Automate your social media posting across platforms with {app_name}",
            "r/socialmedia": f"Developer's approach to social media automation - {app_name}",
            "r/startups": f"How I automated my startup's social media and saved 10 hours/week"
        }
        
        return title_templates.get(subreddit_data.name, f"{app_name} - Automated social media management for developers")
    
    def suggest_posting_schedule(self, subreddits: List[str]) -> Dict[str, Any]:
        """Suggest optimal posting schedule across multiple subreddits."""
        schedule = {}
        
        for subreddit in subreddits:
            subreddit_data = next((s for s in self.relevant_subreddits if s.name.lower() == subreddit.lower()), None)
            if subreddit_data:
                schedule[subreddit] = {
                    "optimal_times": subreddit_data.optimal_post_times,
                    "frequency": "once per month max",
                    "best_days": ["Tuesday", "Wednesday", "Thursday"],
                    "avoid_days": ["Monday", "Friday", "Weekend"]
                }
        
        return schedule
    
    def track_post_performance(self, post: RedditPost, metrics: Dict[str, Any]) -> None:
        """Track performance of Reddit posts for optimization."""
        performance_data = {
            "post": post,
            "metrics": metrics,
            "timestamp": datetime.now(),
            "subreddit_analysis": self.analyze_subreddit_fit(post.subreddit, ContentType.ANNOUNCEMENT)
        }
        
        self.posting_history.append(performance_data)
        
        # Log insights
        logger.info(f"Post performance tracked for {post.subreddit}: {metrics}")


class RedditAnalyzeCommand(ContentCommand):
    """Command to analyze subreddit compatibility."""
    
    def _setup_command(self) -> None:
        self.metadata = CommandMetadata(
            name="reddit-analyze",
            description="Analyze subreddit compatibility for your content",
            category=CommandCategory.SOCIAL,
            examples=[
                "aetherpost reddit analyze --subreddit r/programming",
                "aetherpost reddit analyze --content-type educational"
            ],
            requires_config=True
        )
        
        self.options.extend([
            CommandOption(
                name="subreddit",
                short_name="s",
                help_text="Target subreddit to analyze"
            ),
            CommandOption(
                name="app-name",
                help_text="Name of your app",
                default="AetherPost"
            )
        ])
    
    @handle_errors
    def execute(self, **kwargs) -> OperationResult:
        """Execute reddit analysis command."""
        subreddit = kwargs.get('subreddit')
        content_type = kwargs.get('content_type', 'announcement')
        app_name = kwargs.get('app_name', 'AetherPost')
        
        manager = RedditEnhancedManager()
        
        if subreddit:
            # Analyze specific subreddit
            analysis = manager.analyze_subreddit_fit(subreddit, ContentType(content_type))
            
            result_text = (
                f"[bold green]Subreddit Analysis: {subreddit}[/bold green]\n\n"
                f"Fit Score: [bold yellow]{analysis['fit_score']:.1f}/1.0[/bold yellow]\n\n"
                f"[bold]Recommendations:[/bold]\n" + 
                "\n".join(f"• {rec}" for rec in analysis['recommendations']) +
                f"\n\n[bold]Optimal Posting Times:[/bold]\n" +
                ", ".join(analysis['optimal_times']) +
                f"\n\n[bold]Content Preferences:[/bold]\n" +
                "\n".join(f"• {pref}" for pref in analysis['content_preferences'])
            )
            
            self.console.print(Panel(result_text, title="Reddit Analysis"))
            
            return OperationResult.success_result(
                f"Analysis completed for {subreddit}",
                data=analysis
            )
        else:
            # Show all relevant subreddits
            table = self.create_table("Reddit Subreddit Analysis", [
                "Subreddit", "Members", "Moderation", "Fit Score"
            ])
            
            results = []
            for subreddit_data in manager.relevant_subreddits:
                analysis = manager.analyze_subreddit_fit(subreddit_data.name, ContentType(content_type))
                table.add_row(
                    subreddit_data.name,
                    f"{subreddit_data.members:,}",
                    subreddit_data.moderation_level,
                    f"{analysis['fit_score']:.1f}"
                )
                results.append({
                    "subreddit": subreddit_data.name,
                    "members": subreddit_data.members,
                    "fit_score": analysis['fit_score']
                })
            
            self.console.print(table)
            
            return OperationResult.success_result(
                f"Analyzed {len(results)} subreddits",
                data=results
            )


class RedditGenerateCommand(ContentCommand):
    """Command to generate subreddit-optimized content."""
    
    def _setup_command(self) -> None:
        self.metadata = CommandMetadata(
            name="reddit-generate",
            description="Generate subreddit-optimized content",
            category=CommandCategory.CONTENT,
            examples=[
                "aetherpost reddit generate --subreddit r/programming",
                "aetherpost reddit generate -s r/devtools --preview"
            ],
            requires_config=True
        )
        
        self.options.extend([
            CommandOption(
                name="subreddit",
                short_name="s",
                help_text="Target subreddit",
                required=True
            ),
            CommandOption(
                name="app-name",
                help_text="Name of your app",
                default="AetherPost"
            ),
            CommandOption(
                name="description",
                help_text="App description"
            ),
            CommandOption(
                name="github-url",
                help_text="GitHub repository URL"
            ),
            CommandOption(
                name="preview",
                help_text="Preview content without posting",
                option_type=bool,
                default=False
            )
        ])
    
    @handle_errors
    def execute(self, **kwargs) -> OperationResult:
        """Execute reddit content generation command."""
        subreddit = kwargs.get('subreddit')
        app_name = kwargs.get('app_name', 'AetherPost')
        description = kwargs.get('description')
        github_url = kwargs.get('github_url')
        preview = kwargs.get('preview', False)
        
        manager = RedditEnhancedManager()
        
        context = {
            "app_name": app_name,
            "description": description or f"{app_name} automates your social media posting across multiple platforms",
            "github_url": github_url,
            "technical_stack": "Python, FastAPI, React, AWS",
            "development_story": f"Built {app_name} to solve my own social media automation needs"
        }
        
        try:
            post = manager.generate_subreddit_specific_content(subreddit, context)
            
            result_text = (
                f"[bold green]Title:[/bold green]\n{post.title}\n\n"
                f"[bold green]Content:[/bold green]\n{post.content}"
            )
            
            self.console.print(Panel(
                result_text,
                title=f"Generated Content for {subreddit}"
            ))
            
            if preview:
                self.print_info("Content generated in preview mode - not posted")
            else:
                self.print_warning("Use --preview flag to preview without posting")
            
            return OperationResult.success_result(
                f"Content generated for {subreddit}",
                data={"post": post, "preview": preview}
            )
            
        except ValueError as e:
            return OperationResult.error_result(
                f"Error generating content: {e}",
                errors=[str(e)]
            )


class RedditScheduleCommand(ContentCommand):
    """Command to get optimal posting schedule."""
    
    def _setup_command(self) -> None:
        self.metadata = CommandMetadata(
            name="reddit-schedule",
            description="Get optimal posting schedule for multiple subreddits",
            category=CommandCategory.AUTOMATION,
            examples=[
                "aetherpost reddit schedule",
                "aetherpost reddit schedule --subreddits r/programming,r/webdev"
            ]
        )
        
        self.options.extend([
            CommandOption(
                name="subreddits",
                short_name="s",
                help_text="Target subreddits (comma-separated)",
                multiple=True
            )
        ])
    
    @handle_errors
    def execute(self, **kwargs) -> OperationResult:
        """Execute reddit schedule command."""
        subreddits = kwargs.get('subreddits', [])
        
        manager = RedditEnhancedManager()
        
        if not subreddits:
            subreddits = [s.name for s in manager.relevant_subreddits[:5]]  # Top 5 by default
        
        schedule_data = manager.suggest_posting_schedule(list(subreddits))
        
        table = self.create_table("Reddit Posting Schedule", [
            "Subreddit", "Optimal Times", "Best Days", "Frequency"
        ])
        
        for subreddit, data in schedule_data.items():
            table.add_row(
                subreddit,
                ", ".join(data["optimal_times"]),
                ", ".join(data["best_days"]),
                data["frequency"]
            )
        
        self.console.print(table)
        
        return OperationResult.success_result(
            f"Schedule generated for {len(schedule_data)} subreddits",
            data=schedule_data
        )


class RedditListCommand(ContentCommand):
    """Command to list relevant subreddits."""
    
    def _setup_command(self) -> None:
        self.metadata = CommandMetadata(
            name="reddit-list",
            description="List all relevant subreddits for app promotion",
            category=CommandCategory.UTILITIES,
            examples=["aetherpost reddit list"]
        )
    
    @handle_errors
    def execute(self, **kwargs) -> OperationResult:
        """Execute reddit list command."""
        manager = RedditEnhancedManager()
        
        table = self.create_table("Relevant Subreddits", [
            "Subreddit", "Members", "Description", "Moderation"
        ])
        
        for subreddit_data in manager.relevant_subreddits:
            description = subreddit_data.description
            if len(description) > 50:
                description = description[:50] + "..."
            
            table.add_row(
                subreddit_data.name,
                f"{subreddit_data.members:,}",
                description,
                subreddit_data.moderation_level
            )
        
        self.console.print(table)
        self.print_success(f"Total relevant subreddits: {len(manager.relevant_subreddits)}")
        
        return OperationResult.success_result(
            f"Listed {len(manager.relevant_subreddits)} subreddits",
            data=[{
                "name": s.name,
                "members": s.members,
                "description": s.description,
                "moderation_level": s.moderation_level
            } for s in manager.relevant_subreddits]
        )

# Create Click commands from the command classes
reddit_analyze_cmd = create_click_command(RedditAnalyzeCommand)
reddit_generate_cmd = create_click_command(RedditGenerateCommand)
reddit_schedule_cmd = create_click_command(RedditScheduleCommand)
reddit_list_cmd = create_click_command(RedditListCommand)

# Create command group
@click.group(name="reddit")
@click.pass_context
def reddit_enhanced(ctx):
    """Enhanced Reddit automation and community engagement."""
    ctx.ensure_object(dict)

# Add commands to group
reddit_enhanced.add_command(reddit_analyze_cmd, name="analyze")
reddit_enhanced.add_command(reddit_generate_cmd, name="generate")
reddit_enhanced.add_command(reddit_schedule_cmd, name="schedule")
reddit_enhanced.add_command(reddit_list_cmd, name="list")

if __name__ == "__main__":
    reddit_enhanced()