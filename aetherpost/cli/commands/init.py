"""Initialize command implementation - Terraform-style workflow."""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
import yaml
import json

console = Console()
init_app = typer.Typer()


@init_app.command()
def main(
    name: Optional[str] = typer.Argument(None, help="Project name"),
    quick: bool = typer.Option(False, "--quick/--interactive", "-q", help="Interactive setup with prompts (default: True)"),
    template: str = typer.Option("starter", "--template", "-t", 
                                help="Template type (starter, production, enterprise)"),
    example: bool = typer.Option(False, "--example", help="Show configuration examples"),
    backend: str = typer.Option("local", "--backend", "-b", 
                               help="Backend type (local, aws, cloud)"),
    upgrade: bool = typer.Option(False, "--upgrade", help="Upgrade existing configuration"),
):
    """Initialize AetherPost workspace - Interactive setup by default."""
    
    if example:
        show_examples()
        return
    
    # Welcome banner
    if quick:
        console.print("🚀 [bold blue]AetherPost Quick Setup[/bold blue] - Getting you started in 30 seconds!")
    else:
        console.print(Panel(
            "[bold blue]🚀 AetherPost Initialization[/bold blue]\n\n"
            "[dim]AI-powered social media automation[/dim]\n\n"
            "This will initialize your AetherPost workspace with:\n"
            "• Configuration files (.aetherpost/)\n"
            "• Platform connections\n"
            "• State management\n"
            "• Deployment backend",
            title="AetherPost Init",
            border_style="blue"
        ))
    
    # Check if already initialized
    autopromo_dir = Path(".aetherpost")
    config_file = autopromo_dir / "autopromo.yml"
    
    if config_file.exists() and not upgrade:
        if not Confirm.ask("AetherPost already initialized. Reconfigure?"):
            console.print("✅ AetherPost workspace already configured")
            return
    
    # Get or confirm project name
    if not name:
        name = Prompt.ask("Project name", default=Path.cwd().name)
    
    # Get project concept (always ask)
    concept = Prompt.ask("Project description/concept", default=f"Innovative {name} application")
    
    # Ask about free tier usage
    use_free_tier = Confirm.ask("Stay within free tier limits? (50 posts/day)", default=True)
    
    # Ask about content style
    console.print("\n[bold]🎨 Content Style:[/bold]")
    console.print("1) Casual 2) Professional 3) Technical 4) Humorous")
    style_choice = Prompt.ask("Select style (1-4)", default="1")
    style_map = {"1": "casual", "2": "professional", "3": "technical", "4": "humorous"}
    content_style = style_map.get(style_choice, "casual")
    
    # Template selection
    if not quick:
        console.print("\n[bold]📋 Select Template:[/bold]")
        templates = {
            "starter": "Basic setup - Perfect for personal projects",
            "production": "Production-ready - Multi-platform automation", 
            "enterprise": "Enterprise - Advanced features, monitoring, scaling"
        }
        
        table = Table()
        table.add_column("Template", style="cyan")
        table.add_column("Description", style="white")
        
        for tmpl, desc in templates.items():
            marker = "→" if tmpl == template else " "
            table.add_row(f"{marker} {tmpl}", desc)
        
        console.print(table)
        
        template = Prompt.ask("Choose template", 
                            choices=list(templates.keys()), 
                            default=template)
    
    # Platform configuration
    console.print(f"\n[bold]📱 Platform Configuration:[/bold]")
    
    available_platforms = {
        "twitter": {"name": "Twitter/X", "required": True, "cost": "Free tier + $100/month for high volume"},
        "instagram": {"name": "Instagram", "required": False, "cost": "Free (rate limited)"},
        "youtube": {"name": "YouTube", "required": False, "cost": "Free quota + $0.002/100 units"},
        "tiktok": {"name": "TikTok", "required": False, "cost": "Free tier + enterprise pricing"},
        "reddit": {"name": "Reddit", "required": False, "cost": "Free (60 req/min)"}
    }
    
    # Platform selection (simplified)
    console.print(f"\n[bold]📱 Platform Selection:[/bold]")
    console.print("Available: 1) Twitter/X 2) Reddit 3) YouTube 4) Bluesky 5) Instagram")
    platform_choice = Prompt.ask("Select platforms (1-5, comma separated)", default="1,2")
    
    platform_map = {
        "1": "twitter", "2": "reddit", "3": "youtube", 
        "4": "bluesky", "5": "instagram"
    }
    
    selected_platforms = []
    for choice in platform_choice.split(","):
        choice = choice.strip()
        if choice in platform_map:
            selected_platforms.append(platform_map[choice])
    
    if not selected_platforms:
        selected_platforms = ["twitter", "reddit"]  # Safe defaults
    
    # Language configuration
    console.print(f"\n[bold]🌍 Language Configuration:[/bold]")
    
    available_languages = {
        "en": "English",
        "ja": "Japanese (日本語)",
        "es": "Spanish (Español)", 
        "fr": "French (Français)",
        "de": "German (Deutsch)",
        "ko": "Korean (한국어)",
        "zh": "Chinese (中文)",
        "pt": "Portuguese (Português)",
        "ru": "Russian (Русский)",
        "ar": "Arabic (العربية)"
    }
    
    console.print("Popular: 1) English 2) Japanese 3) Spanish 4) French 5) German 6) Korean")
    lang_choice = Prompt.ask("Select language (1-6 or enter code like 'zh')", default="1")
    
    lang_map = {
        "1": "en", "2": "ja", "3": "es", 
        "4": "fr", "5": "de", "6": "ko"
    }
    
    content_language = lang_map.get(lang_choice, lang_choice if len(lang_choice) == 2 else "en")
    
    # AI Services configuration
    console.print(f"\n[bold]🤖 AI Services Configuration:[/bold]")
    
    ai_services = {
        "openai": {"name": "OpenAI GPT", "cost": "$0.002-0.06/1K tokens", "required": True},
        "elevenlabs": {"name": "ElevenLabs TTS", "cost": "$5-330/month", "required": False},
        "synthesia": {"name": "Synthesia Video", "cost": "$30-90/month", "required": False}
    }
    
    # AI Services (simplified - just use OpenAI)
    selected_ai = ["openai"]
    
    # Backend (simplified - use local for starter)
    backend = "local"  # Keep simple for beginners
    
    # Cost estimation
    estimated_cost = calculate_cost_estimate(template, selected_platforms, selected_ai, backend)
    
    console.print(f"\n[bold]💰 Cost Estimation:[/bold]")
    cost_table = Table()
    cost_table.add_column("Component", style="cyan")
    cost_table.add_column("Monthly Cost", style="green")
    
    for component, cost in estimated_cost.items():
        cost_table.add_row(component, cost)
    
    console.print(cost_table)
    
    # Confirm configuration
    if not quick:
        console.print(f"\n[bold]📋 Configuration Summary:[/bold]")
        summary_table = Table()
        summary_table.add_column("Setting", style="cyan")
        summary_table.add_column("Value", style="white")
        
        summary_table.add_row("Project Name", name)
        summary_table.add_row("Template", template)
        summary_table.add_row("Platforms", ", ".join(selected_platforms))
        summary_table.add_row("Content Language", f"{available_languages.get(content_language, content_language)} ({content_language})")
        summary_table.add_row("AI Services", ", ".join(selected_ai))
        summary_table.add_row("Backend", backend)
        summary_table.add_row("Est. Monthly Cost", estimated_cost.get("total", "$0-50"))
        
        console.print(summary_table)
        
        if not Confirm.ask("Proceed with this configuration?"):
            console.print("❌ Initialization cancelled")
            return
    
    # Create workspace
    create_workspace(name, template, selected_platforms, selected_ai, backend, autopromo_dir, content_language, concept, use_free_tier, content_style)
    
    # Next steps
    show_next_steps(name, selected_platforms)


