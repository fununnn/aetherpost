"""Optimized AetherPost initialization command using the new framework."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import yaml
import json

from aetherpost.cli.framework.command_factory import AetherPostCommand, CommandConfig, ExecutionContext
from aetherpost.cli.framework.response_formatter import ResponseFormatter, FormatterConfig, OutputFormat
from aetherpost.cli.common.base_command import CommandMetadata, CommandCategory, CommandOption
from aetherpost.core.common.base_models import Platform, OperationResult
from aetherpost.core.config.validation_engine import create_autopromo_config_validator
from aetherpost.core.common.config_manager import AetherPostConfig, PlatformCredentials, AIProviderConfig
from aetherpost.core.common.utils import safe_filename
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)


@dataclass
class InitializationTemplate:
    """Template for AetherPost initialization."""
    name: str
    description: str
    target_audience: str
    platforms: List[Platform]
    ai_services: List[str]
    features: Dict[str, bool]
    estimated_cost: str
    complexity: str  # "beginner", "intermediate", "advanced"


@dataclass
class ProjectProfile:
    """User project profile for customized setup."""
    project_type: str
    team_size: str
    budget_range: str
    technical_level: str
    primary_goals: List[str]
    time_investment: str


class AetherPostInitCommand(AetherPostCommand):
    """Enhanced AetherPost initialization command with intelligent recommendations."""
    
    def __init__(self, config: CommandConfig):
        super().__init__(config)
        self.templates = self._load_optimized_templates()
        self.console = Console()
    
    def get_metadata(self) -> CommandMetadata:
        return CommandMetadata(
            name="init",
            description="Initialize AetherPost workspace with intelligent recommendations",
            category=CommandCategory.CORE,
            examples=[
                "aetherpost init",
                "aetherpost init --quick",
                "aetherpost init --template startup",
                "aetherpost init --interactive"
            ]
        )
    
    def get_options(self) -> List[CommandOption]:
        return [
            CommandOption(
                name="name",
                help_text="Project name",
                default=None
            ),
            CommandOption(
                name="quick",
                short_name="q",
                help_text="Quick setup with smart defaults",
                option_type=bool,
                default=False
            ),
            CommandOption(
                name="template",
                short_name="t",
                help_text="Initialization template",
                choices=list(self.templates.keys()),
                default="minimal"
            ),
            CommandOption(
                name="interactive",
                short_name="i",
                help_text="Interactive guided setup",
                option_type=bool,
                default=False
            ),
            CommandOption(
                name="example",
                help_text="Show configuration examples",
                option_type=bool,
                default=False
            )
        ]
    
    async def execute_core_logic(self, context: ExecutionContext) -> OperationResult:
        """Execute enhanced initialization with intelligent recommendations."""
        
        if context.user_input.get('example'):
            self._show_examples()
            return OperationResult.success_result("Examples displayed")
        
        # Show welcome banner
        self._show_welcome_banner()
        
        # Check existing workspace
        autopromo_dir = Path(".aetherpost")
        if autopromo_dir.exists() and not context.user_input.get('force'):
            if not Confirm.ask("AetherPost workspace already exists. Reconfigure?"):
                return OperationResult.success_result("Workspace already configured")
        
        # Determine initialization approach
        if context.user_input.get('quick'):
            result = await self._quick_initialization(context)
        elif context.user_input.get('interactive'):
            result = await self._interactive_initialization(context)
        else:
            result = await self._smart_initialization(context)
        
        return result
    
    def _load_optimized_templates(self) -> Dict[str, InitializationTemplate]:
        """Load optimized templates based on current app capabilities."""
        return {
            "minimal": InitializationTemplate(
                name="Minimal Setup",
                description="Quick start with Twitter and basic AI content generation",
                target_audience="New users, testing, learning the tool",
                platforms=[Platform.TWITTER],
                ai_services=["openai"],
                features={
                    "content_generation": True,
                    "basic_posting": True
                },
                estimated_cost="$5-20/month (OpenAI API usage)",
                complexity="beginner"
            ),
            "social_media": InitializationTemplate(
                name="Social Media",
                description="Twitter, Bluesky, and Mastodon for broad reach",
                target_audience="Content creators, personal brands, small businesses",
                platforms=[Platform.TWITTER, Platform.BLUESKY, Platform.MASTODON],
                ai_services=["openai"],
                features={
                    "content_generation": True,
                    "cross_platform_posting": True,
                    "basic_analytics": True
                },
                estimated_cost="$15-40/month",
                complexity="beginner"
            ),
            "technical": InitializationTemplate(
                name="Technical Content",
                description="Twitter and Reddit optimized for developer content",
                target_audience="Developers, DevRel teams, technical writers",
                platforms=[Platform.TWITTER, Platform.REDDIT],
                ai_services=["openai"],
                features={
                    "content_generation": True,
                    "reddit_optimization": True,
                    "subreddit_analysis": True,
                    "technical_tone": True,
                    "hackernews_trends": True
                },
                estimated_cost="$20-50/month",
                complexity="intermediate"
            ),
            "full_platform": InitializationTemplate(
                name="All Platforms",
                description="All supported platforms including Reddit and YouTube",
                target_audience="Power users, agencies, comprehensive automation",
                platforms=[Platform.TWITTER, Platform.BLUESKY, Platform.MASTODON, Platform.REDDIT, Platform.YOUTUBE],
                ai_services=["openai"],
                features={
                    "content_generation": True,
                    "reddit_optimization": True,
                    "youtube_support": True,
                    "cross_platform_posting": True,
                    "basic_analytics": True
                },
                estimated_cost="$30-80/month",
                complexity="advanced"
            )
        }
    
    def _show_welcome_banner(self):
        """Show enhanced welcome banner."""
        self.console.print(Panel(
            "[bold blue]🚀 AetherPost v2.0 Initialization[/bold blue]\\n\\n"
            "[dim]Social Media Automation Framework[/dim]\\n\\n"
            "✨ Current Features:\\n"
            "• 🧠 AI-powered content generation (OpenAI)\\n"
            "• 🐦 Twitter/X posting with hashtag support\\n"
            "• 🌀 Bluesky AT Protocol integration\\n"
            "• 🐘 Mastodon federated posting\\n"
            "• 📊 Reddit community analysis\\n"
            "• 📈 HackerNews trend monitoring\\n\\n"
            "This setup will configure:\\n"
            "• Platform integrations & API credentials\\n"
            "• AI services for content generation\\n"
            "• Basic analytics and insights\\n"
            "• Local workspace and project structure",
            title="AetherPost v2.0 Setup",
            border_style="blue"
        ))
    
    async def _smart_initialization(self, context: ExecutionContext) -> OperationResult:
        """Smart initialization with project profiling."""
        self.console.print("\\n[bold blue]🧠 Smart Setup - AI-Powered Recommendations[/bold blue]")
        
        # Project profiling
        profile = self._gather_project_profile()
        
        # Get intelligent recommendations
        recommended_template = self._get_smart_recommendations(profile)
        
        self.console.print(f"\\n[bold green]✨ Recommended Setup: {recommended_template.name}[/bold green]")
        self.console.print(f"[dim]{recommended_template.description}[/dim]")
        
        # Show recommendation reasoning
        self._show_recommendation_reasoning(profile, recommended_template)
        
        if Confirm.ask("Use this recommended configuration?", default=True):
            return await self._create_workspace_from_template(
                context, recommended_template, profile
            )
        else:
            return await self._interactive_initialization(context)
    
    async def _interactive_initialization(self, context: ExecutionContext) -> OperationResult:
        """Interactive guided initialization."""
        self.console.print("\\n[bold blue]🎯 Interactive Setup - Guided Configuration[/bold blue]")
        
        # Show all templates with enhanced information
        self._show_template_comparison()
        
        # Template selection
        template_names = list(self.templates.keys())
        template_choice = Prompt.ask(
            "Choose your setup template",
            choices=template_names,
            default="social_media"
        )
        
        selected_template = self.templates[template_choice]
        
        # Customize template
        customized_template = self._customize_template(selected_template)
        
        # Project profile for context
        profile = ProjectProfile(
            project_type="custom",
            team_size="unknown",
            budget_range="flexible",
            technical_level="intermediate",
            primary_goals=["engagement"],
            time_investment="moderate"
        )
        
        return await self._create_workspace_from_template(
            context, customized_template, profile
        )
    
    async def _quick_initialization(self, context: ExecutionContext) -> OperationResult:
        """Quick initialization with smart defaults."""
        self.console.print("\\n[bold blue]⚡ Quick Setup - Smart Defaults[/bold blue]")
        
        # Use minimal template for quick setup
        template = self.templates["minimal"]
        
        # Minimal project profile
        profile = ProjectProfile(
            project_type="personal",
            team_size="1-2",
            budget_range="low",
            technical_level="beginner",
            primary_goals=["content_creation"],
            time_investment="minimal"
        )
        
        project_name = context.user_input.get('name') or Path.cwd().name
        
        self.console.print(f"Setting up '{project_name}' with smart defaults...")
        
        return await self._create_workspace_from_template(context, template, profile)
    
    def _gather_project_profile(self) -> ProjectProfile:
        """Gather project information for smart recommendations."""
        self.console.print("\\n[bold]📋 Tell us about your project (5 quick questions):[/bold]")
        
        # Project type
        project_types = {
            "personal": "Personal brand or individual creator",
            "startup": "Startup or growing business",
            "enterprise": "Large company or organization", 
            "agency": "Marketing agency or service provider",
            "developer": "Developer tools or technical product",
            "nonprofit": "Non-profit or community organization"
        }
        
        self.console.print("\\n1. What type of project is this?")
        for key, desc in project_types.items():
            self.console.print(f"   {key}: {desc}")
        
        project_type = Prompt.ask(
            "Project type",
            choices=list(project_types.keys()),
            default="personal"
        )
        
        # Team size
        team_size = Prompt.ask(
            "\\n2. Team size",
            choices=["just-me", "2-5", "6-20", "20+"],
            default="just-me"
        )
        
        # Budget range
        budget_range = Prompt.ask(
            "\\n3. Monthly budget for social media automation",
            choices=["minimal (<$50)", "moderate ($50-200)", "substantial ($200-500)", "enterprise ($500+)"],
            default="moderate ($50-200)"
        )
        
        # Technical level
        technical_level = Prompt.ask(
            "\\n4. Technical expertise level",
            choices=["beginner", "intermediate", "advanced"],
            default="intermediate"
        )
        
        # Primary goals
        goal_options = ["brand_awareness", "lead_generation", "community_building", "content_distribution", "customer_support"]
        self.console.print("\\n5. Primary goals (select main focus):")
        for i, goal in enumerate(goal_options, 1):
            self.console.print(f"   {i}. {goal.replace('_', ' ').title()}")
        
        goal_choice = IntPrompt.ask("Select primary goal (1-5)", default=1)
        primary_goal = goal_options[goal_choice - 1] if 1 <= goal_choice <= 5 else goal_options[0]
        
        return ProjectProfile(
            project_type=project_type,
            team_size=team_size,
            budget_range=budget_range,
            technical_level=technical_level,
            primary_goals=[primary_goal],
            time_investment="moderate"
        )
    
    def _get_smart_recommendations(self, profile: ProjectProfile) -> InitializationTemplate:
        """Get intelligent template recommendations based on profile."""
        # Simple scoring algorithm for template selection
        scores = {}
        
        for template_name, template in self.templates.items():
            score = 0
            
            # Project type matching
            if profile.project_type == "personal" and template_name == "personal":
                score += 30
            elif profile.project_type == "startup" and template_name == "startup":
                score += 30
            elif profile.project_type == "enterprise" and template_name == "enterprise":
                score += 30
            elif profile.project_type == "developer" and template_name == "developer":
                score += 30
            elif profile.project_type == "agency" and template_name == "agency":
                score += 30
            
            # Budget matching
            if "minimal" in profile.budget_range and template.complexity == "beginner":
                score += 20
            elif "moderate" in profile.budget_range and template.complexity == "intermediate":
                score += 20
            elif "substantial" in profile.budget_range and template.complexity == "advanced":
                score += 20
            
            # Team size matching
            if profile.team_size == "just-me" and not template.features.get("team_collaboration", False):
                score += 15
            elif profile.team_size in ["2-5", "6-20"] and template.features.get("team_collaboration", False):
                score += 15
            
            # Technical level matching
            if (profile.technical_level == "beginner" and template.complexity == "beginner") or \
               (profile.technical_level == "intermediate" and template.complexity == "intermediate") or \
               (profile.technical_level == "advanced" and template.complexity == "advanced"):
                score += 10
            
            scores[template_name] = score
        
        # Return highest scoring template
        best_template_name = max(scores, key=scores.get)
        return self.templates[best_template_name]
    
    def _show_recommendation_reasoning(self, profile: ProjectProfile, template: InitializationTemplate):
        """Show why this template was recommended."""
        reasoning_table = Table(title="Why this recommendation?")
        reasoning_table.add_column("Factor", style="cyan")
        reasoning_table.add_column("Your Profile", style="white")
        reasoning_table.add_column("Template Match", style="green")
        
        reasoning_table.add_row(
            "Project Type",
            profile.project_type.replace('_', ' ').title(),
            template.target_audience
        )
        reasoning_table.add_row(
            "Complexity",
            profile.technical_level.title(),
            template.complexity.title()
        )
        reasoning_table.add_row(
            "Budget Range", 
            profile.budget_range,
            template.estimated_cost
        )
        reasoning_table.add_row(
            "Platforms",
            f"{len(template.platforms)} recommended",
            ", ".join([p.value for p in template.platforms[:3]]) + ("..." if len(template.platforms) > 3 else "")
        )
        
        self.console.print(reasoning_table)
    
    def _show_template_comparison(self):
        """Show enhanced template comparison."""
        comparison_table = Table(title="🎯 Available Setup Templates")
        comparison_table.add_column("Template", style="bold cyan")
        comparison_table.add_column("Best For", style="white")
        comparison_table.add_column("Platforms", style="yellow")
        comparison_table.add_column("Cost", style="green")
        comparison_table.add_column("Complexity", style="magenta")
        
        for name, template in self.templates.items():
            platform_list = ", ".join([p.value for p in template.platforms[:2]])
            if len(template.platforms) > 2:
                platform_list += f" +{len(template.platforms) - 2} more"
            
            comparison_table.add_row(
                name.title(),
                template.target_audience[:40] + "..." if len(template.target_audience) > 40 else template.target_audience,
                platform_list,
                template.estimated_cost,
                template.complexity.title()
            )
        
        self.console.print(comparison_table)
    
    def _customize_template(self, template: InitializationTemplate) -> InitializationTemplate:
        """Allow user to customize selected template."""
        self.console.print(f"\\n[bold]🎨 Customizing {template.name}[/bold]")
        
        # Platform selection - only show working platforms
        working_platforms = [
            Platform.TWITTER, Platform.BLUESKY, Platform.MASTODON, 
            Platform.REDDIT, Platform.YOUTUBE
        ]
        selected_platforms = list(template.platforms)  # Start with template defaults
        
        if Confirm.ask("Customize platform selection?", default=False):
            self.console.print("\\nSelect platforms to enable:")
            self.console.print("[dim]Note: Only fully tested platforms are shown[/dim]")
            selected_platforms = []
            
            for platform in working_platforms:
                default = platform in template.platforms
                status = "✅ Fully supported" if platform in [Platform.TWITTER, Platform.BLUESKY, Platform.MASTODON, Platform.REDDIT] else "⚠️  Basic support"
                if Confirm.ask(f"Enable {platform.value}? ({status})", default=default):
                    selected_platforms.append(platform)
        
        # AI services - only show working ones
        ai_services = list(template.ai_services)
        if Confirm.ask("Customize AI services?", default=False):
            available_ai = ["openai"]  # Only OpenAI is fully implemented
            ai_services = []
            
            for service in available_ai:
                default = service in template.ai_services
                if Confirm.ask(f"Enable {service}? (✅ Fully supported)", default=default):
                    ai_services.append(service)
        
        # Create customized template
        customized = InitializationTemplate(
            name=f"Custom {template.name}",
            description=template.description,
            target_audience=template.target_audience,
            platforms=selected_platforms,
            ai_services=ai_services,
            features=template.features.copy(),
            estimated_cost=template.estimated_cost,
            complexity=template.complexity
        )
        
        return customized
    
    async def _create_workspace_from_template(self, context: ExecutionContext, 
                                            template: InitializationTemplate,
                                            profile: ProjectProfile) -> OperationResult:
        """Create workspace from template configuration."""
        
        project_name = context.user_input.get('name') or Prompt.ask(
            "Project name", 
            default=safe_filename(Path.cwd().name)
        )
        
        # Create directory structure
        autopromo_dir = Path(".aetherpost")
        autopromo_dir.mkdir(exist_ok=True)
        
        # Generate configuration
        config = self._generate_config(project_name, template, profile)
        
        # Validate configuration
        validator = create_autopromo_config_validator()
        validation_result = validator.validate(config.to_dict())
        
        if not validation_result.is_valid:
            self.console.print("\\n⚠️ [yellow]Configuration validation warnings:[/yellow]")
            for issue in validation_result.issues:
                self.console.print(f"   • {issue.message}")
        
        # Save configuration files
        await self._save_workspace_files(autopromo_dir, config, template, profile)
        
        # Show success and next steps
        self._show_success_message(project_name, template)
        
        return OperationResult.success_result(
            f"AetherPost workspace '{project_name}' initialized successfully",
            data={
                "project_name": project_name,
                "template": template.name,
                "platforms": [p.value for p in template.platforms],
                "ai_services": template.ai_services,
                "config_path": str(autopromo_dir)
            }
        )
    
    def _generate_config(self, project_name: str, template: InitializationTemplate, 
                        profile: ProjectProfile) -> AetherPostConfig:
        """Generate AetherPost configuration from template."""
        config = AetherPostConfig(
            app_name=project_name,
            description=f"Social media automation for {project_name}",
            author="AetherPost User",
            company=project_name if profile.project_type != "personal" else None
        )
        
        # Configure platforms
        for platform in template.platforms:
            creds = PlatformCredentials(
                platform=platform,
                # Placeholder credentials - user needs to fill these
                api_key="your_api_key_here",
                api_secret="your_api_secret_here" if platform == Platform.TWITTER else None
            )
            config.set_platform_credentials(creds)
        
        # Configure AI services
        if template.ai_services:
            primary_ai = template.ai_services[0]
            config.ai = AIProviderConfig(
                provider=primary_ai,
                api_key="your_ai_api_key_here",
                model="gpt-4" if primary_ai == "openai" else "ai-model-v3",
                temperature=0.7,
                max_tokens=1000
            )
        
        # Configure features
        config.features.update(template.features)
        
        # Configure defaults based on profile
        config.defaults.update({
            "posting_style": "professional" if profile.project_type in ["enterprise", "agency"] else "friendly",
            "auto_hashtags": True,
            "optimal_timing": True,
            "content_validation": True
        })
        
        return config
    
    async def _save_workspace_files(self, autopromo_dir: Path, config: AetherPostConfig,
                                  template: InitializationTemplate, profile: ProjectProfile):
        """Save all workspace configuration files."""
        
        # Main configuration
        config_file = autopromo_dir / "config.yaml"
        config_data = config.to_dict()
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        # Environment template
        env_template = self._generate_env_template(template.platforms, template.ai_services)
        with open(autopromo_dir / ".env.template", 'w') as f:
            f.write(env_template)
        
        # Project metadata
        metadata = {
            "created_at": datetime.now().isoformat(),
            "template": template.name,
            "profile": {
                "project_type": profile.project_type,
                "team_size": profile.team_size,
                "technical_level": profile.technical_level
            },
            "version": "2.0",
            "last_updated": datetime.now().isoformat()
        }
        
        with open(autopromo_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create .gitignore
        gitignore_content = '''# AetherPost Configuration
.aetherpost/.env
.aetherpost/credentials.yaml
.aetherpost/state/
.aetherpost/logs/
.aetherpost/content_cache/
*.log

# API Keys and Secrets
.env.aetherpost
credentials.json
secrets.yaml
youtube_credentials.json
youtube_token.json

# Cache and temporary files
__pycache__/
*.pyc
.cache/
.pytest_cache/

# Generated content
generated/
content_output/
media_cache/

# State files
promo.state.json
campaign.state

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
'''
        
        with open(".gitignore", 'w') as f:
            f.write(gitignore_content)
    
    def _generate_env_template(self, platforms: List[Platform], ai_services: List[str]) -> str:
        """Generate environment template with current platform requirements."""
        content = '''# AetherPost v2.0 Environment Configuration
# Copy this file to .env.aetherpost and add your actual API keys

# ===========================================
# CORE CONFIGURATION
# ===========================================
AUTOPROMO_ENV=development
AUTOPROMO_LOG_LEVEL=INFO
AUTOPROMO_DEBUG=false

# ===========================================
# PLATFORM CREDENTIALS
# ===========================================

'''
        
        platform_templates = {
            Platform.TWITTER: '''# TWITTER/X API v2 (Fully Supported)
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

''',
            Platform.BLUESKY: '''# BLUESKY AT PROTOCOL (Fully Supported)
BLUESKY_IDENTIFIER=your_username_or_email_here
BLUESKY_PASSWORD=your_app_password_here
BLUESKY_BASE_URL=https://bsky.social

''',
            Platform.MASTODON: '''# MASTODON (Fully Supported)
MASTODON_INSTANCE_URL=https://your-instance.social
MASTODON_ACCESS_TOKEN=your_access_token_here

''',
            Platform.REDDIT: '''# REDDIT API (Fully Supported)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_username_here
REDDIT_PASSWORD=your_password_here
REDDIT_USER_AGENT=AetherPost/1.0

''',
            Platform.YOUTUBE: '''# YOUTUBE DATA API v3 (Basic Support)
YOUTUBE_API_KEY=your_api_key_here
YOUTUBE_CLIENT_ID=your_client_id_here
YOUTUBE_CLIENT_SECRET=your_client_secret_here
YOUTUBE_CREDENTIALS_FILE=youtube_credentials.json
YOUTUBE_TOKEN_FILE=youtube_token.json

''',
            Platform.INSTAGRAM: '''# INSTAGRAM (Basic Support - Manual configuration required)
INSTAGRAM_APP_ID=your_app_id_here
INSTAGRAM_APP_SECRET=your_app_secret_here
INSTAGRAM_ACCESS_TOKEN=your_access_token_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_business_account_id_here

''',
            Platform.TIKTOK: '''# TIKTOK (Basic Support - Manual configuration required)
TIKTOK_ACCESS_TOKEN=your_access_token_here
TIKTOK_APP_ID=your_app_id_here
TIKTOK_APP_SECRET=your_app_secret_here

'''
        }
        
        for platform in platforms:
            if platform in platform_templates:
                content += platform_templates[platform]
        
        content += '''
# ===========================================
# AI SERVICES
# ===========================================

'''
        
        ai_templates = {
            "openai": "# OPENAI (Fully Supported)\\nOPENAI_API_KEY=your_openai_api_key_here\\nOPENAI_MODEL=gpt-4\\nOPENAI_TEMPERATURE=0.7\\nOPENAI_MAX_TOKENS=1000\\n\\n"
        }
        
        for service in ai_services:
            if service in ai_templates:
                content += ai_templates[service]
        
        content += '''
# ===========================================
# OPTIONAL SERVICES
# ===========================================

# Analytics (optional)
ANALYTICS_ENABLED=true

# Caching (optional)
REDIS_URL=redis://localhost:6379

# Database (optional - for advanced features)
DATABASE_URL=sqlite:///autopromo.db

# Monitoring (optional)
SENTRY_DSN=your_sentry_dsn_here
'''
        
        return content
    
    def _show_success_message(self, project_name: str, template: InitializationTemplate):
        """Show success message with next steps."""
        self.console.print(Panel(
            f"[bold green]🎉 {project_name} initialized successfully![/bold green]\\n\\n"
            f"Template: [cyan]{template.name}[/cyan]\\n"
            f"Platforms: [yellow]{len(template.platforms)}[/yellow] configured\\n"
            f"AI Services: [magenta]{len(template.ai_services)}[/magenta] configured\\n\\n"
            "[bold]Next Steps:[/bold]\\n"
            "1️⃣  Copy [cyan].aetherpost/.env.template[/cyan] to [cyan].env.aetherpost[/cyan]\\n"
            "2️⃣  Add your API keys to [cyan].env.aetherpost[/cyan]\\n"
            "3️⃣  Test setup: [cyan]aetherpost doctor[/cyan]\\n"
            "4️⃣  Try Reddit analysis: [cyan]aetherpost hackernews analyze[/cyan]\\n"
            "5️⃣  Generate content: [cyan]aetherpost ai generate --text 'Your content idea'[/cyan]",
            title="Setup Complete",
            border_style="green"
        ))
        
        # Show platform-specific quick start examples
        if Platform.TWITTER in template.platforms:
            self.console.print(f"\\n💡 [dim]Quick start: aetherpost ai generate --text 'My new project launch' --platform twitter[/dim]")
        elif Platform.REDDIT in template.platforms:
            self.console.print(f"\\n💡 [dim]Quick start: aetherpost hackernews analyze --days 7[/dim]")
        else:
            self.console.print(f"\\n💡 [dim]Quick start: aetherpost ai generate --text 'Hello world!'[/dim]")
    
    def _show_examples(self):
        """Show configuration examples for the new framework."""
        self.console.print(Panel(
            """[bold]AetherPost v2.0 Initialization Examples[/bold]

