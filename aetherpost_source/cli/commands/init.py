"""Initialize command implementation - Terraform-style workflow."""

import typer
from pathlib import Path
from typing import Optional, List, Dict
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
import yaml
import json
import getpass
import os

console = Console()
init_app = typer.Typer()

# API Requirements Configuration
API_REQUIREMENTS = {
    "levels": {
        "starter": {
            "name": "Starter (Twitter + AI)",
            "description": "Essential setup for basic promotion",
            "required": ["openai", "twitter"],
            "optional": ["slack_webhook"]
        },
        "recommended": {
            "name": "Recommended (+ Reddit)", 
            "description": "Good coverage with developer communities",
            "required": ["openai", "twitter", "reddit"],
            "optional": ["slack_webhook", "line_notify"]
        },
        "advanced": {
            "name": "Advanced (+ YouTube)",
            "description": "Multi-platform with video content",
            "required": ["openai", "twitter", "reddit", "youtube"],
            "optional": ["slack_webhook", "line_notify"]
        },
        "complete": {
            "name": "Complete (All Platforms)",
            "description": "Full feature set with all integrations", 
            "required": ["openai", "twitter", "reddit", "youtube", "bluesky"],
            "optional": ["slack_webhook", "line_notify", "instagram"]
        }
    },
    "services": {
        "openai": {
            "name": "OpenAI API",
            "description": "AI content generation (GPT-3.5/4)",
            "cost": "$0.002-0.06/1K tokens",
            "setup_url": "https://platform.openai.com/api-keys",
            "keys": ["OPENAI_API_KEY"]
        },
        "twitter": {
            "name": "Twitter API v2", 
            "description": "Post tweets and threads",
            "cost": "Free tier + $100/month for high volume",
            "setup_url": "https://developer.twitter.com/en/portal",
            "keys": ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"]
        },
        "reddit": {
            "name": "Reddit API",
            "description": "Post to subreddits", 
            "cost": "Free (60 requests/minute)",
            "setup_url": "https://www.reddit.com/prefs/apps",
            "keys": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]
        },
        "youtube": {
            "name": "YouTube Data API v3",
            "description": "Upload videos and manage channel",
            "cost": "Free quota + $0.002/100 units", 
            "setup_url": "https://console.cloud.google.com/apis",
            "keys": ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"]
        },
        "bluesky": {
            "name": "Bluesky API",
            "description": "Post to Bluesky social network",
            "cost": "Free",
            "setup_url": "https://bsky.app",
            "keys": ["BLUESKY_HANDLE", "BLUESKY_PASSWORD"]
        },
        "slack_webhook": {
            "name": "Slack Notifications",
            "description": "Preview notifications before posting",
            "cost": "Free",
            "setup_url": "https://api.slack.com/apps",
            "keys": ["SLACK_WEBHOOK_URL"]
        },
        "instagram": {
            "name": "Instagram Graph API",
            "description": "Post photos, reels, and stories",
            "cost": "Free (rate limited, business account required)",
            "setup_url": "https://developers.facebook.com/docs/instagram-api",
            "keys": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID"]
        },
        "line_notify": {
            "name": "LINE Notify",
            "description": "Mobile notifications",
            "cost": "Free", 
            "setup_url": "https://notify-bot.line.me",
            "keys": ["LINE_NOTIFY_TOKEN"]
        }
    }
}


