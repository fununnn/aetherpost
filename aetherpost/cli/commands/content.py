"""Content generation and strategy commands."""

import typer
import asyncio
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from datetime import datetime, timedelta

from ...core.content.strategy import (
    PlatformContentStrategy, 
    ContentType, 
    PostingSchedule
)
from ...core.settings import config
from ...core.connector_factory import connector_factory

console = Console()
content_app = typer.Typer()


@content_app.command()
def generate(
    content_type: str = typer.Argument(..., help="Content type (announcement, maintenance, educational, etc.)"),
    platform: str = typer.Option("all", "--platform", "-p", help="Target platform"),
    title: Optional[str] = typer.Option(None, "--title", help="Content title"),
    description: Optional[str] = typer.Option(None, "--description", help="Content description"),
    schedule: bool = typer.Option(False, "--schedule", help="Schedule for optimal time"),
    preview: bool = typer.Option(True, "--preview", help="Preview before posting"),
):
    """Generate platform-appropriate content based on type and context."""
    
    console.print(Panel(
        "[bold blue]AetherPost Content Generator[/bold blue]",
        subtitle="Platform-optimized content creation"
    ))
    
    # Validate content type
    try:
        content_type_enum = ContentType(content_type.lower())
    except ValueError:
        console.print(f"❌ Invalid content type: {content_type}")
        console.print("Available types: announcement, maintenance, educational, engagement, promotional, periodic, behind_scenes, community, status")
        return
    
    # Get platforms
    if platform == "all":
        platforms = config.get_configured_platforms()
    else:
        platforms = [platform]
    
    # Interactive content gathering if not provided
    context = gather_content_context(content_type_enum, title, description)
    
    # Generate content for each platform
    strategy = PlatformContentStrategy()
    generated_content = {}
    
    for plat in platforms:
        try:
            content_result = strategy.generate_content(content_type_enum, plat, context)
            generated_content[plat] = content_result
        except Exception as e:
            console.print(f"❌ Failed to generate content for {plat}: {e}")
    
    # Display generated content
    display_generated_content(generated_content, content_type_enum)
    
    # Validation and suggestions
    for plat, content_data in generated_content.items():
        validation = strategy.validate_content_appropriateness(
            content_data["text"], plat, content_type_enum
        )
        
        if validation["warnings"]:
            console.print(f"\n⚠️  [yellow]{plat} warnings:[/yellow]")
            for warning in validation["warnings"]:
                console.print(f"   • {warning}")
        
        if validation["suggestions"]:
            console.print(f"\n💡 [blue]{plat} suggestions:[/blue]")
            for suggestion in validation["suggestions"]:
                console.print(f"   • {suggestion}")
    
    # Posting options
    if not preview or Confirm.ask("Post this content now?"):
        post_generated_content(generated_content, schedule)


@content_app.command()
def schedule_maintenance(
    maintenance_type: str = typer.Argument(..., help="Type of maintenance (update, security, feature, etc.)"),
    description: str = typer.Option(..., "--description", help="Maintenance description"),
    start_time: str = typer.Option(..., "--start", help="Start time (YYYY-MM-DD HH:MM)"),
    duration: str = typer.Option("2 hours", "--duration", help="Expected duration"),
    impact: str = typer.Option("minimal", "--impact", help="Expected impact (minimal, moderate, significant)"),
    platforms: str = typer.Option("all", "--platforms", help="Platforms to notify"),
):
    """Schedule maintenance notifications across platforms."""
    
    console.print(Panel(
        "[bold yellow]🔧 Maintenance Notification Scheduler[/bold yellow]",
        subtitle="Keep your community informed"
    ))
    
    # Parse platforms
    if platforms == "all":
        platform_list = config.get_configured_platforms()
    else:
        platform_list = [p.strip() for p in platforms.split(",")]
    
    # Create maintenance context
    context = {
        "maintenance_type": maintenance_type.title(),
        "description": description,
        "schedule": f"{start_time} (Duration: {duration})",
        "impact": f"{impact.title()} service interruption expected"
    }
    
    # Generate maintenance notifications
    strategy = PlatformContentStrategy()
    notifications = {}
    
    for platform in platform_list:
        try:
            content = strategy.generate_content(ContentType.MAINTENANCE, platform, context)
            notifications[platform] = content
        except Exception as e:
            console.print(f"❌ Failed to generate notification for {platform}: {e}")
    
    # Display notifications
    display_generated_content(notifications, ContentType.MAINTENANCE)
    
    # Schedule posting
    if Confirm.ask("Schedule these maintenance notifications?"):
        # Calculate posting times (e.g., 24h before, 2h before, during, after)
        posting_times = calculate_maintenance_posting_times(start_time)
        
        console.print("\n📅 Scheduled posting times:")
        for timing, time_str in posting_times.items():
            console.print(f"   • {timing}: {time_str}")
        
        # In a real implementation, this would integrate with a scheduling system
        console.print("\n✅ Maintenance notifications scheduled!")