[cyan]🚀 Smart Setup (Recommended):[/cyan]
   aetherpost init
   # AI-powered recommendations based on your project

[cyan]⚡ Quick Minimal Setup:[/cyan]
   aetherpost init --quick --template minimal
   # Basic Twitter + OpenAI setup for testing

[cyan]🌐 Multi-Platform Setup:[/cyan]
   aetherpost init --template multi_platform --interactive
   # Twitter, Bluesky, Mastodon, and Reddit

[cyan]👨‍💻 Technical Content Setup:[/cyan]
   aetherpost init --template technical
   # Optimized for developers and technical teams

[cyan]📱 Personal Brand Setup:[/cyan]
   aetherpost init --template personal
   # Twitter, Bluesky, and Mastodon for personal branding

[yellow]After initialization:[/yellow]
   • Run [cyan]aetherpost doctor[/cyan] to check system health
   • Try [cyan]aetherpost hackernews analyze[/cyan] for trending topics
   • Generate content with [cyan]aetherpost ai generate[/cyan]
   • Test platforms with [cyan]aetherpost ai test[/cyan]""",
            title="📚 Setup Examples",
            border_style="green"
        ))


def register_init_command():
    """Register the enhanced init command."""
    from aetherpost.cli.framework.command_factory import command_factory, CommandConfig
    
    config = CommandConfig(
        requires_config=False,
        requires_auth=False,
        supports_dry_run=False,
        supports_output_format=False,
        log_execution=True
    )
    
    return command_factory.create_command(AetherPostInitCommand, config)