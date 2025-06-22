"""Initial setup wizard for new users."""

import typer
import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.config.parser import ConfigLoader
from ...core.config.models import CampaignConfig, CredentialsConfig
from .auth import setup_openai_auth
console = Console()
setup_app = typer.Typer()


@setup_app.command()
def wizard():
    """Interactive setup wizard for new users."""
    
    console.print(Panel(
        "[bold blue]🚀 AetherPost Setup Wizard[/bold blue]\n"
        "Welcome! Let's get you set up with AetherPost.",
        border_style="blue"
    ))
    
    # Check if already configured
    if Path("campaign.yaml").exists() or Path(".aetherpost").exists():
        if not Confirm.ask("AetherPost is already configured in this directory. Continue anyway?"):
            console.print("Setup cancelled.")
            return
    
    console.print("\n[bold]Step 1: Campaign Information[/bold]")
    setup_campaign()
    
    console.print("\n[bold]Step 2: Authentication Setup[/bold]")
    setup_authentication()
    
    console.print("\n[bold]Step 3: Test Setup[/bold]")
    asyncio.run(test_setup())
    
    show_next_steps()


def setup_campaign():
    """Setup basic campaign configuration."""
    name = Prompt.ask("? What's your app/service name?")
    concept = Prompt.ask("? Describe your app in one sentence")
    url = Prompt.ask("? App URL (optional)", default="")
    
    # Platform selection with better UX
    console.print("\n? Select social media platforms:")
    console.print("  [dim]Choose the platforms where you want to post[/dim]")
    
    platforms = []
    available_platforms = [
        ("twitter", "Twitter/X", True),
        ("bluesky", "Bluesky", False),
        ("mastodon", "Mastodon", False)
    ]
    
    for platform, display_name, default in available_platforms:
        if Confirm.ask(f"  • {display_name}", default=default):
            platforms.append(platform)
    
    if not platforms:
        platforms = ["twitter"]
        console.print("  [yellow]No platforms selected. Defaulting to Twitter.[/yellow]")
    
    # Style selection
    console.print("\n? Choose your posting style:")
    styles = [
        ("casual", "😊 Casual - Friendly with emojis"),
        ("professional", "💼 Professional - Business-focused"),
        ("technical", "⚙️ Technical - Developer-oriented"),
        ("humorous", "😄 Humorous - Playful and witty")
    ]
    
    for i, (key, desc) in enumerate(styles, 1):
        console.print(f"  {i}. {desc}")
    
    style_choice = Prompt.ask("Select style", choices=["1", "2", "3", "4"], default="1")
    style_map = {"1": "casual", "2": "professional", "3": "technical", "4": "humorous"}
    style = style_map[style_choice]
    
    # Create campaign config
    config = CampaignConfig(
        name=name,
        concept=concept,
        url=url if url else None,
        platforms=platforms,
        content={"style": style, "action": "Learn more"}
    )
    
    # Save configuration
    config_loader = ConfigLoader()
    config_loader.save_campaign_config(config)
    
    console.print("✅ [green]Campaign configuration saved[/green]")


def setup_authentication():
    """Setup authentication for selected platforms and AI providers."""
    config_loader = ConfigLoader()
    config = config_loader.load_campaign_config()
    credentials = CredentialsConfig()
    
    # Setup platform authentication
    for platform in config.platforms:
        console.print(f"\n[cyan]Setting up {platform.title()} authentication...[/cyan]")
        
        if platform == "twitter":
            setup_twitter_auth(credentials, config_loader)
        else:
            console.print(f"[dim]{platform.title()} setup will be available soon[/dim]")
    
    # Setup AI provider (required for content generation)
    console.print(f"\n[cyan]Setting up AI provider for content generation...[/cyan]")
    console.print("AetherPost needs an AI provider to generate engaging posts.")
    console.print("Choose one of the following:")
    
    ai_choice = Prompt.ask(
        "AI Provider", 
        choices=["[AI Service]", "openai", "skip"], 
        default="[AI Service]",
        show_choices=True
    )
    
    if ai_choice == "[AI Service]":
        setup_claude_auth(credentials, config_loader)
    elif ai_choice == "openai":
        setup_openai_auth(credentials, config_loader)
    else:
        console.print("[yellow]Skipping AI setup. You can configure it later with 'aetherpost auth setup'[/yellow]")