@content_app.command()
def periodic_setup(
    frequency: str = typer.Argument(..., help="Frequency (daily, weekly, monthly)"),
    content_types: str = typer.Option("engagement,educational", "--types", help="Content types to rotate"),
    platforms: str = typer.Option("all", "--platforms", help="Target platforms"),
    start_date: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
):
    """Set up periodic content posting schedule."""
    
    console.print(Panel(
        "[bold green]📅 Periodic Content Setup[/bold green]",
        subtitle="Automate your content strategy"
    ))
    
    # Parse frequency
    try:
        frequency_enum = PostingSchedule(frequency.lower())
    except ValueError:
        console.print(f"❌ Invalid frequency: {frequency}")
        console.print("Available: daily, weekly, monthly")
        return
    
    # Parse content types
    content_type_list = []
    for ct in content_types.split(","):
        try:
            content_type_list.append(ContentType(ct.strip().lower()))
        except ValueError:
            console.print(f"⚠️  Skipping invalid content type: {ct}")
    
    # Parse platforms
    if platforms == "all":
        platform_list = config.get_configured_platforms()
    else:
        platform_list = [p.strip() for p in platforms.split(",")]
    
    # Create posting schedule
    schedule_plan = create_periodic_schedule(
        frequency_enum, content_type_list, platform_list, start_date
    )
    
    # Display schedule plan
    display_schedule_plan(schedule_plan)
    
    # Confirm and save
    if Confirm.ask("Set up this periodic posting schedule?"):
        save_periodic_schedule(schedule_plan)
        console.print("✅ Periodic content schedule configured!")


@content_app.command()
def templates():
    """Show available content templates and examples."""
    
    console.print(Panel(
        "[bold cyan]📝 Content Templates[/bold cyan]",
        subtitle="Available templates for each platform"
    ))
    
    strategy = PlatformContentStrategy()
    
    # Show content types
    console.print("\n[bold]Available Content Types:[/bold]")
    for content_type in ContentType:
        console.print(f"  • {content_type.value}: {get_content_type_description(content_type)}")
    
    # Show platform-specific templates
    for platform in ["twitter", "instagram", "youtube", "reddit", "tiktok"]:
        if platform in strategy.templates:
            console.print(f"\n[bold]{platform.title()} Templates:[/bold]")
            
            table = Table()
            table.add_column("Content Type", style="cyan")
            table.add_column("Template Preview", style="white")
            table.add_column("Schedule", style="green")
            
            for content_type, template in strategy.templates[platform].items():
                preview = template.template[:100] + "..." if len(template.template) > 100 else template.template
                schedule_str = template.schedule.value if template.schedule else "On-demand"
                table.add_row(content_type.value, preview, schedule_str)
            
            console.print(table)


def gather_content_context(content_type: ContentType, title: Optional[str], 
                          description: Optional[str]) -> dict:
    """Interactively gather context for content generation."""
    
    context = {}
    
    if content_type == ContentType.ANNOUNCEMENT:
        context["title"] = title or Prompt.ask("Announcement title")
        context["description"] = description or Prompt.ask("Brief description")
        context["call_to_action"] = Prompt.ask("Call to action", default="Check it out!")
        
        if Confirm.ask("Add detailed benefits?"):
            benefits = []
            while True:
                benefit = Prompt.ask("Benefit (empty to finish)", default="")
                if not benefit:
                    break
                benefits.append(f"• {benefit}")
            context["benefits"] = "\n".join(benefits)
    
    elif content_type == ContentType.MAINTENANCE:
        context["maintenance_type"] = Prompt.ask("Maintenance type", default="Scheduled Update")
        context["description"] = description or Prompt.ask("What's being updated?")
        context["schedule"] = Prompt.ask("When?", default="Tonight 2:00-4:00 AM UTC")
        context["impact"] = Prompt.ask("Expected impact", default="Minimal service interruption")
    
    elif content_type == ContentType.ENGAGEMENT:
        context["question"] = Prompt.ask("Question to ask the community")
        context["context"] = description or Prompt.ask("Additional context", default="")
    
    elif content_type == ContentType.EDUCATIONAL:
        context["tip_title"] = title or Prompt.ask("Tip/Tutorial title")
        context["tip_content"] = description or Prompt.ask("Main tip content")
        
        if Confirm.ask("Add pro tips?"):
            pro_tips = []
            while True:
                tip = Prompt.ask("Pro tip (empty to finish)", default="")
                if not tip:
                    break
                pro_tips.append(f"• {tip}")
            context["pro_tips"] = "\n".join(pro_tips)
    
    elif content_type == ContentType.PERIODIC:
        context["accomplishments"] = Prompt.ask("Recent accomplishments")
        context["in_progress"] = Prompt.ask("What's in progress")
        context["next_week"] = Prompt.ask("What's coming next")
    
    elif content_type == ContentType.BEHIND_SCENES:
        context["development_story"] = description or Prompt.ask("Development story")
        context["challenges_overcome"] = Prompt.ask("Challenges overcome", default="")
        context["team_insights"] = Prompt.ask("Team insights", default="")
    
    return context