def calculate_cost_estimate(template: str, platforms: List[str], ai_services: List[str], backend: str) -> dict:
    """Calculate estimated monthly costs."""
    costs = {}
    
    # Platform costs (simplified)
    platform_costs = {
        "twitter": "$0-100" if template == "starter" else "$100",
        "instagram": "$0",
        "youtube": "$5-20",
        "tiktok": "$0-50",
        "reddit": "$0"
    }
    
    for platform in platforms:
        if platform in platform_costs:
            costs[f"{platform.title()} API"] = platform_costs[platform]
    
    # AI service costs
    ai_costs = {
        "openai": "$10-50",
        "elevenlabs": "$5-30",
        "synthesia": "$30-90"
    }
    
    for service in ai_services:
        if service in ai_costs:
            costs[f"{service.title()} AI"] = ai_costs[service]
    
    # Backend costs
    backend_costs = {
        "local": "$0",
        "aws": "$5-20",
        "cloud": "$15-50"
    }
    costs["Infrastructure"] = backend_costs.get(backend, "$0")
    
    # Calculate total range
    if template == "starter":
        costs["total"] = "$0-50"
    elif template == "production":
        costs["total"] = "$50-300"
    else:  # enterprise
        costs["total"] = "$200-500"
    
    return costs


def create_workspace(name: str, template: str, platforms: List[str], ai_services: List[str], 
                    backend: str, autopromo_dir: Path, content_language: str = "en", concept: str = "", 
                    use_free_tier: bool = True, content_style: str = "casual"):
    """Create AetherPost workspace files."""
    
    # Create directory structure
    autopromo_dir.mkdir(exist_ok=True)
    
    # Main configuration file
    config = {
        "project": {
            "name": name,
            "version": "1.0.0",
            "template": template,
            "created": "2024-01-01T00:00:00Z"
        },
        "backend": {
            "type": backend,
            "config": get_backend_config(backend)
        },
        "platforms": {platform: get_platform_config(platform) for platform in platforms},
        "ai": {service: get_ai_config(service) for service in ai_services},
        "content": {
            "default_style": "professional" if template == "enterprise" else "casual",
            "max_length": 280,
            "hashtags": ["#AetherPost"],
            "language": content_language
        },
        "scheduling": {
            "timezone": "UTC",
            "default_delay": "5m",
            "retry_attempts": 3
        },
        "analytics": {
            "enabled": template != "starter",
            "retention_days": 90 if template == "enterprise" else 30
        }
    }
    
    # Write main config
    with open(autopromo_dir / "autopromo.yml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    # Create environment file template
    env_content = create_env_template(platforms, ai_services)
    with open(autopromo_dir / ".env.template", "w") as f:
        f.write(env_content)
    
    # Create platform-specific configs
    for platform in platforms:
        platform_config = get_detailed_platform_config(platform, template)
        with open(autopromo_dir / f"{platform}.yml", "w") as f:
            yaml.dump(platform_config, f, default_flow_style=False)
    
    # Create scripts directory
    scripts_dir = autopromo_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    # Create deployment script
    create_deployment_script(scripts_dir, backend, template)
    
    # Create .gitignore
    gitignore_content = """
# AetherPost
.aetherpost/.env
.aetherpost/state/
.aetherpost/logs/
*.log

# API Keys
.env.aetherpost
credentials.json

# Cache
__pycache__/
*.pyc
.cache/
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content.strip())
    
    # Create campaign.yaml
    campaign_yaml = {
        "name": name,
        "concept": concept or f"Innovative {name} application",
        "url": f"https://github.com/yourusername/{name}",
        "platforms": platforms,
        "content": {
            "style": content_style,
            "action": "Check it out!",
            "language": content_language,
            "hashtags": ["#OpenSource", "#DevTools"]
        },
        "limits": {
            "free_tier": use_free_tier,
            "max_posts_per_day": 50 if use_free_tier else 1000
        }
    }
    
    with open("campaign.yaml", "w") as f:
        yaml.dump(campaign_yaml, f, default_flow_style=False, sort_keys=False)
    
    console.print(f"\n✅ [green]AetherPost workspace initialized successfully![/green]")
    console.print(f"📁 Configuration created in: [cyan].aetherpost/[/cyan]")
    console.print(f"📝 Campaign template created: [cyan]campaign.yaml[/cyan]")
    
    # Don't auto-install dependencies - keep it simple


def get_backend_config(backend: str) -> dict:
    """Get backend-specific configuration."""
    configs = {
        "local": {
            "state_file": ".aetherpost/terraform.tfstate",
            "backup": True
        },
        "aws": {
            "bucket": "${PROJECT_NAME}-autopromo-state",
            "key": "autopromo.tfstate",
            "region": "us-east-1",
            "dynamodb_table": "${PROJECT_NAME}-autopromo-locks"
        },
        "cloud": {
            "organization": "your-org",
            "workspaces": {"name": "${PROJECT_NAME}"}
        }
    }
    return configs.get(backend, configs["local"])


def get_platform_config(platform: str) -> dict:
    """Get platform-specific configuration."""
    return {
        "enabled": True,
        "auth_required": True,
        "rate_limits": True,
        "features": get_platform_features(platform)
    }


def get_platform_features(platform: str) -> List[str]:
    """Get available features for platform."""
    features = {
        "twitter": ["posts", "threads", "spaces", "hashtags", "mentions"],
        "instagram": ["posts", "stories", "reels", "shopping", "hashtags"],
        "youtube": ["videos", "shorts", "live", "membership", "monetization"],
        "tiktok": ["videos", "challenges", "trends", "hashtags", "effects"],
        "reddit": ["posts", "comments", "communities", "ama", "reputation"]
    }
    return features.get(platform, ["posts"])


def get_ai_config(service: str) -> dict:
    """Get AI service configuration."""
    return {
        "enabled": True,
        "model": get_default_model(service),
        "limits": get_service_limits(service)
    }


def get_default_model(service: str) -> str:
    """Get default model for AI service."""
    models = {
        "openai": "gpt-4-turbo",
        "elevenlabs": "eleven_multilingual_v2",
        "synthesia": "default"
    }
    return models.get(service, "default")


def get_service_limits(service: str) -> dict:
    """Get service usage limits."""
    limits = {
        "openai": {"requests_per_minute": 500, "tokens_per_month": 1000000},
        "elevenlabs": {"characters_per_month": 30000},
        "synthesia": {"videos_per_month": 10}
    }
    return limits.get(service, {"requests_per_minute": 100})


def get_detailed_platform_config(platform: str, template: str) -> dict:
    """Get detailed platform configuration."""
    base_config = {
        "metadata": {
            "platform": platform,
            "template": template,
            "version": "1.0"
        },
        "authentication": {
            "method": "oauth2" if platform != "reddit" else "password",
            "scopes": get_platform_scopes(platform)
        },
        "content": {
            "max_length": get_platform_max_length(platform),
            "supported_media": get_supported_media(platform),
            "hashtag_limit": get_hashtag_limit(platform)
        },
        "posting": {
            "rate_limit": get_rate_limit(platform),
            "retry_policy": {
                "attempts": 3,
                "backoff": "exponential"
            }
        }
    }
    
    if template == "enterprise":
        base_config["advanced"] = {
            "analytics": True,
            "a_b_testing": True,
            "automation": True,
            "monetization": platform in ["youtube", "instagram", "twitter"]
        }
    
    return base_config


def get_platform_scopes(platform: str) -> List[str]:
    """Get required OAuth scopes for platform."""
    scopes = {
        "twitter": ["tweet.read", "tweet.write", "users.read"],
        "instagram": ["instagram_basic", "instagram_content_publish"],
        "youtube": ["youtube.upload", "youtube.readonly"],
        "tiktok": ["user.info.basic", "video.publish"],
        "reddit": ["submit", "read"]
    }
    return scopes.get(platform, [])


def get_platform_max_length(platform: str) -> int:
    """Get max content length for platform."""
    lengths = {
        "twitter": 280,
        "instagram": 2200,
        "youtube": 5000,
        "tiktok": 300,
        "reddit": 40000
    }
    return lengths.get(platform, 280)


def get_supported_media(platform: str) -> List[str]:
    """Get supported media types for platform."""
    media = {
        "twitter": ["image", "video", "gif"],
        "instagram": ["image", "video", "carousel"],
        "youtube": ["video", "thumbnail"],
        "tiktok": ["video"],
        "reddit": ["image", "video", "link"]
    }
    return media.get(platform, ["image"])


def get_hashtag_limit(platform: str) -> int:
    """Get hashtag limit for platform."""
    limits = {
        "twitter": 10,
        "instagram": 30,
        "youtube": 15,
        "tiktok": 20,
        "reddit": 0
    }
    return limits.get(platform, 5)


def get_rate_limit(platform: str) -> str:
    """Get rate limit for platform."""
    limits = {
        "twitter": "300/15min",
        "instagram": "200/hour",
        "youtube": "10000/day",
        "tiktok": "100/day",
        "reddit": "60/min"
    }
    return limits.get(platform, "100/hour")


def create_env_template(platforms: List[str], ai_services: List[str]) -> str:
    """Create .env template file."""
    content = """# AetherPost Environment Configuration
# Copy this file to .env.aetherpost and add your actual API keys

# ===========================================
# PLATFORM CREDENTIALS
# ===========================================

"""
    
    for platform in platforms:
        content += f"# {platform.upper()}\n"
        if platform == "twitter":
            content += """TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

"""
        elif platform == "instagram":
            content += """INSTAGRAM_APP_ID=your_app_id_here
INSTAGRAM_APP_SECRET=your_app_secret_here
INSTAGRAM_ACCESS_TOKEN=your_access_token_here

"""
        elif platform == "youtube":
            content += """YOUTUBE_API_KEY=your_api_key_here
YOUTUBE_CLIENT_ID=your_client_id_here
YOUTUBE_CLIENT_SECRET=your_client_secret_here
YOUTUBE_CHANNEL_ID=your_channel_id_here

"""
        elif platform == "tiktok":
            content += """TIKTOK_CLIENT_KEY=your_client_key_here
TIKTOK_CLIENT_SECRET=your_client_secret_here
TIKTOK_ACCESS_TOKEN=your_access_token_here

"""
        elif platform == "reddit":
            content += """REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_username_here
REDDIT_PASSWORD=your_password_here

"""
    
    content += """
# ===========================================
# AI SERVICES
# ===========================================

"""
    
    for service in ai_services:
        content += f"{service.upper()}_API_KEY=your_{service}_api_key_here\n"
    
    content += """
# ===========================================
# INFRASTRUCTURE
# ===========================================

# AWS (if using AWS backend)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1

# Redis (optional caching)
REDIS_URL=redis://localhost:6379
"""
    
    return content


def create_deployment_script(scripts_dir: Path, backend: str, template: str):
    """Create deployment script."""
    script_content = f"""#!/bin/bash
# AetherPost Deployment Script
# Generated for {backend} backend with {template} template

set -e

echo "🚀 Deploying AetherPost..."

# Check requirements
if ! command -v aetherpost &> /dev/null; then
    echo "❌ AetherPost CLI not found. Install with: pip install autopromo"
    exit 1
fi

# Validate configuration
echo "📋 Validating configuration..."
aetherpost validate

# Plan deployment
echo "📊 Planning deployment..."
aetherpost plan

# Apply (with confirmation)
read -p "Apply changes? (y/N): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo "✅ Applying changes..."
    aetherpost apply
else
    echo "❌ Deployment cancelled"
    exit 1
fi

echo "🎉 Deployment complete!"
"""
    
    script_path = scripts_dir / "deploy.sh"
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Make executable
    script_path.chmod(0o755)


def show_examples():
    """Show configuration examples."""
    console.print(Panel(
        """[bold]AetherPost Configuration Examples[/bold]

[cyan]1. Super Simple (Default):[/cyan]
   aetherpost init

[cyan]2. Quick Personal Project:[/cyan]
   aetherpost init my-project

[cyan]3. Custom Template:[/cyan]
   aetherpost init --template production --interactive

[cyan]4. With Custom Backend:[/cyan]
   aetherpost init --backend aws --interactive

[yellow]After initialization:[/yellow]
   • Edit .aetherpost/.env.template
   • Copy to .env.aetherpost with real API keys
   • Run: aetherpost plan
   • Run: aetherpost apply""",
        title="📚 Examples",
        border_style="green"
    ))


def show_next_steps(name: str, platforms: List[str]):
    """Show next steps after initialization."""
    console.print(f"\n[bold green]🎉 {name} ready for promotion![/bold green]\n")
    
    console.print("[bold]Next steps:[/bold]")
    console.print("1️⃣  Add API keys: [cyan]cp .aetherpost/.env.template .env.aetherpost[/cyan]")
    console.print("2️⃣  Preview posts: [cyan]aetherpost plan[/cyan]")
    console.print("3️⃣  Go live: [cyan]aetherpost apply[/cyan]")


if __name__ == "__main__":
    init_app()