async def test_setup():
    """Test the configuration."""
    console.print("Testing your setup...")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Test configuration
        task1 = progress.add_task("Validating configuration...", total=None)
        config_loader = ConfigLoader()
        
        try:
            config = config_loader.load_campaign_config()
            issues = config_loader.validate_config(config)
            
            if issues:
                progress.update(task1, description="❌ Configuration has issues")
                for issue in issues:
                    console.print(f"  • {issue}")
                return
            else:
                progress.update(task1, description="✅ Configuration valid")
        except Exception as e:
            progress.update(task1, description=f"❌ Configuration error: {e}")
            return
        
        # Test authentication
        task2 = progress.add_task("Testing authentication...", total=None)
        
        try:
            credentials = config_loader.load_credentials()
            
            # Test Twitter if configured
            if hasattr(credentials, 'twitter') and credentials.twitter:
                from ...plugins.manager import plugin_manager
                
                try:
                    connector = plugin_manager.load_connector('twitter', credentials.twitter)
                    auth_success = await connector.authenticate(credentials.twitter)
                    
                    if auth_success:
                        progress.update(task2, description="✅ Twitter authentication successful")
                    else:
                        progress.update(task2, description="❌ Twitter authentication failed")
                        return
                except Exception as e:
                    progress.update(task2, description=f"❌ Twitter test failed: {e}")
                    return
            else:
                progress.update(task2, description="⚠️ No authentication configured")
        
        except Exception as e:
            progress.update(task2, description=f"❌ Authentication test failed: {e}")
            return
        
        # Test content generation
        task3 = progress.add_task("Testing content generation...", total=None)
        
        try:
            from ...core.content.generator import ContentGenerator
            
            content_generator = ContentGenerator(credentials)
            test_content = await content_generator.generate_content(config, config.platforms[0])
            
            if test_content and test_content.get("text"):
                progress.update(task3, description="✅ Content generation working")
                console.print(f"\n[dim]Sample generated content:[/dim]")
                console.print(f"[italic]{test_content['text']}[/italic]")
            else:
                progress.update(task3, description="❌ Content generation failed")
        
        except Exception as e:
            progress.update(task3, description=f"❌ Content generation error: {e}")


def show_next_steps():
    """Show next steps to the user with installation completion banner."""
    
    # ASCII art banner inspired by Claude Code startup
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     █████╗ ███████╗████████╗██╗  ██╗███████╗██████╗           ║
    ║    ██╔══██╗██╔════╝╚══██╔══╝██║  ██║██╔════╝██╔══██╗          ║
    ║    ███████║█████╗     ██║   ███████║█████╗  ██████╔╝          ║
    ║    ██╔══██║██╔══╝     ██║   ██╔══██║██╔══╝  ██╔══██╗          ║
    ║    ██║  ██║███████╗   ██║   ██║  ██║███████╗██║  ██║          ║
    ║    ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝          ║
    ║                                                               ║
    ║        ██████╗  ██████╗ ███████╗████████╗                    ║
    ║        ██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝                    ║
    ║        ██████╔╝██║   ██║███████╗   ██║                       ║
    ║        ██╔═══╝ ██║   ██║╚════██║   ██║                       ║
    ║        ██║     ╚██████╔╝███████║   ██║                       ║
    ║        ╚═╝      ╚═════╝ ╚══════╝   ╚═╝                       ║
    ║                                                               ║
    ║                 🚀 INSTALLATION COMPLETE! 🚀                  ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    
    console.print(f"[bold cyan]{banner}[/bold cyan]")
    
    console.print(Panel(
        "[bold green]🎉 AetherPost is ready to automate your social media![/bold green]\n\n"
        
        "[bold blue]📋 Quick Start Commands:[/bold blue]\n"
        "• [cyan]aetherpost init[/cyan] - Create a campaign configuration\n"
        "• [cyan]aetherpost plan[/cyan] - Preview your content before posting\n"
        "• [cyan]aetherpost apply[/cyan] - Execute and post to all platforms\n\n"
        
        "[bold blue]🎭 Interactive Mode:[/bold blue]\n"
        "• [cyan]aetherpost interactive[/cyan] - Full interactive campaign builder\n"
        "• [cyan]aetherpost interactive wizard[/cyan] - Step-by-step guided setup\n\n"
        
        "[bold blue]⚡ Advanced Usage:[/bold blue]\n"
        "• [cyan]aetherpost now \"Your message\"[/cyan] - Quick one-off post\n"
        "• [cyan]aetherpost profile generate[/cyan] - Optimize your social profiles\n"
        "• [cyan]aetherpost stats[/cyan] - View campaign analytics\n"
        "• [cyan]aetherpost validate[/cyan] - Check your configuration\n\n"
        
        "[bold blue]🔗 Learn More:[/bold blue]\n"
        "• Documentation: [link]https://aether-post.com[/link]\n"
        "• Examples: [link]https://github.com/fununnn/aetherpost/tree/main/examples[/link]\n"
        "• Community: [link]https://github.com/fununnn/aetherpost/discussions[/link]",
        
        title="🚀 You're All Set!",
        border_style="green"
    ))


