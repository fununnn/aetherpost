"""Refactored Reddit commands using the new framework."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from aetherpost.core.common.base_models import Platform, ContentType, OperationResult
from aetherpost.cli.framework.command_factory import (
    AetherPostCommand, CommandConfig, ExecutionContext, command_factory
)
from aetherpost.cli.framework.response_formatter import (
    ResponseFormatter, FormatterConfig, OutputFormat, format_data_as_table
)
from aetherpost.cli.common.base_command import CommandMetadata, CommandCategory, CommandOption
from aetherpost.core.services.container import container, inject
from aetherpost.core.services.platform_service import PlatformServiceProtocol

# Import existing Reddit manager (keeping business logic)
from aetherpost.cli.commands.reddit_enhanced import RedditEnhancedManager


logger = logging.getLogger(__name__)


@dataclass
class RedditCommandOptions:
    """Standardized options for Reddit commands."""
    subreddit: Optional[str] = None
    content_type: str = "announcement"
    app_name: str = "AetherPost"
    description: Optional[str] = None
    github_url: Optional[str] = None
    preview: bool = False
    subreddits: List[str] = None


class RedditAnalyzeCommand(AetherPostCommand):
    """Analyze subreddit compatibility using new framework."""
    
    def __init__(self, config: CommandConfig):
        super().__init__(config)
        self.reddit_manager = RedditEnhancedManager()
    
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="reddit-analyze",
            description="Analyze subreddit compatibility for your content",
            category=CommandCategory.SOCIAL,
            examples=[
                "aetherpost reddit analyze --subreddit r/programming",
                "aetherpost reddit analyze --content-type educational",
                "aetherpost reddit analyze --format json"
            ],
            requires_config=True
        )
    
    def get_options(self) -> List[CommandOption]:
        return [
            CommandOption(
                name="subreddit",
                short_name="s",
                help_text="Target subreddit to analyze"
            ),
            CommandOption(
                name="app-name",
                help_text="Name of your app",
                default="AetherPost"
            ),
            CommandOption(
                name="content-type",
                help_text="Type of content",
                choices=["announcement", "educational", "community"],
                default="announcement"
            )
        ]
    
    async def execute_core_logic(self, context: ExecutionContext) -> OperationResult:
        """Execute Reddit analysis with enhanced formatting."""
        options = self._parse_options(context.user_input)
        
        if options.subreddit:
            # Analyze specific subreddit
            analysis = self.reddit_manager.analyze_subreddit_fit(
                options.subreddit, 
                ContentType(options.content_type)
            )
            
            # Enhanced result formatting
            enhanced_analysis = {
                "subreddit": options.subreddit,
                "fit_score": analysis["fit_score"],
                "fit_percentage": f"{analysis['fit_score'] * 100:.1f}%",
                "recommendation_count": len(analysis["recommendations"]),
                "optimal_times": ", ".join(analysis["optimal_times"]),
                "content_preferences": analysis["content_preferences"]
            }
            
            # Use new formatter
            formatter = ResponseFormatter(context.console)
            config = FormatterConfig(
                format_type=OutputFormat(context.user_input.get('format', 'panel')),
                show_metadata=context.verbose
            )
            
            if context.user_input.get('format') == 'table':
                format_data_as_table([enhanced_analysis], f"Analysis: {options.subreddit}")
            else:
                context.console.print(f"\\n📊 **Analysis for {options.subreddit}**")
                context.console.print(f"Fit Score: {enhanced_analysis['fit_percentage']}")
                context.console.print(f"Recommendations: {enhanced_analysis['recommendation_count']}")
                context.console.print(f"Optimal Times: {enhanced_analysis['optimal_times']}")
            
            return OperationResult.success_result(
                f"Analysis completed for {options.subreddit}",
                data=enhanced_analysis,
                metadata={"analysis_type": "single_subreddit"}
            )
        else:
            # Analyze all subreddits
            results = []
            for subreddit_data in self.reddit_manager.relevant_subreddits:
                analysis = self.reddit_manager.analyze_subreddit_fit(
                    subreddit_data.name, 
                    ContentType(options.content_type)
                )
                
                results.append({
                    "subreddit": subreddit_data.name,
                    "members": f"{subreddit_data.members:,}",
                    "moderation": subreddit_data.moderation_level,
                    "fit_score": f"{analysis['fit_score']:.1f}",
                    "fit_percentage": f"{analysis['fit_score'] * 100:.1f}%"
                })
            
            # Sort by fit score
            results.sort(key=lambda x: float(x["fit_score"]), reverse=True)
            
            format_data_as_table(results, "Reddit Subreddit Compatibility Analysis")
            
            return OperationResult.success_result(
                f"Analyzed {len(results)} subreddits",
                data=results,
                metadata={
                    "analysis_type": "bulk_analysis",
                    "content_type": options.content_type,
                    "top_match": results[0]["subreddit"] if results else None
                }
            )
    
    def _parse_options(self, user_input: Dict[str, Any]) -> RedditCommandOptions:
        """Parse user input into structured options."""
        return RedditCommandOptions(
            subreddit=user_input.get('subreddit'),
            content_type=user_input.get('content_type', 'announcement'),
            app_name=user_input.get('app_name', 'AetherPost'),
            description=user_input.get('description'),
            github_url=user_input.get('github_url'),
            preview=user_input.get('preview', False)
        )


class RedditGenerateCommand(AetherPostCommand):
    """Generate subreddit-optimized content."""
    
    def __init__(self, config: CommandConfig):
        super().__init__(config)
        self.reddit_manager = RedditEnhancedManager()
    
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="reddit-generate",
            description="Generate subreddit-optimized content",
            category=CommandCategory.CONTENT,
            examples=[
                "aetherpost reddit generate --subreddit r/programming",
                "aetherpost reddit generate -s r/devtools --preview",
                "aetherpost reddit generate -s r/opensource --github-url https://github.com/user/repo"
            ],
            requires_config=True
        )
    
    def get_options(self) -> List[CommandOption]:
        return [
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
            )
        ]
    
    async def execute_core_logic(self, context: ExecutionContext) -> OperationResult:
        """Generate optimized content for subreddit."""
        options = self._parse_options(context.user_input)
        
        # Show dry-run message if applicable
        if self.handle_dry_run(context, f"generate content for {options.subreddit}"):
            return OperationResult.success_result(
                f"Would generate content for {options.subreddit}",
                data={"dry_run": True}
            )
        
        content_context = {
            "app_name": options.app_name,
            "description": options.description or f"{options.app_name} automates social media posting",
            "github_url": options.github_url,
            "technical_stack": "Python, FastAPI, React, AWS",
            "development_story": f"Built {options.app_name} to solve social media automation needs"
        }
        
        try:
            post = self.reddit_manager.generate_subreddit_specific_content(
                options.subreddit, 
                content_context
            )
            
            # Enhanced content presentation
            content_data = {
                "subreddit": options.subreddit,
                "title": post.title,
                "content": post.content,
                "word_count": len(post.content.split()),
                "character_count": len(post.content),
                "post_type": post.post_type
            }
            
            # Display with rich formatting
            context.console.print(f"\\n📝 **Generated Content for {options.subreddit}**")
            context.console.print(f"\\n**Title:** {post.title}")
            context.console.print(f"\\n**Content:**\\n{post.content}")
            context.console.print(f"\\n**Stats:** {content_data['word_count']} words, {content_data['character_count']} characters")
            
            if options.preview or context.dry_run:
                context.console.print("\\n[yellow]📋 Content generated in preview mode[/yellow]")
            
            return OperationResult.success_result(
                f"Content generated for {options.subreddit}",
                data=content_data,
                metadata={
                    "generation_method": "subreddit_optimized",
                    "preview_mode": options.preview or context.dry_run
                }
            )
            
        except ValueError as e:
            return OperationResult.error_result(
                f"Content generation failed: {e}",
                errors=[str(e)],
                metadata={"subreddit": options.subreddit}
            )
    
    def _parse_options(self, user_input: Dict[str, Any]) -> RedditCommandOptions:
        """Parse user input into structured options."""
        return RedditCommandOptions(
            subreddit=user_input.get('subreddit'),
            app_name=user_input.get('app_name', 'AetherPost'),
            description=user_input.get('description'),
            github_url=user_input.get('github_url'),
            preview=user_input.get('preview', False)
        )


class RedditScheduleCommand(AetherPostCommand):
    """Get optimal posting schedule for subreddits."""
    
    def __init__(self, config: CommandConfig):
        super().__init__(config)
        self.reddit_manager = RedditEnhancedManager()
    
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="reddit-schedule",
            description="Get optimal posting schedule for multiple subreddits",
            category=CommandCategory.AUTOMATION,
            examples=[
                "aetherpost reddit schedule",
                "aetherpost reddit schedule --subreddits r/programming,r/webdev",
                "aetherpost reddit schedule --format json"
            ]
        )
    
    def get_options(self) -> List[CommandOption]:
        return [
            CommandOption(
                name="subreddits",
                short_name="s",
                help_text="Target subreddits (comma-separated)",
                multiple=True
            )
        ]
    
    async def execute_core_logic(self, context: ExecutionContext) -> OperationResult:
        """Generate posting schedule with enhanced insights."""
        subreddits = context.user_input.get('subreddits', [])
        
        if not subreddits:
            # Use top 5 subreddits by default
            subreddits = [s.name for s in self.reddit_manager.relevant_subreddits[:5]]
        
        schedule_data = self.reddit_manager.suggest_posting_schedule(list(subreddits))
        
        # Enhanced schedule with additional insights
        enhanced_schedule = []
        for subreddit, data in schedule_data.items():
            # Find subreddit info for additional context
            subreddit_info = next(
                (s for s in self.reddit_manager.relevant_subreddits if s.name == subreddit),
                None
            )
            
            enhanced_schedule.append({
                "subreddit": subreddit,
                "optimal_times": ", ".join(data["optimal_times"]),
                "best_days": ", ".join(data["best_days"]),
                "frequency": data["frequency"],
                "members": f"{subreddit_info.members:,}" if subreddit_info else "Unknown",
                "moderation": subreddit_info.moderation_level if subreddit_info else "Unknown"
            })
        
        format_data_as_table(enhanced_schedule, "Reddit Posting Schedule")
        
        # Additional insights
        total_reach = sum(
            s.members for s in self.reddit_manager.relevant_subreddits 
            if s.name in subreddits
        )
        
        context.console.print(f"\\n📊 **Schedule Insights:**")
        context.console.print(f"Total potential reach: {total_reach:,} members")
        context.console.print(f"Recommended posting frequency: Once per month per subreddit")
        context.console.print(f"Best overall days: Tuesday, Wednesday, Thursday")
        
        return OperationResult.success_result(
            f"Schedule generated for {len(enhanced_schedule)} subreddits",
            data=enhanced_schedule,
            metadata={
                "total_subreddits": len(enhanced_schedule),
                "total_reach": total_reach,
                "schedule_type": "optimal_timing"
            }
        )


class RedditStatusCommand(AetherPostCommand):
    """Show Reddit automation status and statistics."""
    
    def __init__(self, config: CommandConfig):
        super().__init__(config)
        self.reddit_manager = RedditEnhancedManager()
    
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="reddit-status",
            description="Show Reddit automation status and statistics",
            category=CommandCategory.UTILITIES,
            examples=["aetherpost reddit status"]
        )
    
    def get_options(self) -> List[CommandOption]:
        return []
    
    async def execute_core_logic(self, context: ExecutionContext) -> OperationResult:
        """Show comprehensive Reddit status."""
        # Calculate statistics
        total_subreddits = len(self.reddit_manager.relevant_subreddits)
        total_members = sum(s.members for s in self.reddit_manager.relevant_subreddits)
        
        moderation_stats = {}
        for s in self.reddit_manager.relevant_subreddits:
            mod_level = s.moderation_level
            moderation_stats[mod_level] = moderation_stats.get(mod_level, 0) + 1
        
        # Recent activity (mock data - would come from actual tracking)
        recent_posts = len(self.reddit_manager.posting_history)
        
        status_data = {
            "Total Subreddits": total_subreddits,
            "Total Potential Reach": f"{total_members:,} members",
            "Strict Moderation": moderation_stats.get('strict', 0),
            "Moderate Moderation": moderation_stats.get('moderate', 0),
            "Relaxed Moderation": moderation_stats.get('relaxed', 0),
            "Recent Posts Tracked": recent_posts,
            "Status": "🟢 Active"
        }
        
        context.console.print("\\n📊 **Reddit Automation Status**\\n")
        
        for key, value in status_data.items():
            context.console.print(f"**{key}:** {value}")
        
        # Top subreddits by reach
        top_subreddits = sorted(
            self.reddit_manager.relevant_subreddits,
            key=lambda s: s.members,
            reverse=True
        )[:3]
        
        context.console.print("\\n**🎯 Top Subreddits by Reach:**")
        for i, subreddit in enumerate(top_subreddits, 1):
            context.console.print(f"{i}. {subreddit.name} - {subreddit.members:,} members")
        
        return OperationResult.success_result(
            "Reddit status retrieved",
            data=status_data,
            metadata={"status_type": "comprehensive", "timestamp": "now"}
        )


# Configure and register commands with the factory
def register_reddit_commands():
    """Register all Reddit commands with the command factory."""
    
    # Analyze command
    analyze_config = CommandConfig(
        requires_config=True,
        supports_output_format=True,
        supports_dry_run=False
    )
    analyze_cmd = command_factory.create_command(RedditAnalyzeCommand, analyze_config)
    
    # Generate command  
    generate_config = CommandConfig(
        requires_config=True,
        supports_dry_run=True,
        log_execution=True
    )
    generate_cmd = command_factory.create_command(RedditGenerateCommand, generate_config)
    
    # Schedule command
    schedule_config = CommandConfig(
        requires_config=False,
        supports_output_format=True,
        supports_dry_run=False
    )
    schedule_cmd = command_factory.create_command(RedditScheduleCommand, schedule_config)
    
    # Status command
    status_config = CommandConfig(
        requires_config=False,
        supports_output_format=True,
        cache_results=True
    )
    status_cmd = command_factory.create_command(RedditStatusCommand, status_config)
    
    return {
        "analyze": analyze_cmd,
        "generate": generate_cmd,
        "schedule": schedule_cmd,
        "status": status_cmd
    }