def display_generated_content(content_dict: dict, content_type: ContentType):
    """Display generated content in a formatted way."""
    
    console.print(f"\n[bold]📝 Generated {content_type.value.title()} Content:[/bold]")
    
    for platform, content_data in content_dict.items():
        console.print(f"\n[bold cyan]{platform.title()}:[/bold cyan]")
        
        # Content preview
        console.print(Panel(
            content_data["text"],
            title=f"{platform} - {content_data['tone']}",
            border_style="blue"
        ))
        
        # Hashtags
        if content_data["hashtags"]:
            console.print(f"🏷️  Hashtags: {', '.join(content_data['hashtags'])}")
        
        # Media requirements
        if content_data["media_requirements"]["required"]:
            console.print(f"📸 Media required: {content_data['media_requirements']['type']}")
        
        # Optimal timing
        if content_data["optimal_time"]:
            console.print(f"⏰ Best times: {content_data['optimal_time']}")
        
        # Schedule recommendation
        if content_data["schedule_recommendation"]:
            console.print(f"📅 Recommended frequency: {content_data['schedule_recommendation']}")


def post_generated_content(content_dict: dict, schedule: bool):
    """Post the generated content to platforms."""
    
    async def post_content():
        connectors = connector_factory.create_all_connectors()
        
        for platform, content_data in content_dict.items():
            if platform in connectors:
                try:
                    post_data = {
                        "text": content_data["text"],
                        "hashtags": content_data["hashtags"]
                    }
                    
                    console.print(f"\n🔄 Posting to {platform}...")
                    result = await connectors[platform].post(post_data)
                    
                    if result.get("status") == "published":
                        console.print(f"✅ {platform}: Posted successfully")
                    else:
                        console.print(f"❌ {platform}: {result.get('error', 'Failed')}")
                        
                except Exception as e:
                    console.print(f"❌ {platform}: {str(e)}")
    
    if schedule:
        console.print("📅 Content scheduled for optimal times")
        # In real implementation, integrate with scheduling system
    else:
        asyncio.run(post_content())


def calculate_maintenance_posting_times(start_time: str) -> dict:
    """Calculate optimal posting times for maintenance notifications."""
    
    # This would parse the start_time and calculate appropriate notification times
    return {
        "24h_before": "2024-01-15 09:00",
        "2h_before": "2024-01-16 07:00", 
        "during": "2024-01-16 09:00",
        "completion": "2024-01-16 11:00"
    }


def create_periodic_schedule(frequency: PostingSchedule, content_types: List[ContentType],
                           platforms: List[str], start_date: Optional[str]) -> dict:
    """Create a periodic posting schedule."""
    
    return {
        "frequency": frequency.value,
        "content_types": [ct.value for ct in content_types],
        "platforms": platforms,
        "start_date": start_date or datetime.now().strftime("%Y-%m-%d"),
        "next_posts": []  # Would be calculated based on frequency
    }


def display_schedule_plan(schedule_plan: dict):
    """Display the periodic schedule plan."""
    
    console.print(f"\n📋 Schedule Plan:")
    console.print(f"  Frequency: {schedule_plan['frequency']}")
    console.print(f"  Content Types: {', '.join(schedule_plan['content_types'])}")
    console.print(f"  Platforms: {', '.join(schedule_plan['platforms'])}")
    console.print(f"  Start Date: {schedule_plan['start_date']}")


def save_periodic_schedule(schedule_plan: dict):
    """Save the periodic schedule configuration."""
    # In real implementation, save to configuration file or database
    pass


def get_content_type_description(content_type: ContentType) -> str:
    """Get human-readable description for content type."""
    
    descriptions = {
        ContentType.ANNOUNCEMENT: "New features, releases, important updates",
        ContentType.MAINTENANCE: "System updates, scheduled downtime notifications",
        ContentType.ENGAGEMENT: "Community questions, discussions, polls",
        ContentType.EDUCATIONAL: "Tutorials, tips, how-to guides",
        ContentType.PROMOTIONAL: "Service highlights, feature showcases",
        ContentType.PERIODIC: "Regular updates, weekly summaries",
        ContentType.BEHIND_SCENES: "Development process, team insights",
        ContentType.COMMUNITY: "User spotlights, success stories",
        ContentType.STATUS: "System status, uptime reports"
    }
    
    return descriptions.get(content_type, "General content")


if __name__ == "__main__":
    content_app()