def collect_api_keys(selected_platforms: List[str], template: str) -> Dict[str, str]:
    """Collect API keys based on selected platforms and template."""
    
    console.print(Panel(
        "[bold]🔑 API Keys Setup[/bold]\n\n"
        "We'll help you set up the API keys needed for your selected platforms.\n"
        "You can start with the basics and add more later.",
        title="API Configuration",
        border_style="yellow"
    ))
    
    # Determine setup level based on platforms
    setup_level = determine_setup_level(selected_platforms, template)
    
    # Show setup level options
    console.print(f"\n[bold]📊 Recommended Setup Level:[/bold]")
    levels = API_REQUIREMENTS["levels"]
    
    table = Table()
    table.add_column("Level", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Required APIs", style="green")
    
    for level_key, level_info in levels.items():
        marker = "→" if level_key == setup_level else " "
        required_count = len(level_info["required"])
        table.add_row(
            f"{marker} {level_info['name']}",
            level_info["description"], 
            f"{required_count} required"
        )
    
    console.print(table)
    
    # Let user choose setup level
    chosen_level = Prompt.ask(
        "Choose setup level",
        choices=list(levels.keys()),
        default=setup_level
    )
    
    # Collect API keys for chosen level
    api_keys = {}
    level_config = levels[chosen_level]
    
    console.print(f"\n[bold]🔧 Setting up {level_config['name']}:[/bold]")
    
    # Required APIs
    console.print("\n[bold green]Required APIs:[/bold green]")
    for service_key in level_config["required"]:
        service_info = API_REQUIREMENTS["services"][service_key]
        keys = collect_service_keys(service_key, service_info, required=True)
        api_keys.update(keys)
    
    # Optional APIs
    if level_config["optional"]:
        setup_optional = Confirm.ask("\nSet up optional services (notifications, etc.)?")
        if setup_optional:
            console.print("\n[bold yellow]Optional APIs:[/bold yellow]")
            for service_key in level_config["optional"]:
                service_info = API_REQUIREMENTS["services"][service_key]
                setup_this = Confirm.ask(f"Set up {service_info['name']}?")
                if setup_this:
                    keys = collect_service_keys(service_key, service_info, required=False)
                    api_keys.update(keys)
    
    return api_keys


def determine_setup_level(platforms: List[str], template: str) -> str:
    """Determine recommended setup level based on platforms and template."""
    if template == "enterprise":
        return "complete"
    elif "youtube" in platforms:
        return "advanced"
    elif "reddit" in platforms:
        return "recommended"
    else:
        return "starter"


def collect_service_keys(service_key: str, service_info: Dict, required: bool = True) -> Dict[str, str]:
    """Collect API keys for a specific service."""
    console.print(f"\n[bold]{service_info['name']}[/bold]")
    console.print(f"Description: {service_info['description']}")
    console.print(f"Cost: {service_info['cost']}")
    console.print(f"Setup guide: [blue]{service_info['setup_url']}[/blue]")
    
    keys = {}
    
    for key_name in service_info["keys"]:
        prompt_text = f"Enter {key_name}"
        if not required:
            prompt_text += " (optional, press Enter to skip)"
        
        # Use getpass for sensitive API keys
        if "API_KEY" in key_name or "SECRET" in key_name or "TOKEN" in key_name:
            value = getpass.getpass(f"{prompt_text}: ")
        else:
            value = Prompt.ask(prompt_text, default="" if not required else None)
        
        if value:
            keys[key_name] = value
        elif required:
            console.print(f"[red]⚠️ {key_name} is required for {service_info['name']}[/red]")
            # Allow user to skip if they want to set up later
            skip = Confirm.ask("Skip this service for now? (you can add it later)")
            if skip:
                break
            else:
                return collect_service_keys(service_key, service_info, required)
    
    return keys


def save_api_keys(api_keys: Dict[str, str], autopromo_dir: Path):
    """Save API keys to .env.aetherpost file."""
    env_file = autopromo_dir.parent / ".env.aetherpost"
    
    # Create header
    content = """# AetherPost API Configuration
# Generated automatically by 'aetherpost init'
# Keep this file secure and do not commit to version control

# ===========================================
# PLATFORM CREDENTIALS
# ===========================================

"""
    
    # Group keys by service
    service_groups = {
        "AI Services": ["OPENAI_API_KEY"],
        "Twitter": ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"],
        "Reddit": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"],
        "YouTube": ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"],
        "Bluesky": ["BLUESKY_HANDLE", "BLUESKY_PASSWORD"],
        "Instagram": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID"],
        "Notifications": ["SLACK_WEBHOOK_URL", "LINE_NOTIFY_TOKEN"]
    }
    
    for group_name, group_keys in service_groups.items():
        group_has_keys = any(key in api_keys for key in group_keys)
        if group_has_keys:
            content += f"# {group_name}\n"
            for key in group_keys:
                if key in api_keys:
                    content += f"{key}={api_keys[key]}\n"
            content += "\n"
    
    # Write to file
    with open(env_file, "w") as f:
        f.write(content)
    
    # Set secure permissions (readable only by owner)
    env_file.chmod(0o600)


def validate_api_keys(api_keys: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """Validate API key formats and provide setup status."""
    results = {}
    
    # OpenAI validation
    if "OPENAI_API_KEY" in api_keys:
        key = api_keys["OPENAI_API_KEY"]
        if key.startswith("sk-") and len(key) > 20:
            results["OpenAI"] = {"status": "valid", "message": "API key format looks correct"}
        else:
            results["OpenAI"] = {"status": "warning", "message": "API key format may be incorrect"}
    
    # Twitter validation
    twitter_keys = ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"]
    twitter_count = sum(1 for key in twitter_keys if key in api_keys)
    if twitter_count == 4:
        results["Twitter"] = {"status": "valid", "message": "All required keys provided"}
    elif twitter_count > 0:
        results["Twitter"] = {"status": "warning", "message": f"Only {twitter_count}/4 keys provided"}
    
    # Reddit validation
    reddit_keys = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
    reddit_count = sum(1 for key in reddit_keys if key in api_keys)
    if reddit_count == 2:
        results["Reddit"] = {"status": "valid", "message": "Required keys provided"}
    elif reddit_count > 0:
        results["Reddit"] = {"status": "warning", "message": f"Only {reddit_count}/2 required keys provided"}
    
    # YouTube validation
    youtube_keys = ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"]
    youtube_count = sum(1 for key in youtube_keys if key in api_keys)
    if youtube_count == 2:
        results["YouTube"] = {"status": "valid", "message": "OAuth2 credentials provided"}
    elif youtube_count > 0:
        results["YouTube"] = {"status": "warning", "message": "Incomplete OAuth2 setup"}
    
    # Bluesky validation
    bluesky_keys = ["BLUESKY_HANDLE", "BLUESKY_PASSWORD"]
    bluesky_count = sum(1 for key in bluesky_keys if key in api_keys)
    if bluesky_count == 2:
        results["Bluesky"] = {"status": "valid", "message": "Credentials provided"}
    elif bluesky_count > 0:
        results["Bluesky"] = {"status": "warning", "message": "Incomplete credentials"}
    
    # Instagram validation
    instagram_keys = ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID"]
    instagram_count = sum(1 for key in instagram_keys if key in api_keys)
    if instagram_count == 2:
        results["Instagram"] = {"status": "valid", "message": "Business account setup complete"}
    elif instagram_count > 0:
        results["Instagram"] = {"status": "warning", "message": "Incomplete business account setup"}
    
    # Notification services
    if "SLACK_WEBHOOK_URL" in api_keys:
        webhook = api_keys["SLACK_WEBHOOK_URL"]
        if webhook.startswith("https://hooks.slack.com/"):
            results["Slack"] = {"status": "valid", "message": "Webhook URL format correct"}
        else:
            results["Slack"] = {"status": "warning", "message": "Webhook URL format may be incorrect"}
    
    return results


def show_validation_results(results: Dict[str, Dict[str, str]]):
    """Display API key validation results."""
    if not results:
        return
        
    console.print(f"\n[bold]🔍 API Key Validation:[/bold]")
    
    table = Table()
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Message", style="dim")
    
    for service, result in results.items():
        status = result["status"]
        if status == "valid":
            status_icon = "✅"
            status_color = "green"
        else:
            status_icon = "⚠️"
            status_color = "yellow"
        
        table.add_row(
            service,
            f"[{status_color}]{status_icon} {status.title()}[/{status_color}]",
            result["message"]
        )
    
    console.print(table)


def init_main(
    name: Optional[str] = typer.Argument(None, help="Project name"),
    quick: bool = typer.Option(False, "--quick/--interactive", "-q", help="Interactive setup with prompts (default: True)"),
    template: str = typer.Option("starter", "--template", "-t", 
                                help="Template type (starter, production, enterprise)"),
    example: bool = typer.Option(False, "--example", help="Show configuration examples"),
    backend: str = typer.Option("local", "--backend", "-b", 
                               help="Backend type (local, aws, cloud)"),
    upgrade: bool = typer.Option(False, "--upgrade", help="Upgrade existing configuration"),
    generate_profiles: bool = typer.Option(True, "--generate-profiles/--no-profiles", help="Generate social media profiles during init"),
):
    """Initialize AetherPost workspace - Interactive setup by default."""
    
    if example:
        show_examples()
        return
    
    # Check for existing campaign.yaml - auto-setup mode
    campaign_file = Path("campaign.yaml")
    if campaign_file.exists() and not upgrade:
        try:
            with open(campaign_file, "r", encoding="utf-8") as f:
                existing_campaign = yaml.safe_load(f)
            
            console.print(Panel(
                "[bold green]📋 既存設定を検出しました[/bold green]\n\n"
                "[dim]campaign.yaml が見つかりました[/dim]\n\n"
                f"• プロジェクト: {existing_campaign.get('name', 'Unknown')}\n"
                f"• プラットフォーム: {', '.join(existing_campaign.get('platforms', []))}\n"
                f"• 言語: {existing_campaign.get('content', {}).get('language', 'en')}\n\n"
                "既存設定を使用して自動初期化します...",
                title="🚀 Auto Setup Mode",
                border_style="green"
            ))
            
            # Auto-setup using existing campaign
            auto_setup_from_campaign(existing_campaign)
            return
            
        except Exception as e:
            console.print(f"⚠️ [yellow]campaign.yaml読み込みエラー: {e}[/yellow]")
            console.print("インタラクティブモードで続行します...")
    
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
    
    # API Key Collection
    console.print(f"\n[bold]🔑 API Keys Setup:[/bold]")
    api_keys = collect_api_keys(selected_platforms, template)
    
    # Notification Settings
    console.print(f"\n[bold]📱 通知設定（Notification Settings）:[/bold]")
    console.print("投稿前に確認通知を受け取りますか？")
    console.print("1) あり - Slack/LINE通知で事前確認（推奨）")
    console.print("2) なし - 自動投稿（確認なし）")
    
    notification_choice = Prompt.ask("通知設定を選択 (1-2)", default="1")
    enable_notifications = notification_choice == "1"
    
    if enable_notifications:
        console.print("✅ [green]通知ありモード: apply実行時に事前確認通知を送信します[/green]")
        auto_apply = False
    else:
        console.print("⚡ [yellow]自動実行モード: apply実行後に自動的に投稿します[/yellow]")
        auto_apply = True
    
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
        summary_table.add_row("Notification Mode", "事前確認あり" if enable_notifications else "自動実行")
        summary_table.add_row("AI Services", ", ".join(selected_ai))
        summary_table.add_row("Backend", backend)
        summary_table.add_row("Est. Monthly Cost", estimated_cost.get("total", "$0-50"))
        
        console.print(summary_table)
        
        if not Confirm.ask("Proceed with this configuration?"):
            console.print("❌ Initialization cancelled")
            return
    
    # Create workspace with API keys and notification settings
    create_workspace(name, template, selected_platforms, selected_ai, backend, autopromo_dir, content_language, concept, use_free_tier, content_style, api_keys, enable_notifications, auto_apply)
    
    # Generate profiles if requested
    if generate_profiles:
        console.print(f"\n[bold]🎭 Generating optimized social media profiles...[/bold]")
        try:
            from ...core.profile_manager import ProfileManager
            
            profile_manager = ProfileManager()
            campaign_data = {
                "name": name,
                "description": concept,
                "urls": {
                    "main": f"https://{name.lower().replace(' ', '')}.com",
                    "github": f"https://github.com/user/{name.lower().replace(' ', '')}",
                }
            }
            
            generated_profiles = {}
            for platform in selected_platforms:
                if platform in ['twitter', 'bluesky', 'instagram', 'linkedin', 'github', 'youtube']:
                    profile = profile_manager.generate_profile(platform, campaign_data, style=content_style)
                    generated_profiles[platform] = profile
                    console.print(f"  ✅ Generated {platform.title()} profile")
            
            # Save profiles to workspace
            profiles_file = autopromo_dir / "generated_profiles.json"
            with open(profiles_file, "w") as f:
                import json
                json.dump(generated_profiles, f, indent=2)
            
            console.print(f"[green]✅ Profiles saved to: {profiles_file}[/green]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Profile generation failed: {e}[/yellow]")
            console.print("[dim]You can generate profiles later with: aetherpost profile generate[/dim]")
    
    # Next steps
    show_next_steps(name, selected_platforms, bool(api_keys))


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
                    use_free_tier: bool = True, content_style: str = "casual", api_keys: Dict[str, str] = None,
                    enable_notifications: bool = True, auto_apply: bool = False):
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
        "notifications": {
            "enabled": enable_notifications,
            "auto_apply": auto_apply,
            "preview_required": enable_notifications
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
        },
        "notifications": {
            "enabled": enable_notifications,
            "auto_apply": auto_apply
        }
    }
    
    with open("campaign.yaml", "w") as f:
        yaml.dump(campaign_yaml, f, default_flow_style=False, sort_keys=False)
    
    console.print(f"\n✅ [green]AetherPost workspace initialized successfully![/green]")
    console.print(f"📁 Configuration created in: [cyan].aetherpost/[/cyan]")
    console.print(f"📝 Campaign template created: [cyan]campaign.yaml[/cyan]")
    
    # Save API keys to .env.aetherpost
    if api_keys:
        save_api_keys(api_keys, autopromo_dir)
        console.print(f"🔑 [green]API keys saved securely to .env.aetherpost[/green]")
        
        # Validate API keys
        validation_results = validate_api_keys(api_keys)
        show_validation_results(validation_results)
    
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


