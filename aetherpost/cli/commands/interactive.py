"""Interactive command mode for AetherPost."""

import typer
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
import time

from ...core.config.models import CampaignConfig

console = Console()
interactive_app = typer.Typer()


@interactive_app.command()
def main():
    """Interactive command mode with real-time preview."""
    
    console.print(Panel(
        "[bold blue]🎭 AetherPost Interactive Mode[/bold blue]\n\n"
        "Real-time campaign building with live preview.\n"
        "Press Ctrl+C to exit at any time.",
        border_style="blue"
    ))
    
    try:
        # Initialize or load existing configuration
        config = load_or_create_config()
        
        # Main interactive loop
        while True:
            show_main_menu(config)
            choice = Prompt.ask(
                "What would you like to do?", 
                choices=["1", "2", "3", "4", "5", "6", "7", "q"], 
                default="1"
            )
            
            if choice == "q":
                break
            elif choice == "1":
                config = edit_basic_info(config)
            elif choice == "2":
                config = edit_platforms(config)
            elif choice == "3":
                config = edit_content_style(config)
            elif choice == "4":
                config = edit_scheduling(config)
            elif choice == "5":
                preview_campaign(config)
            elif choice == "6":
                execute_campaign(config)
            elif choice == "7":
                save_and_exit(config)
                break
        
        console.print("\n👋 [green]Thanks for using AetherPost![/green]")
        
    except KeyboardInterrupt:
        console.print("\n\n👋 [yellow]Interactive mode cancelled[/yellow]")


def load_or_create_config():
    """Load existing config or create new one."""
    from ...core.config.parser import ConfigLoader
    from ...core.config.models import CampaignConfig
    
    config_loader = ConfigLoader()
    
    if Path("campaign.yaml").exists():
        try:
            return config_loader.load_campaign_config()
        except Exception:
            console.print("⚠️ [yellow]Could not load existing config, creating new one[/yellow]")
    
    # Create minimal config
    return CampaignConfig(
        name="",
        concept="",
        platforms=["twitter"]
    )


