"""Profile management command for social media accounts."""

import typer
import asyncio
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
import yaml
import os

from ...platforms.core.platform_registry import platform_registry
from ...platforms.core.platform_factory import platform_factory
from ...platforms.core.base_platform import Profile

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
    """Generate optimized social media profiles using the unified platform system."""
    
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
        platforms = platform_registry.get_available_platforms()
    else:
        # Validate requested platforms
        available_platforms = platform_registry.get_available_platforms()
        platforms = [p for p in platform if p in available_platforms]
        if len(platforms) != len(platform):
            invalid = set(platform) - set(platforms)
            console.print(f"⚠️  Invalid platforms: {', '.join(invalid)}")
    
    console.print(Panel(
        f"[bold green]Generating profiles for {project_info.get('name', 'your app')}[/bold green]",
        title="🎭 Profile Generation"
    ))
    
    # Generate profiles for each platform
    for platform_name in platforms:
        try:
            console.print(f"\n[bold blue]━━━ {platform_name.title()} Profile ━━━[/bold blue]")
            
            # Get platform info
            platform_info = platform_registry.get_platform_info(platform_name)
            if not platform_info or 'error' in platform_info:
                console.print(f"❌ Platform {platform_name} not available: {platform_info.get('error', 'Unknown error')}")
                continue
            
            # Generate profile using new system
            profile = _generate_profile_for_platform(platform_name, platform_info, project_info, style)
            
            # Display the generated profile
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Field", style="cyan", width=15)
            table.add_column("Value", style="white")
            
            table.add_row("Display Name", profile.display_name or "N/A")
            table.add_row("Bio", profile.bio or "N/A")
            if profile.website_url:
                table.add_row("Website", profile.website_url)
            if hasattr(profile, 'business_email') and profile.business_email:
                table.add_row("Contact", profile.business_email)
            
            char_count = len(profile.bio) if profile.bio else 0
            char_limit = platform_info.get('character_limit', 0)
            table.add_row("Characters", f"{char_count}/{char_limit}")
            
            console.print(table)
            
        except Exception as e:
            console.print(f"❌ Error generating {platform_name} profile: {e}")

@profile_app.command()
def platforms():
    """Show supported platforms and their requirements."""
    
    console.print(Panel(
        "[bold green]Supported Social Media Platforms[/bold green]",
        title="📱 Platform Support"
    ))
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Platform", style="cyan")
    table.add_column("Bio Limit")
    table.add_column("Content Types")
    table.add_column("Capabilities")
    
    available_platforms = platform_registry.get_available_platforms()
    for platform_name in sorted(available_platforms):
        try:
            platform_info = platform_registry.get_platform_info(platform_name)
            if platform_info and 'error' not in platform_info:
                content_types = ', '.join(platform_info.get('supported_content_types', [])[:3])
                if len(platform_info.get('supported_content_types', [])) > 3:
                    content_types += "..."
                    
                capabilities = ', '.join(platform_info.get('capabilities', [])[:3])
                if len(platform_info.get('capabilities', [])) > 3:
                    capabilities += "..."
                
                table.add_row(
                    platform_info.get('display_name', platform_name.title()),
                    str(platform_info.get('character_limit', 'N/A')),
                    content_types,
                    capabilities
                )
        except Exception as e:
            console.print(f"⚠️  Error loading {platform_name}: {e}")
    
    console.print(table)