def show_next_steps(name: str, platforms: List[str], api_keys_configured: bool = False):
    """Show next steps after initialization."""
    console.print(f"\n[bold green]🎉 {name} ready for promotion![/bold green]\n")
    
    console.print("[bold]Next steps:[/bold]")
    
    if api_keys_configured:
        console.print("1️⃣  ✅ [green]API keys configured[/green]")
        console.print("2️⃣  Test connection: [cyan]aetherpost auth test[/cyan]")
        console.print("3️⃣  Preview posts: [cyan]aetherpost plan[/cyan]")
        console.print("4️⃣  Go live: [cyan]aetherpost apply[/cyan]")
    else:
        console.print("1️⃣  Set up API keys: [cyan]aetherpost auth setup[/cyan]")
        console.print("2️⃣  Or manually edit: [cyan].env.aetherpost[/cyan]")
        console.print("3️⃣  Preview posts: [cyan]aetherpost plan[/cyan]")
        console.print("4️⃣  Go live: [cyan]aetherpost apply[/cyan]")
    
    # Show API requirements for selected platforms
    console.print(f"\n[bold]🔑 Required APIs for your platforms:[/bold]")
    api_table = Table()
    api_table.add_column("Platform", style="cyan")
    api_table.add_column("Required APIs", style="green")
    api_table.add_column("Setup Guide", style="blue")
    
    platform_apis = {
        "twitter": ("Twitter API v2", "https://developer.twitter.com/en/portal"),
        "reddit": ("Reddit API", "https://www.reddit.com/prefs/apps"),
        "youtube": ("YouTube Data API v3", "https://console.cloud.google.com/apis"),
        "bluesky": ("Bluesky API", "https://bsky.app"),
        "instagram": ("Instagram Basic Display", "https://developers.facebook.com/")
    }
    
    # Always show OpenAI requirement
    api_table.add_row("AI Content", "OpenAI API", "https://platform.openai.com/api-keys")
    
    for platform in platforms:
        if platform in platform_apis:
            name, url = platform_apis[platform]
            api_table.add_row(platform.title(), name, url)
    
    console.print(api_table)