@setup_app.command()
def check():
    """Check current setup status."""
    console.print(Panel(
        "[bold blue]🔍 Setup Status Check[/bold blue]",
        border_style="blue"
    ))
    
    checks = []
    
    # Check campaign config
    if Path("campaign.yaml").exists():
        try:
            config_loader = ConfigLoader()
            config = config_loader.load_campaign_config()
            issues = config_loader.validate_config(config)
            
            if not issues:
                checks.append(("✅", "Campaign configuration", "Valid"))
            else:
                checks.append(("❌", "Campaign configuration", f"{len(issues)} issues found"))
        except Exception as e:
            checks.append(("❌", "Campaign configuration", f"Error: {e}"))
    else:
        checks.append(("❌", "Campaign configuration", "Not found - run 'aetherpost init main'"))
    
    # Check credentials
    creds_file = Path(".aetherpost/credentials.enc")
    if creds_file.exists():
        try:
            config_loader = ConfigLoader()
            credentials = config_loader.load_credentials()
            
            # Check each platform
            platform_count = 0
            if hasattr(credentials, 'twitter') and credentials.twitter:
                platform_count += 1
            if hasattr(credentials, 'ai_service') and credentials.ai_service:
                platform_count += 1
            if hasattr(credentials, 'openai') and credentials.openai:
                platform_count += 1
            
            if platform_count > 0:
                checks.append(("✅", "Authentication", f"{platform_count} service(s) configured"))
            else:
                checks.append(("❌", "Authentication", "No services configured"))
        
        except Exception as e:
            checks.append(("❌", "Authentication", f"Error: {e}"))
    else:
        checks.append(("❌", "Authentication", "Not configured - run 'aetherpost auth setup'"))
    
    # Check dependencies
    try:
        import tweepy, anthropic, rich, typer
        checks.append(("✅", "Dependencies", "All required packages installed"))
    except ImportError as e:
        checks.append(("❌", "Dependencies", f"Missing package: {e}"))
    
    # Display results
    for status, item, details in checks:
        console.print(f"{status} {item}: [dim]{details}[/dim]")
    
    # Show recommendations
    failed_checks = [check for check in checks if check[0] == "❌"]
    if failed_checks:
        console.print(f"\n[yellow]💡 Run 'aetherpost setup wizard' to fix issues[/yellow]")
    else:
        console.print(f"\n[green]🎉 Everything looks good! Ready to post.[/green]")


@setup_app.command()  
def reset():
    """Reset AetherPost configuration."""
    if not Confirm.ask("This will delete all AetherPost configuration. Continue?"):
        console.print("Reset cancelled.")
        return
    
    # Remove files
    files_to_remove = [
        Path("campaign.yaml"),
        Path("promo.state.json"),
        Path(".aetherpost")
    ]
    
    removed_count = 0
    for file_path in files_to_remove:
        try:
            if file_path.is_file():
                file_path.unlink()
                removed_count += 1
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
                removed_count += 1
        except Exception as e:
            console.print(f"[red]Failed to remove {file_path}: {e}[/red]")
    
    if removed_count > 0:
        console.print(f"✅ [green]Reset complete. Removed {removed_count} items.[/green]")
        console.print("Run [cyan]aetherpost setup wizard[/cyan] to start fresh.")
    else:
        console.print("ℹ️ No AetherPost configuration found.")