@profile_app.command()
def update(
    platform: str = typer.Argument(..., help="Platform to update profile on"),
    campaign_config: Optional[str] = typer.Option("campaign.yaml", "--campaign-config", "-c", help="Path to campaign.yaml"),
    credentials_env: Optional[str] = typer.Option(".env.aetherpost", "--env", "-e", help="Path to credentials file")
):
    """Update profile on a specific platform."""
    
    # Check if platform is supported
    available_platforms = platform_registry.get_available_platforms()
    if platform not in available_platforms:
        console.print(f"❌ Platform '{platform}' not supported. Available: {', '.join(available_platforms)}")
        raise typer.Exit(1)
    
    # Load campaign config
    if not os.path.exists(campaign_config):
        console.print(f"❌ Campaign config not found: {campaign_config}")
        raise typer.Exit(1)
    
    try:
        with open(campaign_config, 'r', encoding='utf-8') as f:
            project_info = yaml.safe_load(f)
    except Exception as e:
        console.print(f"❌ Error loading campaign config: {e}")
        raise typer.Exit(1)
    
    # Load credentials
    credentials = {}
    if os.path.exists(credentials_env):
        try:
            with open(credentials_env, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        credentials[key.strip()] = value.strip().strip('"\'')
        except Exception as e:
            console.print(f"⚠️  Error loading credentials: {e}")
    
    # Extract platform-specific credentials
    platform_credentials = {}
    prefix = f"{platform.upper()}_"
    for key, value in credentials.items():
        if key.startswith(prefix):
            platform_key = key[len(prefix):].lower()
            platform_credentials[platform_key] = value
    
    if not platform_credentials:
        console.print(f"⚠️  No credentials found for {platform}")
        console.print(f"Add credentials to {credentials_env} with {prefix}* prefix")
        raise typer.Exit(1)
    
    async def update_profile_async():
        try:
            # Create platform instance
            platform_instance = platform_factory.create_platform(
                platform_name=platform,
                credentials=platform_credentials
            )
            
            # Get platform info for profile generation
            platform_info = platform_registry.get_platform_info(platform)
            
            # Generate profile
            profile = _generate_profile_for_platform(platform, platform_info, project_info, 'friendly')
            
            console.print(f"[bold blue]Updating {platform} profile...[/bold blue]")
            
            # Authenticate
            if not await platform_instance.authenticate():
                console.print(f"❌ Authentication failed for {platform}")
                return False
            
            # Update profile
            result = await platform_instance.update_profile(profile)
            
            if result.success:
                console.print(f"✅ Successfully updated {platform} profile")
                if result.raw_data and 'updates_made' in result.raw_data:
                    updates = result.raw_data['updates_made']
                    if updates:
                        console.print(f"📝 Updates made: {', '.join(updates)}")
                return True
            else:
                console.print(f"❌ Failed to update {platform} profile: {result.error_message}")
                return False
                
        except Exception as e:
            console.print(f"❌ Error updating profile: {e}")
            return False
        finally:
            if 'platform_instance' in locals():
                await platform_instance.cleanup()
    
    # Run async update
    success = asyncio.run(update_profile_async())
    if not success:
        raise typer.Exit(1)

@profile_app.command()
def demo():
    """Show profile generation demo with sample data."""
    
    console.print(Panel(
        "[bold green]AetherPost Profile Generator Demo[/bold green]\n"
        "This demo shows how to generate optimized profiles using the unified platform system.",
        title="🎭 Profile Demo"
    ))
    
    # Sample project data
    demo_data = {
        "name": "MyAwesomeApp",
        "description": "Revolutionary productivity tool for developers",
        "website_url": "https://myapp.example.com",
        "github_url": "https://github.com/user/myawesomeapp",
        "tech_stack": ["Python", "FastAPI", "React"],
        "features": ["automation", "developer-tools", "productivity"]
    }
    
    # Show profiles for available platforms (limit to 3 for demo)
    available_platforms = platform_registry.get_available_platforms()
    demo_platforms = available_platforms[:3]
    
    for platform_name in demo_platforms:
        try:
            console.print(f"\n[bold blue]━━━ {platform_name.title()} Profile ━━━[/bold blue]")
            
            platform_info = platform_registry.get_platform_info(platform_name)
            if not platform_info or 'error' in platform_info:
                console.print(f"❌ Platform {platform_name} not available")
                continue
                
            profile = _generate_profile_for_platform(platform_name, platform_info, demo_data, 'friendly')
            
            # Display the generated profile
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Field", style="cyan", width=15)
            table.add_column("Value", style="white")
            
            table.add_row("Display Name", profile.display_name or "N/A")
            table.add_row("Bio", profile.bio or "N/A")
            if profile.website_url:
                table.add_row("Website", profile.website_url)
            
            char_count = len(profile.bio) if profile.bio else 0
            char_limit = platform_info.get('character_limit', 0)
            table.add_row("Characters", f"{char_count}/{char_limit}")
            
            console.print(table)
            
        except Exception as e:
            console.print(f"❌ Error in demo for {platform_name}: {e}")

def _generate_profile_for_platform(platform_name: str, platform_info: Dict[str, Any], 
                                 project_info: Dict[str, Any], style: str) -> Profile:
    """Generate a profile for a specific platform using the unified system."""
    
    app_name = project_info.get("name", "AetherPost")
    description = project_info.get("description", "Social media automation for developers")
    char_limit = platform_info.get('character_limit', 280)
    
    # Generate platform-optimized bio based on character limit and style
    if char_limit <= 160:  # Twitter-like
        if style == "professional":
            bio = f"Building {app_name} - {description}"
        else:  # friendly
            bio = f"👋 Building {app_name}! {description}"
    elif char_limit <= 256:  # Bluesky-like
        if style == "professional":
            bio = f"Building {app_name} - {description}. Connecting with fellow developers and sharing progress."
        else:  # friendly
            bio = f"👋 Building {app_name}! {description}. Love connecting with fellow builders! #community"
    else:  # LinkedIn/longer platforms
        if style == "professional":
            bio = f"Building {app_name} | {description} | Helping developers automate their social media presence"
        else:  # friendly
            bio = f"👋 Creator of {app_name} - {description}. Always excited to connect with fellow developers!"
    
    # Ensure bio fits within platform limit
    if len(bio) > char_limit:
        bio = bio[:char_limit-3] + "..."
    
    # Create profile object
    profile = Profile(
        display_name=app_name,
        bio=bio,
        website_url=project_info.get("website_url"),
        location=project_info.get("location"),
        business_email=project_info.get("contact_email"),
        tags=project_info.get("features", [])
    )
    
    # Add additional URLs if available
    if project_info.get("github_url"):
        profile.additional_urls.append(project_info["github_url"])
    
    return profile