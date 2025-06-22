"""Plan command implementation."""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

from ...core.config.parser import ConfigLoader
from ...core.content.generator import ContentGenerator
from ...plugins.manager import plugin_manager

console = Console()
plan_app = typer.Typer()


def plan_main(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file"),
):
    """Preview campaign content before posting."""
    
    console.print(Panel(
        "[bold blue]📋 Campaign Preview[/bold blue]",
        border_style="blue"
    ))
    
    try:
        # Load configuration
        config_loader = ConfigLoader()
        config = config_loader.load_campaign_config(config_file)
        
        # Validate configuration
        issues = config_loader.validate_config(config)
        if issues:
            console.print("⚠️  [yellow]Configuration Issues:[/yellow]")
            for issue in issues:
                console.print(f"  • {issue}")
            console.print()
        
        # Run content generation
        asyncio.run(generate_preview(config))
        
    except FileNotFoundError:
        console.print(f"❌ [red]Configuration file not found: {config_file}[/red]")
        console.print("Run [cyan]aetherpost init[/cyan] to create a configuration file.")
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


async def generate_preview(config):
    """Generate and display content preview."""
    
    # Load credentials for AI providers
    config_loader = ConfigLoader()
    credentials = config_loader.load_credentials()
    
    # Initialize content generator
    content_generator = ContentGenerator(credentials)
    
    # Generate content for each platform
    platform_previews = []
    
    for platform in config.platforms:
        try:
            console.print(f"⠋ Generating content for {platform}...")
            
            # Generate content
            content = await content_generator.generate_content(config, platform)
            
            # Create preview panel
            preview_text = Text()
            preview_text.append(content.get("text", ""), style="white")
            
            # Add media info if present
            if content.get("media"):
                preview_text.append(f"\n\n📎 Media: {len(content['media'])} item(s)", style="dim")
            
            # Add hashtags if present
            if content.get("hashtags"):
                preview_text.append(f"\n🏷️  {' '.join(content['hashtags'])}", style="blue")
            
            platform_panel = Panel(
                preview_text,
                title=f"[bold]{platform.title()}[/bold]",
                border_style="green"
            )
            
            platform_previews.append(platform_panel)
            
            console.print(f"✓ Generated content for {platform}")
        
        except Exception as e:
            error_panel = Panel(
                f"[red]Error generating content: {e}[/red]",
                title=f"[bold]{platform.title()}[/bold]",
                border_style="red"
            )
            platform_previews.append(error_panel)
    
    # Display all platform previews
    if len(platform_previews) == 1:
        console.print(platform_previews[0])
    else:
        console.print(Columns(platform_previews, equal=True))
    
    # Show campaign details
    show_campaign_details(config)
    
    # Show execution plan
    console.print("\n[bold]Execution Plan:[/bold]")
    console.print(f"• Platforms: {len(config.platforms)} ({', '.join(config.platforms)})")
    console.print(f"• Schedule: {config.schedule.type}")
    if config.image:
        console.print(f"• Visual content: {config.image}")
    
    console.print(f"\n💡 Run [cyan]aetherpost apply[/cyan] to execute this campaign")


def show_campaign_details(config):
    """Show detailed campaign information."""
    console.print("\n[bold]Campaign Details:[/bold]")
    console.print(f"• Name: {config.name}")
    console.print(f"• Concept: {config.concept}")
    if config.url:
        console.print(f"• URL: {config.url}")
    console.print(f"• Style: {config.content.style}")
    console.print(f"• Action: {config.content.action}")
    
    if config.experiments:
        console.print(f"• A/B Testing: {config.experiments.enabled}")
        if config.experiments.enabled:
            console.print(f"  Variants: {len(config.experiments.variants)}")
    
    if config.story:
        console.print(f"• Story Mode: {config.story.title}")
        console.print(f"  Episodes: {len(config.story.episodes)}")


@plan_app.command("story")
def plan_story(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file"),
):
    """Preview story mode content."""
    
    console.print(Panel(
        "[bold blue]📖 Story Preview[/bold blue]",
        border_style="blue"
    ))
    
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_campaign_config(config_file)
        
        if not config.story:
            console.print("❌ [red]Story mode not configured[/red]")
            console.print("Add a 'story' section to your campaign.yaml")
            return
        
        # Show story episodes
        console.print(f"[bold]Story: {config.story.title}[/bold]\n")
        
        for i, episode in enumerate(config.story.episodes, 1):
            console.print(f"Episode {i}: [cyan]{episode.get('title', 'Untitled')}[/cyan]")
            console.print(f"  Template: {episode.get('template', 'default')}")
            if episode.get('schedule'):
                console.print(f"  Schedule: {episode['schedule']}")
            console.print()
    
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


@plan_app.command("variants")
def plan_variants(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file"),
):
    """Preview A/B test variants."""
    
    console.print(Panel(
        "[bold blue]🧪 A/B Test Variants[/bold blue]",
        border_style="blue"
    ))
    
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_campaign_config(config_file)
        
        if not config.experiments or not config.experiments.enabled:
            console.print("❌ [red]A/B testing not enabled[/red]")
            console.print("Add an 'experiments' section to your campaign.yaml")
            return
        
        # Show variants
        for i, variant in enumerate(config.experiments.variants, 1):
            variant_panel = Panel(
                f"Action: {variant.get('action', 'N/A')}\n"
                f"Style: {variant.get('style', config.content.style)}",
                title=f"[bold]Variant {i}[/bold]",
                border_style="cyan"
            )
            console.print(variant_panel)
        
        console.print(f"\n[bold]Test Configuration:[/bold]")
        console.print(f"• Metric: {config.experiments.metric}")
        console.print(f"• Duration: {config.experiments.duration}")
    
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")