def auto_setup_from_campaign(campaign_config: dict):
    """Auto-setup workspace from existing campaign.yaml."""
    
    # Extract configuration from campaign
    name = campaign_config.get('name', 'my-project')
    concept = campaign_config.get('concept', f'Innovative {name} application')
    platforms = campaign_config.get('platforms', ['twitter', 'reddit'])
    content_config = campaign_config.get('content', {})
    content_style = content_config.get('style', 'casual')
    content_language = content_config.get('language', 'en')
    notifications_config = campaign_config.get('notifications', {})
    enable_notifications = notifications_config.get('enabled', True)
    auto_apply = notifications_config.get('auto_apply', False)
    
    # Check for template hints
    explicit_template = campaign_config.get('template', '')
    if explicit_template in ['starter', 'production', 'enterprise']:
        template = explicit_template
    else:
        template = "starter"
        if len(platforms) >= 3:
            template = "production"
    
    # Default AI services
    ai_services = ["openai"]
    backend = "local"
    use_free_tier = campaign_config.get('limits', {}).get('free_tier', True)
    
    # Create workspace directory
    autopromo_dir = Path(".aetherpost")
    
    # Check for existing API keys
    env_file = Path(".env.aetherpost")
    api_keys = {}
    
    if env_file.exists():
        console.print("🔑 [green].env.aetherpost が見つかりました - API設定を読み込み中...[/green]")
        # Read existing API keys
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if value:
                            api_keys[key] = value
            console.print(f"✅ [green]{len(api_keys)}個のAPIキーを読み込みました[/green]")
        except Exception as e:
            console.print(f"⚠️ [yellow].env.aetherpost読み込みエラー: {e}[/yellow]")
    else:
        console.print("📝 [yellow].env.aetherpostが見つかりません - 後でAPI設定が必要です[/yellow]")
    
    # Create workspace with existing configuration
    create_workspace(
        name=name,
        template=template,
        platforms=platforms,
        ai_services=ai_services,
        backend=backend,
        autopromo_dir=autopromo_dir,
        content_language=content_language,
        concept=concept,
        use_free_tier=use_free_tier,
        content_style=content_style,
        api_keys=api_keys,
        enable_notifications=enable_notifications,
        auto_apply=auto_apply
    )
    
    console.print(f"\n✅ [bold green]{name}の自動初期化が完了しました！[/bold green]")
    
    # Show status and next steps
    if api_keys:
        console.print("\n[bold]🎯 準備完了 - すぐに開始できます:[/bold]")
        console.print("1️⃣  コンテンツ確認: [cyan]aetherpost plan[/cyan]")
        console.print("2️⃣  投稿実行: [cyan]aetherpost apply[/cyan]")
        
        if auto_apply:
            console.print("\n⚡ [yellow]自動実行モードが有効です - apply実行で確認なしで投稿します[/yellow]")
        else:
            console.print("\n📱 [blue]通知モードが有効です - apply実行前に確認通知を受け取ります[/blue]")
    else:
        console.print("\n[bold]🔑 次のステップ:[/bold]")
        console.print("1️⃣  API設定: [cyan].env.aetherpost[/cyan]ファイルを作成")
        console.print("2️⃣  設定例: [cyan].aetherpost/.env.template[/cyan]を参考")
        console.print("3️⃣  確認: [cyan]aetherpost plan[/cyan]")
        console.print("4️⃣  実行: [cyan]aetherpost apply[/cyan]")
    
    # Show detected configuration
    console.print(f"\n[bold]📋 検出された設定:[/bold]")
    summary_table = Table()
    summary_table.add_column("項目", style="cyan")
    summary_table.add_column("値", style="white")
    
    summary_table.add_row("プロジェクト名", name)
    summary_table.add_row("テンプレート", template)
    summary_table.add_row("プラットフォーム", ", ".join(platforms))
    summary_table.add_row("コンテンツ言語", content_language)
    summary_table.add_row("通知モード", "事前確認あり" if enable_notifications else "自動実行")
    summary_table.add_row("API設定", "✅ 設定済み" if api_keys else "❌ 未設定")
    
    console.print(summary_table)
    
    console.print(f"\n🎭 [dim]Meta: このワークフローはClaude Codeなどによる自動プロジェクト生成に最適化されています[/dim]")


if __name__ == "__main__":
    init_app()