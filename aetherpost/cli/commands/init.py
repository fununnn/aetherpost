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
    quick: bool = typer.Option(True, "--quick/--interactive", "-q", help="Quick setup with defaults (default: True)"),
    template: str = typer.Option("starter", "--template", "-t", 
                                help="Template type (starter, production, enterprise)"),
    example: bool = typer.Option(False, "--example", help="Show configuration examples"),
    backend: str = typer.Option("local", "--backend", "-b", 
                               help="Backend type (local, aws, cloud)"),
    upgrade: bool = typer.Option(False, "--upgrade", help="Upgrade existing configuration"),
):
    """Initialize AetherPost workspace - Simple and quick by default."""
    
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
    
    selected_platforms = []
    
    if quick:
        selected_platforms = ["twitter", "reddit"]  # Quick defaults - free platforms
    else:
        console.print("Select platforms to enable:")
        for platform, info in available_platforms.items():
            default = info["required"] or (template == "production")
            
            if Confirm.ask(f"Enable {info['name']}? ({info['cost']})", default=default):
                selected_platforms.append(platform)
    
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
    
    if quick:
        content_language = "en"  # Default to English
    else:
        console.print("Available languages for content generation:")
        for code, name in available_languages.items():
            console.print(f"  {code}: {name}")
        
        content_language = Prompt.ask(
            "Choose content language", 
            choices=list(available_languages.keys()), 
            default="en"
        )
    
    # AI Services configuration
    console.print(f"\n[bold]🤖 AI Services Configuration:[/bold]")
    
    ai_services = {
        "openai": {"name": "OpenAI GPT", "cost": "$0.002-0.06/1K tokens", "required": True},
        "elevenlabs": {"name": "ElevenLabs TTS", "cost": "$5-330/month", "required": False},
        "synthesia": {"name": "Synthesia Video", "cost": "$30-90/month", "required": False}
    }
    
    selected_ai = []
    
    if quick:
        selected_ai = ["openai"]  # Essential only
    else:
        for service, info in ai_services.items():
            default = info["required"] or (template == "enterprise")
            
            if Confirm.ask(f"Enable {info['name']}? ({info['cost']})", default=default):
                selected_ai.append(service)
    
    # Backend configuration
    console.print(f"\n[bold]☁️ Backend Configuration:[/bold]")
    
    backends = {
        "local": "Local files (development)",
        "aws": "AWS S3 + DynamoDB (production)",
        "cloud": "AetherPost Cloud (managed)"
    }
    
    if not quick:
        for b, desc in backends.items():
            console.print(f"  {b}: {desc}")
        backend = Prompt.ask("Choose backend", choices=list(backends.keys()), default=backend)
    
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
    create_workspace(name, template, selected_platforms, selected_ai, backend, autopromo_dir, content_language)
    
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
                    backend: str, autopromo_dir: Path, content_language: str = "en"):
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
    
    console.print(f"\n✅ [green]AetherPost workspace initialized successfully![/green]")
    console.print(f"📁 Configuration created in: [cyan].aetherpost/[/cyan]")
    
    # Auto-install dependencies if requirements file exists
    if Path("requirements-oss.txt").exists():
        console.print(f"\n📦 [yellow]Installing dependencies automatically...[/yellow]")
        import subprocess
        try:
            subprocess.run(["pip", "install", "-r", "requirements-oss.txt"], check=True, capture_output=True)
            subprocess.run(["pip", "install", "-e", "."], check=True, capture_output=True)
            console.print(f"✅ [green]Dependencies installed successfully![/green]")
        except subprocess.CalledProcessError:
            console.print(f"⚠️ [yellow]Dependencies installation failed. Please run manually:[/yellow]")
            console.print(f"   pip install -r requirements-oss.txt")
            console.print(f"   pip install -e .")


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
    console.print(f"\n[bold green]🎉 {name} initialized successfully![/bold green]\n")
    
    steps = [
        "1️⃣  Copy [cyan].aetherpost/.env.template[/cyan] to [cyan].env.aetherpost[/cyan]",
        "2️⃣  Add your API keys to [cyan].env.aetherpost[/cyan]",
        "3️⃣  Test configuration: [cyan]aetherpost validate[/cyan]",
        "4️⃣  Plan your first promotion: [cyan]aetherpost plan[/cyan]",
        "5️⃣  Apply configuration: [cyan]aetherpost apply[/cyan]"
    ]
    
    for step in steps:
        console.print(step)
    
    console.print(f"\n[dim]💡 Quick start: aetherpost promote \"Hello World!\" --platforms {','.join(platforms[:2])}[/dim]")
    
    # Show example campaign configuration
    console.print(f"\n[bold]📝 Example campaign.yaml:[/bold]")
    example_yaml = f"""[dim]name: "{name}-campaign"
concept: "Awesome AI-powered productivity tool"
url: "https://myapp.com"
platforms: [{', '.join(f'"{p}"' for p in platforms[:3])}]
content:
  style: casual
  action: "Try it now!"
  language: en  # Change to ja, es, fr, de, ko, etc.
  hashtags: ["#AI", "#productivity"]
[/dim]"""
    console.print(example_yaml)
    
    # Show helpful links
    console.print(f"\n[bold]📚 Helpful Resources:[/bold]")
    console.print("• Documentation: [blue]https://d3b75mcubdhimz.cloudfront.net[/blue]")
    console.print("• GitHub: [blue]https://github.com/fununnn/aetherpost[/blue]") 
    console.print("• Multi-Language Examples: [blue]examples/multilang-campaign.yaml[/blue]")
    console.print("• Language Support: [blue]20+ languages including Japanese, Spanish, French, German, Korean[/blue]")


if __name__ == "__main__":
    init_app()