def show_main_menu(config):
    """Display main menu with current configuration."""
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=8),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=5)
    )
    
    # Header
    layout["header"].update(Panel(
        "[bold]🎭 Interactive Campaign Builder[/bold]",
        border_style="blue"
    ))
    
    # Body - current configuration
    config_table = Table(title="Current Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="white")
    
    config_table.add_row("Name", config.name or "[dim]Not set[/dim]")
    config_table.add_row("Concept", config.concept or "[dim]Not set[/dim]")
    config_table.add_row("Platforms", ", ".join(config.platforms))
    config_table.add_row("Style", getattr(config.content, 'style', 'casual') if config.content else 'casual')
    config_table.add_row("URL", config.url or "[dim]Not set[/dim]")
    
    layout["body"].update(config_table)
    
    # Footer - menu options
    menu_text = """[bold]Options:[/bold]
1. Edit Basic Info    2. Edit Platforms    3. Edit Content Style    4. Edit Scheduling
5. Preview Campaign   6. Execute Campaign   7. Save & Exit          q. Quit"""
    
    layout["footer"].update(Panel(menu_text, border_style="green"))
    
    console.print(layout)


def edit_basic_info(config):
    """Edit basic campaign information."""
    
    console.print(Panel(
        "[bold]📝 Edit Basic Information[/bold]",
        border_style="cyan"
    ))
    
    # App name
    current_name = config.name or ""
    new_name = Prompt.ask("App/Service name", default=current_name)
    if new_name:
        config.name = new_name
    
    # Concept
    current_concept = config.concept or ""
    new_concept = Prompt.ask("Describe your app in one sentence", default=current_concept)
    if new_concept:
        config.concept = new_concept
    
    # URL
    current_url = config.url or ""
    new_url = Prompt.ask("App URL (optional)", default=current_url)
    config.url = new_url
    
    console.print("✅ [green]Basic information updated![/green]")
    return config


def edit_platforms(config):
    """Edit platform selection with preview."""
    
    console.print(Panel(
        "[bold]📱 Edit Platforms[/bold]",
        border_style="cyan"
    ))
    
    available_platforms = ["twitter", "bluesky", "mastodon", "linkedin", "dev_to"]
    selected_platforms = config.platforms.copy()
    
    platform_table = Table(title="Platform Selection")
    platform_table.add_column("Platform", style="cyan")
    platform_table.add_column("Selected", style="green")
    platform_table.add_column("Features", style="white")
    
    features = {
        "twitter": "280 chars, images, polls",
        "bluesky": "300 chars, images, threading",
        "mastodon": "500 chars, images, CW",
        "linkedin": "3000 chars, professional",
        "dev_to": "Articles, developer focus"
    }
    
    for platform in available_platforms:
        selected = "✅" if platform in selected_platforms else "❌"
        platform_table.add_row(platform.title(), selected, features.get(platform, ""))
    
    console.print(platform_table)
    
    # Let user modify selection
    for platform in available_platforms:
        current = platform in selected_platforms
        if Confirm.ask(f"Include {platform}?", default=current):
            if platform not in selected_platforms:
                selected_platforms.append(platform)
        else:
            if platform in selected_platforms:
                selected_platforms.remove(platform)
    
    config.platforms = selected_platforms
    console.print(f"✅ [green]Platforms updated: {', '.join(selected_platforms)}[/green]")
    return config


def edit_content_style(config):
    """Edit content style with live preview."""
    
    console.print(Panel(
        "[bold]🎨 Edit Content Style[/bold]",
        border_style="cyan"
    ))
    
    # Ensure content object exists
    if not config.content:
        from ...core.config.models import ContentConfig
        config.content = ContentConfig()
    
    # Style selection
    styles = {
        "1": ("casual", "Friendly with emojis 😊"),
        "2": ("professional", "Business-focused tone"),
        "3": ("technical", "Developer-oriented"),
        "4": ("humorous", "Playful and witty")
    }
    
    style_table = Table(title="Content Styles")
    style_table.add_column("Option", style="cyan")
    style_table.add_column("Style", style="green")
    style_table.add_column("Description", style="white")
    
    for key, (style, desc) in styles.items():
        current = "👈" if getattr(config.content, 'style', 'casual') == style else ""
        style_table.add_row(key, style.title(), f"{desc} {current}")
    
    console.print(style_table)
    
    choice = Prompt.ask("Select style", choices=list(styles.keys()), default="1")
    selected_style = styles[choice][0]
    config.content.style = selected_style
    
    # Call to action
    current_action = getattr(config.content, 'action', '')
    new_action = Prompt.ask("Call to action", default=current_action or "Learn more")
    config.content.action = new_action
    
    # Hashtags
    current_hashtags = getattr(config.content, 'hashtags', [])
    hashtags_str = Prompt.ask(
        "Hashtags (comma-separated)", 
        default=", ".join(current_hashtags) if current_hashtags else ""
    )
    
    if hashtags_str:
        config.content.hashtags = [tag.strip() for tag in hashtags_str.split(",")]
    
    console.print("✅ [green]Content style updated![/green]")
    return config


def edit_scheduling(config):
    """Edit scheduling options."""
    
    console.print(Panel(
        "[bold]⏰ Edit Scheduling[/bold]",
        border_style="cyan"
    ))
    
    schedule_options = {
        "1": "Post immediately",
        "2": "Schedule for specific time",
        "3": "Recurring posts", 
        "4": "Smart scheduling (optimal times)"
    }
    
    for key, desc in schedule_options.items():
        console.print(f"{key}. {desc}")
    
    choice = Prompt.ask("Select scheduling option", choices=list(schedule_options.keys()), default="1")
    
    from ...core.config.models import ScheduleConfig
    
    if choice == "1":
        config.schedule = ScheduleConfig(type="immediate")
    elif choice == "2":
        schedule_time = Prompt.ask("When to post (e.g., '2025-06-14 10:00', 'tomorrow 9am')")
        config.schedule = ScheduleConfig(type="delayed", time=schedule_time)
    elif choice == "3":
        frequency = Prompt.ask("Frequency", choices=["daily", "weekly", "monthly"], default="weekly")
        config.schedule = ScheduleConfig(type="recurring", frequency=frequency)
    elif choice == "4":
        config.schedule = ScheduleConfig(type="smart")
    
    console.print("✅ [green]Scheduling updated![/green]")
    return config


def preview_campaign(config):
    """Show live preview of campaign."""
    
    console.print(Panel(
        "[bold]👀 Campaign Preview[/bold]",
        border_style="green"
    ))
    
    # Validate required fields
    if not config.name or not config.concept:
        console.print("❌ [red]Missing required fields (name, concept)[/red]")
        return
    
    # Show config summary
    summary_table = Table(title="Campaign Summary")
    summary_table.add_column("Field", style="cyan")
    summary_table.add_column("Value", style="white")
    
    summary_table.add_row("Name", config.name)
    summary_table.add_row("Concept", config.concept)
    summary_table.add_row("Platforms", ", ".join(config.platforms))
    summary_table.add_row("Style", getattr(config.content, 'style', 'casual') if config.content else 'casual')
    
    console.print(summary_table)
    
    # Generate preview content
    try:
        console.print("\n[bold]Generated Content Preview:[/bold]")
        
        # Mock content generation for preview
        for platform in config.platforms:
            content = generate_preview_content(config, platform)
            console.print(f"\n[cyan]{platform.title()}:[/cyan]")
            console.print(f"[dim]{content}[/dim]")
    
    except Exception as e:
        console.print(f"⚠️ [yellow]Could not generate preview: {e}[/yellow]")
    
    Prompt.ask("Press Enter to continue")


def generate_preview_content(config, platform):
    """Generate mock content for preview."""
    
    style = getattr(config.content, 'style', 'casual') if config.content else 'casual'
    action = getattr(config.content, 'action', 'Learn more') if config.content else 'Learn more'
    
    # Simple template-based generation
    emoji = "🚀" if style == "casual" else ""
    intro = f"{emoji} Introducing {config.name}" if emoji else f"Introducing {config.name}"
    
    content = f"{intro} - {config.concept}"
    
    if config.url:
        content += f"\n\n{action} → {config.url}"
    else:
        content += f"\n\n{action}!"
    
    # Add hashtags
    if config.content and getattr(config.content, 'hashtags', []):
        hashtags = " ".join(f"#{tag}" for tag in config.content.hashtags[:3])
        content += f"\n\n{hashtags}"
    
    return content


def execute_campaign(config):
    """Execute the campaign."""
    
    console.print(Panel(
        "[bold]🚀 Execute Campaign[/bold]",
        border_style="red"
    ))
    
    # Validate configuration
    if not config.name or not config.concept:
        console.print("❌ [red]Cannot execute: Missing required fields[/red]")
        return
    
    # Check credentials
    creds_file = Path(".aetherpost/credentials.yaml")
    if not creds_file.exists():
        console.print("❌ [red]No credentials found. Run 'aetherpost setup wizard' first.[/red]")
        return
    
    # Final confirmation
    if not Confirm.ask("🚨 Execute campaign and post to all platforms?"):
        console.print("Execution cancelled.")
        return
    
    # Save configuration first
    try:
        from ...core.config.parser import ConfigLoader
        config_loader = ConfigLoader()
        config_loader.save_campaign_config(config)
        console.print("✅ Configuration saved")
    except Exception as e:
        console.print(f"❌ Failed to save configuration: {e}")
        return
    
    # Execute via apply command
    console.print("🚀 [blue]Executing campaign...[/blue]")
    try:
        from .apply import main as apply_main
        apply_main()
    except Exception as e:
        console.print(f"❌ [red]Execution failed: {e}[/red]")


def save_and_exit(config):
    """Save configuration and exit."""
    
    try:
        from ...core.config.parser import ConfigLoader
        config_loader = ConfigLoader()
        config_loader.save_campaign_config(config)
        console.print("✅ [green]Configuration saved to campaign.yaml[/green]")
    except Exception as e:
        console.print(f"❌ [red]Failed to save: {e}[/red]")


@interactive_app.command()
def wizard():
    """Step-by-step campaign creation wizard."""
    
    console.print(Panel(
        "[bold green]🧙‍♂️ AetherPost Campaign Wizard[/bold green]\n\n"
        "I'll guide you through creating your first campaign step by step.",
        border_style="green"
    ))
    
    steps = [
        ("📝", "Basic Information", setup_basic_info),
        ("📱", "Platform Selection", setup_platforms),
        ("🎨", "Content Style", setup_content_style),
        ("⏰", "Scheduling", setup_scheduling),
        ("🎯", "Advanced Options", setup_advanced),
        ("👀", "Review & Preview", review_config),
        ("🚀", "Ready to Launch", final_steps)
    ]
    
    config = CampaignConfig(name="", concept="", platforms=[])
    
    for i, (emoji, title, setup_func) in enumerate(steps, 1):
        console.print(f"\n[bold]Step {i}/{len(steps)}: {emoji} {title}[/bold]")
        console.rule(style="dim")
        
        config = setup_func(config)
        
        if i < len(steps):
            if not Confirm.ask("Continue to next step?", default=True):
                break
    
    console.print("\n🎉 [green]Wizard completed![/green]")


def setup_basic_info(config):
    """Wizard step 1: Basic information."""
    
    console.print("Let's start with some basic information about your app or service.")
    
    config.name = Prompt.ask("What's the name of your app/service?")
    config.concept = Prompt.ask("Describe it in one sentence (this helps generate better content)")
    
    if Confirm.ask("Do you have a website or URL?"):
        config.url = Prompt.ask("URL")
    
    console.print(f"✅ Got it! We're promoting [cyan]{config.name}[/cyan]")
    return config


def setup_platforms(config):
    """Wizard step 2: Platform selection."""
    
    console.print("Now let's choose where to post your content.")
    
    platforms = []
    
    if Confirm.ask("Post to Twitter?", default=True):
        platforms.append("twitter")
    
    if Confirm.ask("Post to Bluesky?"):
        platforms.append("bluesky")
    
    if Confirm.ask("Post to other platforms (Mastodon, LinkedIn)?"):
        if Confirm.ask("Include Mastodon?"):
            platforms.append("mastodon")
        if Confirm.ask("Include LinkedIn?"):
            platforms.append("linkedin")
    
    config.platforms = platforms
    console.print(f"✅ Will post to: [cyan]{', '.join(platforms)}[/cyan]")
    return config


def setup_content_style(config):
    """Wizard step 3: Content style."""
    
    console.print("Let's define the style and tone for your posts.")
    
    styles = ["casual", "professional", "technical", "humorous"]
    style_descriptions = {
        "casual": "Friendly, approachable, with emojis",
        "professional": "Business-focused, formal tone", 
        "technical": "Developer-oriented, precise",
        "humorous": "Playful, witty, engaging"
    }
    
    console.print("Available styles:")
    for i, style in enumerate(styles, 1):
        console.print(f"{i}. [cyan]{style.title()}[/cyan] - {style_descriptions[style]}")
    
    choice = IntPrompt.ask("Select style number", default=1, show_default=True)
    selected_style = styles[choice - 1]
    
    from ...core.config.models import ContentConfig
    config.content = ContentConfig(style=selected_style)
    
    config.content.action = Prompt.ask("Call to action (e.g., 'Try it free!', 'Learn more')", default="Learn more")
    
    console.print(f"✅ Style set to [cyan]{selected_style}[/cyan] with action '[cyan]{config.content.action}[/cyan]'")
    return config


def setup_scheduling(config):
    """Wizard step 4: Scheduling."""
    
    console.print("When would you like to post?")
    
    if Confirm.ask("Post immediately?", default=True):
        from ...core.config.models import ScheduleConfig
        config.schedule = ScheduleConfig(type="immediate")
        console.print("✅ Set to post immediately")
    else:
        console.print("Scheduling options coming soon! For now, set to immediate.")
        from ...core.config.models import ScheduleConfig
        config.schedule = ScheduleConfig(type="immediate")
    
    return config


def setup_advanced(config):
    """Wizard step 5: Advanced options."""
    
    console.print("Let's configure some advanced options.")
    
    if Confirm.ask("Include visual content (images)?"):
        if Confirm.ask("Generate images automatically?", default=True):
            config.image = "generate"
        else:
            config.image = Prompt.ask("Image path or 'none'", default="none")
    
    if Confirm.ask("Enable analytics tracking?", default=True):
        config.analytics = True
    
    console.print("✅ Advanced options configured")
    return config


def review_config(config):
    """Wizard step 6: Review configuration."""
    
    console.print("Let's review your campaign configuration:")
    
    review_table = Table(title="Campaign Review")
    review_table.add_column("Setting", style="cyan")
    review_table.add_column("Value", style="white")
    
    review_table.add_row("Name", config.name)
    review_table.add_row("Concept", config.concept)
    review_table.add_row("URL", config.url or "Not set")
    review_table.add_row("Platforms", ", ".join(config.platforms))
    review_table.add_row("Style", getattr(config.content, 'style', 'casual') if config.content else 'casual')
    review_table.add_row("Action", getattr(config.content, 'action', 'Learn more') if config.content else 'Learn more')
    
    console.print(review_table)
    
    if Confirm.ask("Looks good?", default=True):
        # Save configuration
        try:
            from ...core.config.parser import ConfigLoader
            config_loader = ConfigLoader()
            config_loader.save_campaign_config(config)
            console.print("✅ [green]Configuration saved![/green]")
        except Exception as e:
            console.print(f"❌ [red]Failed to save: {e}[/red]")
    
    return config


def final_steps(config):
    """Wizard step 7: Final steps."""
    
    console.print("🎉 Your campaign is ready!")
    
    next_steps = [
        "✅ Configuration saved to campaign.yaml",
        "🔍 Preview: aetherpost plan",
        "🚀 Execute: aetherpost apply",
        "📊 Monitor: aetherpost stats"
    ]
    
    for step in next_steps:
        console.print(step)
    
    if Confirm.ask("\nExecute campaign now?"):
        try:
            from .apply import main as apply_main
            apply_main()
        except Exception as e:
            console.print(f"❌ [red]Execution failed: {e}[/red]")
            console.print("You can run 'aetherpost apply' manually when ready.")
    
    return config