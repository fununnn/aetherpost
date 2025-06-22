"""Profile management command for social media accounts."""

import typer
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
import yaml

from ...core.profiles.generator import ProfileGenerator, ProfileContent

console = Console()

# Create profile app
profile_app = typer.Typer(name="profile", help="Generate and manage social media profiles")

@profile_app.command()
def generate(
    app_name: Optional[str] = typer.Option(None, "--app-name", "-n", help="Your app/product name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="App description"),
    github_url: Optional[str] = typer.Option(None, "--github-url", "-g", help="GitHub repository URL"),
    website_url: Optional[str] = typer.Option(None, "--website-url", "-w", help="Website URL"),
    platform: List[str] = typer.Option([], "--platform", "-P", help="Specific platforms (default: all)"),
    style: str = typer.Option('friendly', "--style", "-s", help="Profile style"),
    campaign_config: Optional[str] = typer.Option(None, "--campaign-config", "-c", help="Path to campaign.yaml")
):
    """Generate optimized social media profiles."""
    
    generator = ProfileGenerator()
    
    # Load campaign config if provided
    project_info = {}
    if campaign_config:
        try:
            with open(campaign_config, 'r', encoding='utf-8') as f:
                campaign_data = yaml.safe_load(f)
                project_info.update(campaign_data)
                console.print(f"✅ Loaded campaign config from {campaign_config}")
        except Exception as e:
            console.print(f"⚠️  Could not load campaign config: {e}")
    
    # Override with provided values
    if app_name:
        project_info["name"] = app_name
    if description:
        project_info["description"] = description
    if website_url:
        project_info["website_url"] = website_url
    if github_url:
        project_info["github_url"] = github_url
    
    # Set defaults if nothing provided
    if not project_info.get("name"):
        project_info["name"] = "AetherPost"
    if not project_info.get("description"):
        project_info["description"] = "Social media automation for developers"
    
    # Determine platforms to generate
    if not platform:
        platforms = ["twitter", "bluesky", "instagram", "github"]
    else:
        platforms = platform
    
    console.print(Panel(
        f"[bold green]Generating profiles for {project_info.get('name', 'your app')}[/bold green]",
        title="🎭 Profile Generation"
    ))
    
    # Generate profiles for each platform
    for platform_name in platforms:
        try:
            console.print(f"\n[bold blue]━━━ {platform_name.title()} Profile ━━━[/bold blue]")
            
            profile = generator.generate_profile(platform_name, project_info, style)
            
            # Display the generated profile
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Field", style="cyan", width=15)
            table.add_column("Value", style="white")
            
            table.add_row("Display Name", profile.display_name)
            table.add_row("Bio", profile.bio)
            if profile.website_url:
                table.add_row("Website", profile.website_url)
            
            table.add_row("Characters", f"{profile.character_count}/{profile.character_limit}")
            
            console.print(table)
            
        except Exception as e:
            console.print(f"❌ Error generating {platform_name} profile: {e}")

@profile_app.command()
def platforms():
    """Show supported platforms and their requirements."""
    
    generator = ProfileGenerator()
    
    console.print(Panel(
        "[bold green]Supported Social Media Platforms[/bold green]",
        title="📱 Platform Support"
    ))
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Platform", style="cyan")
    table.add_column("Bio Limit")
    table.add_column("Features")
    
    platforms = generator.get_supported_platforms()
    for platform_name in platforms:
        config = generator.get_platform_requirements(platform_name)
        if config:
            features = []
            if config.supports_website:
                features.append("Website")
            if config.supports_location:
                features.append("Location")
            if config.emoji_friendly:
                features.append("Emoji")
            
            table.add_row(
                platform_name.title(),
                str(config.bio_max_length),
                ", ".join(features)
            )
    
    console.print(table)

@profile_app.command()
def demo():
    """Show profile generation demo with sample data."""
    
    console.print(Panel(
        "[bold green]AetherPost Profile Generator Demo[/bold green]\n"
        "This demo shows how to generate optimized profiles for your app.",
        title="🎭 Profile Demo"
    ))
    
    # Sample project data
    demo_data = {
        "name": "MyAwesomeApp",
        "description": "Revolutionary productivity tool for developers",
        "urls": {
            "main": "https://myapp.example.com",
            "github": "https://github.com/user/myawesomeapp",
            "docs": "https://docs.myapp.example.com"
        },
        "tech_stack": ["Python", "FastAPI", "React"],
        "features": ["automation", "developer-tools", "productivity"]
    }
    
    generator = ProfileGenerator()
    
    # Show profiles for major platforms
    demo_platforms = ["twitter", "bluesky"]
    
    for platform in demo_platforms:
        console.print(f"\n[bold blue]━━━ {platform.title()} Profile ━━━[/bold blue]")
        
        profile = generator.generate_profile(platform, demo_data)
        
        # Display the generated profile
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan", width=15)
        table.add_column("Value", style="white")
        
        table.add_row("Display Name", profile.display_name)
        table.add_row("Bio", profile.bio)
        if profile.website_url:
            table.add_row("Website", profile.website_url)
        
        table.add_row("Characters", f"{profile.character_count}/{profile.character_limit}")
        
        console.print(table)
        
        if profile.additional_links:
            console.print("\n[dim]Additional URLs:[/dim]")
            for link in profile.additional_links:
                console.print(f"  • {link['title']}: {link['url']}")