"""Campaign management commands for seasonal events and marketing campaigns."""

import asyncio
import logging
import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
# from rich.calendar import Calendar  # This module doesn't exist in rich
from rich.progress import Progress, SpinnerColumn, TextColumn

from aetherpost.core.campaigns.templates import (
    CampaignTemplateLibrary, 
    CampaignTemplate, 
    CampaignType, 
    CampaignPhase,
    campaign_library
)
from aetherpost.core.preview.generator import ContentPreviewGenerator
from aetherpost.core.preview.notifiers import notification_manager
import logging
from aetherpost.cli.utils.ui import create_status_panel, print_success, print_error, print_warning

logger = logging.getLogger(__name__)
console = Console()

class CampaignManager:
    """Manage campaign creation, scheduling, and execution."""
    
    def __init__(self):
        self.library = campaign_library
        self.preview_generator = ContentPreviewGenerator()
        self.campaign_dir = Path.cwd() / ".aetherpost" / "campaigns"
        self.campaign_dir.mkdir(parents=True, exist_ok=True)
    
    def create_campaign_from_template(self, template_name: str, campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create campaign configuration from template."""
        template = self.library.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Parse event date
        event_date_str = campaign_config.get("event_date")
        if event_date_str:
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
        else:
            event_date = datetime.now() + timedelta(days=7)  # Default to next week
        
        # Generate schedule
        schedule = template.get_campaign_schedule(event_date)
        
        # Create campaign configuration
        campaign_data = {
            "name": campaign_config.get("campaign_name", template.name),
            "template": template_name,
            "event_date": event_date.isoformat(),
            "created_at": datetime.now().isoformat(),
            "status": "draft",
            "context": campaign_config.get("context", {}),
            "platforms": campaign_config.get("platforms", ["twitter", "instagram"]),
            "schedule": schedule,
            "theme_colors": template.theme_colors,
            "key_hashtags": template.key_hashtags,
            "target_audience": template.target_audience,
            "success_metrics": template.success_metrics,
            "content_pieces": [
                {
                    "phase": content.phase.value,
                    "platform": content.platform,
                    "content_type": content.content_type,
                    "text_template": content.text_template,
                    "hashtags": content.hashtags,
                    "visual_elements": content.visual_elements,
                    "optimal_time": content.optimal_time,
                    "priority": content.priority
                }
                for content in template.content_pieces
            ]
        }
        
        return campaign_data
    
    def save_campaign(self, campaign_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save campaign configuration to file."""
        if not filename:
            safe_name = campaign_data["name"].lower().replace(" ", "_").replace("-", "_")
            filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d')}.yaml"
        
        campaign_file = self.campaign_dir / filename
        
        with open(campaign_file, 'w') as f:
            yaml.dump(campaign_data, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Campaign saved to {campaign_file}")
        return str(campaign_file)
    
    def load_campaign(self, filename: str) -> Dict[str, Any]:
        """Load campaign configuration from file."""
        campaign_file = Path(filename)
        if not campaign_file.exists():
            # Try in campaigns directory
            campaign_file = self.campaign_dir / filename
            if not campaign_file.exists():
                raise FileNotFoundError(f"Campaign file not found: {filename}")
        
        with open(campaign_file, 'r') as f:
            return yaml.safe_load(f)
    
    def list_campaigns(self) -> List[Dict[str, Any]]:
        """List all saved campaigns."""
        campaigns = []
        for campaign_file in self.campaign_dir.glob("*.yaml"):
            try:
                campaign_data = self.load_campaign(str(campaign_file))
                campaigns.append({
                    "filename": campaign_file.name,
                    "name": campaign_data.get("name", "Unknown"),
                    "template": campaign_data.get("template", "custom"),
                    "event_date": campaign_data.get("event_date"),
                    "status": campaign_data.get("status", "draft"),
                    "created_at": campaign_data.get("created_at")
                })
            except Exception as e:
                logger.warning(f"Could not load campaign {campaign_file}: {e}")
        
        return sorted(campaigns, key=lambda x: x.get("created_at", ""))
    
    async def generate_campaign_preview(self, campaign_data: Dict[str, Any], phase: Optional[str] = None) -> None:
        """Generate preview for campaign content."""
        content_items = []
        
        # Filter content by phase if specified
        for content_piece in campaign_data["content_pieces"]:
            if phase and content_piece["phase"] != phase:
                continue
            
            # Format content with context
            context = campaign_data.get("context", {})
            context.update({
                "app_name": context.get("app_name", "AetherPost"),
                "campaign_name": campaign_data["name"]
            })
            
            try:
                formatted_text = content_piece["text_template"].format(**context)
                formatted_hashtags = [
                    tag.format(**context) if "{" in tag else tag 
                    for tag in content_piece["hashtags"]
                ]
            except KeyError as e:
                logger.warning(f"Missing context variable {e}, using template as-is")
                formatted_text = content_piece["text_template"]
                formatted_hashtags = content_piece["hashtags"]
            
            content_items.append({
                "platform": content_piece["platform"],
                "content_type": content_piece["content_type"],
                "text": formatted_text,
                "hashtags": formatted_hashtags,
                "phase": content_piece["phase"],
                "priority": content_piece["priority"]
            })
        
        if not content_items:
            console.print("No content found for preview")
            return
        
        # Create preview session
        session = self.preview_generator.create_preview_session(
            campaign_data["name"],
            content_items
        )
        
        # Display preview
        console.print(Panel(
            f"[bold green]Campaign Preview Generated[/bold green]\n\n"
            f"Campaign: {session.campaign_name}\n"
            f"Phase: {phase or 'All phases'}\n"
            f"Content pieces: {len(session.content_items)}\n"
            f"Estimated reach: {session.total_estimated_reach:,}",
            title="Campaign Preview"
        ))
        
        # Show content breakdown by phase
        phases = {}
        for item in content_items:
            phase_name = item["phase"]
            if phase_name not in phases:
                phases[phase_name] = []
            phases[phase_name].append(item)
        
        for phase_name, phase_items in phases.items():
            console.print(f"\n[bold cyan]Phase: {phase_name.title()}[/bold cyan]")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Platform", style="cyan")
            table.add_column("Content Preview")
            table.add_column("Priority")
            
            for item in sorted(phase_items, key=lambda x: x["priority"]):
                content_preview = item["text"][:80] + "..." if len(item["text"]) > 80 else item["text"]
                priority_display = "🔴 High" if item["priority"] == 1 else "🟡 Medium" if item["priority"] == 2 else "🟢 Low"
                
                table.add_row(
                    item["platform"].title(),
                    content_preview,
                    priority_display
                )
            
            console.print(table)
        
        # Ask if user wants to send preview notifications
        if Confirm.ask("\nSend preview to notification channels?", default=False):
            results = await notification_manager.send_preview_to_all(session)
            
            success_count = sum(1 for r in results.values() if r.get("status") == "success")
            console.print(f"\n📨 Sent to {success_count}/{len(results)} channels")

@click.group(name="campaign")
@click.pass_context
def campaign(ctx):
    """Campaign management for seasonal events and marketing."""
    ctx.ensure_object(dict)
    ctx.obj['manager'] = CampaignManager()

@campaign.command()
@click.option("--template", "-t", help="Template name (use 'list' to see available templates)")
@click.option("--name", "-n", help="Campaign name")
@click.option("--event-date", help="Event date (YYYY-MM-DD)")
@click.option("--app-name", help="Your app/product name")
@click.option("--platforms", "-p", multiple=True, help="Target platforms")
@click.option("--interactive", "-i", is_flag=True, help="Interactive setup wizard")
def init(template, name, event_date, app_name, platforms, interactive):
    """Initialize a new campaign from template."""
    manager = CampaignManager()
    
    if template == "list" or not template:
        # Show available templates
        console.print(Panel(
            "[bold green]Available Campaign Templates[/bold green]",
            title="Templates"
        ))
        
        # Group by type
        seasonal = manager.library.get_seasonal_templates()
        
        if seasonal:
            console.print("\n[bold cyan]🎃 Seasonal Campaigns:[/bold cyan]")
            for tmpl in seasonal:
                console.print(f"  • [green]{tmpl.name.lower().replace(' ', '_')}[/green] - {tmpl.description}")
        
        other_templates = [t for t in manager.library.templates.values() if t.campaign_type != CampaignType.SEASONAL]
        if other_templates:
            console.print("\n[bold cyan]📈 Other Campaigns:[/bold cyan]")
            for tmpl in other_templates:
                console.print(f"  • [green]{tmpl.name.lower().replace(' ', '_')}[/green] - {tmpl.description}")
        
        console.print("\n[yellow]Usage:[/yellow] [cyan]aetherpost campaign init --template halloween --interactive[/cyan]")
        return
    
    if interactive or not all([template, name, event_date, app_name]):
        # Interactive setup
        console.print(Panel(
            "[bold green]Campaign Setup Wizard[/bold green]\n"
            "Let's create your marketing campaign step by step!",
            title="🚀 AetherPost Campaign Creator"
        ))
        
        # Template selection
        if not template:
            console.print("\n[bold]Available Templates:[/bold]")
            templates = list(manager.library.templates.keys())
            for i, tmpl_name in enumerate(templates, 1):
                tmpl = manager.library.get_template(tmpl_name)
                console.print(f"  {i}. [cyan]{tmpl_name}[/cyan] - {tmpl.description}")
            
            while True:
                try:
                    choice = IntPrompt.ask("\nSelect template number", choices=[str(i) for i in range(1, len(templates) + 1)])
                    template = templates[choice - 1]
                    break
                except ValueError:
                    console.print("[red]Invalid choice. Please try again.[/red]")
        
        # Get template info
        template_obj = manager.library.get_template(template)
        console.print(f"\n[green]Selected:[/green] {template_obj.name}")
        console.print(f"[yellow]Description:[/yellow] {template_obj.description}")
        
        # Campaign details
        if not name:
            default_name = f"{template_obj.name} {datetime.now().year}"
            name = Prompt.ask("\nCampaign name", default=default_name)
        
        if not event_date:
            console.print(f"\n[bold]Event Date Selection[/bold]")
            console.print("Enter the main event date for this campaign:")
            
            # Show current date and some suggestions
            today = datetime.now()
            console.print(f"Today: {today.strftime('%Y-%m-%d')}")
            
            # Suggest dates based on template
            if template == "halloween":
                suggested = "2024-10-31"
                console.print(f"Suggested for Halloween: {suggested}")
            elif template == "christmas":
                suggested = "2024-12-25"
                console.print(f"Suggested for Christmas: {suggested}")
            else:
                suggested = (today + timedelta(days=14)).strftime('%Y-%m-%d')
                console.print(f"Suggested (2 weeks from now): {suggested}")
            
            event_date = Prompt.ask("Event date (YYYY-MM-DD)", default=suggested)
        
        if not app_name:
            app_name = Prompt.ask("\nYour app/product name", default="AetherPost")
        
        if not platforms:
            console.print("\n[bold]Platform Selection[/bold]")
            available_platforms = ["twitter", "instagram", "reddit", "linkedin", "youtube", "tiktok"]
            console.print("Available platforms: " + ", ".join(available_platforms))
            platforms_str = Prompt.ask("Select platforms (comma-separated)", default="twitter,instagram")
            platforms = [p.strip() for p in platforms_str.split(",")]
    
    # Create campaign context
    context = {
        "app_name": app_name,
        "campaign_name": name,
        "event_date": event_date
    }
    
    # Add template-specific context
    if template == "halloween":
        context.update({
            "feature_name": Prompt.ask("Halloween feature name", default="Spooky Automation") if interactive else "Halloween Special",
            "feature_description": "Automated social media with Halloween themes"
        })
    elif template == "christmas":
        context.update({
            "feature_name": "Christmas Edition",
            "holiday_message": "Wishing you happy holidays!"
        })
    elif template == "product_launch":
        context.update({
            "product_name": Prompt.ask("Product name", default=app_name) if interactive else app_name,
            "product_description": Prompt.ask("Product description") if interactive else "Amazing new features",
            "product_url": Prompt.ask("Product URL", default="https://github.com/user/repo") if interactive else "#"
        })
    
    # Create campaign configuration
    campaign_config = {
        "campaign_name": name,
        "event_date": event_date,
        "platforms": list(platforms),
        "context": context
    }
    
    try:
        campaign_data = manager.create_campaign_from_template(template, campaign_config)
        
        # Save campaign
        campaign_file = manager.save_campaign(campaign_data)
        
        # Show summary
        console.print(Panel(
            f"[bold green]Campaign Created Successfully! 🎉[/bold green]\n\n"
            f"📝 Name: {campaign_data['name']}\n"
            f"📅 Event Date: {event_date}\n"
            f"📱 Platforms: {', '.join(platforms)}\n"
            f"📊 Content Pieces: {len(campaign_data['content_pieces'])}\n"
            f"💾 Saved to: {Path(campaign_file).name}",
            title="Campaign Summary"
        ))
        
        # Ask if user wants to preview
        if interactive and Confirm.ask("\nGenerate preview now?", default=True):
            async def preview_campaign():
                await manager.generate_campaign_preview(campaign_data)
            
            asyncio.run(preview_campaign())
        
        console.print(f"\n[green]Next steps:[/green]")
        console.print(f"• Review: [cyan]aetherpost campaign preview {Path(campaign_file).name}[/cyan]")
        console.print(f"• Execute: [cyan]aetherpost campaign run {Path(campaign_file).name}[/cyan]")
        console.print(f"• Schedule: [cyan]aetherpost campaign schedule {Path(campaign_file).name}[/cyan]")
        
    except Exception as e:
        print_error(f"Failed to create campaign: {e}")

@campaign.command()
@click.argument("campaign_file", required=False)
@click.option("--phase", help="Preview specific phase only")
def preview(campaign_file, phase):
    """Preview campaign content."""
    manager = CampaignManager()
    
    if not campaign_file:
        # Show available campaigns
        campaigns = manager.list_campaigns()
        if not campaigns:
            console.print("No campaigns found. Create one with: [cyan]aetherpost campaign init[/cyan]")
            return
        
        console.print("[bold]Available Campaigns:[/bold]")
        for i, camp in enumerate(campaigns, 1):
            status_emoji = "✅" if camp["status"] == "active" else "📝" if camp["status"] == "draft" else "⏸️"
            console.print(f"  {i}. {status_emoji} [cyan]{camp['filename']}[/cyan] - {camp['name']}")
        
        choice = IntPrompt.ask("Select campaign number", choices=[str(i) for i in range(1, len(campaigns) + 1)])
        campaign_file = campaigns[choice - 1]["filename"]
    
    try:
        campaign_data = manager.load_campaign(campaign_file)
        
        async def run_preview():
            await manager.generate_campaign_preview(campaign_data, phase)
        
        asyncio.run(run_preview())
        
    except Exception as e:
        print_error(f"Failed to preview campaign: {e}")

@campaign.command()
def list():
    """List all campaigns."""
    manager = CampaignManager()
    campaigns = manager.list_campaigns()
    
    if not campaigns:
        console.print("No campaigns found.")
        console.print("\nCreate your first campaign: [cyan]aetherpost campaign init --interactive[/cyan]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Campaign", style="cyan")
    table.add_column("Template")
    table.add_column("Event Date") 
    table.add_column("Status")
    table.add_column("Created")
    
    for campaign in campaigns:
        status_emoji = "✅" if campaign["status"] == "active" else "📝" if campaign["status"] == "draft" else "⏸️"
        status_display = f"{status_emoji} {campaign['status'].title()}"
        
        # Format dates
        event_date = campaign.get("event_date", "")
        if event_date:
            try:
                event_dt = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                event_date = event_dt.strftime("%Y-%m-%d")
            except:
                pass
        
        created_at = campaign.get("created_at", "")
        if created_at:
            try:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = created_dt.strftime("%m/%d")
            except:
                pass
        
        table.add_row(
            campaign["name"],
            campaign["template"].title(),
            event_date,
            status_display,
            created_at
        )
    
    console.print(table)

@campaign.command()
@click.argument("campaign_file")
@click.option("--phase", help="Run specific phase only")
@click.option("--dry-run", is_flag=True, help="Preview without actually posting")
def run(campaign_file, phase, dry_run):
    """Execute campaign (placeholder for future implementation)."""
    manager = CampaignManager()
    
    try:
        campaign_data = manager.load_campaign(campaign_file)
        
        console.print(Panel(
            f"[bold yellow]Campaign Execution[/bold yellow]\n\n"
            f"Campaign: {campaign_data['name']}\n"
            f"Phase: {phase or 'All phases'}\n"
            f"Mode: {'Dry run' if dry_run else 'Live execution'}",
            title="🚀 Campaign Runner"
        ))
        
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No posts will be published[/yellow]")
        
        # This would integrate with the existing apply/publish system
        console.print("[blue]Campaign execution integration coming soon![/blue]")
        console.print("For now, use the preview function to review content.")
        
    except Exception as e:
        print_error(f"Failed to run campaign: {e}")

@campaign.command()
def templates():
    """Show detailed information about available templates."""
    manager = CampaignManager()
    
    console.print(Panel(
        "[bold green]AetherPost Campaign Templates[/bold green]",
        title="📋 Template Library"
    ))
    
    # Group templates by type
    template_groups = {}
    for template in manager.library.templates.values():
        group = template.campaign_type.value
        if group not in template_groups:
            template_groups[group] = []
        template_groups[group].append(template)
    
    for group_name, templates in template_groups.items():
        console.print(f"\n[bold cyan]{group_name.title()} Campaigns:[/bold cyan]")
        
        for template in templates:
            console.print(f"\n[green]• {template.name}[/green]")
            console.print(f"  Description: {template.description}")
            console.print(f"  Duration: {template.duration_days} days")
            console.print(f"  Content pieces: {len(template.content_pieces)}")
            console.print(f"  Key hashtags: {', '.join(template.key_hashtags[:3])}")
            
            if template.theme_colors:
                color_display = " ".join([f"[{color}]█[/{color}]" for color in template.theme_colors[:3]])
                console.print(f"  Theme colors: {color_display}")

@campaign.command()
@click.option("--month", type=int, help="Month number (1-12)")
@click.option("--year", type=int, help="Year")
def calendar(month, year):
    """Show campaign calendar with seasonal suggestions."""
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    console.print(Panel(
        f"[bold green]Campaign Calendar - {datetime(year, month, 1).strftime('%B %Y')}[/bold green]",
        title="📅 Marketing Calendar"
    ))
    
    # Show calendar - using a table instead since rich doesn't have Calendar
    import calendar
    cal = calendar.monthcalendar(year, month)
    
    table = Table(title=f"{calendar.month_name[month]} {year}")
    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        table.add_column(day, style="cyan", width=4)
    
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append("")
            else:
                row.append(str(day))
        table.add_row(*row)
    
    console.print(table)
    
    # Show seasonal suggestions
    seasonal_suggestions = {
        1: ["new_year", "winter_update"],
        2: ["valentine", "love_your_users"],
        3: ["spring_launch", "international_womens_day"],
        4: ["april_fools", "easter_special"],
        5: ["may_the_fourth", "mothers_day"],
        6: ["fathers_day", "summer_kickoff"],
        7: ["summer_update", "independence_day"],
        8: ["back_to_school_prep", "summer_sale"],
        9: ["back_to_school", "autumn_launch"],
        10: ["halloween", "october_surprise"],
        11: ["thanksgiving", "black_friday"],
        12: ["christmas", "year_end_review"]
    }
    
    suggestions = seasonal_suggestions.get(month, [])
    if suggestions:
        console.print(f"\n[bold yellow]Suggested campaigns for {datetime(year, month, 1).strftime('%B')}:[/bold yellow]")
        for suggestion in suggestions:
            available_template = suggestion in ["halloween", "christmas", "new_year", "product_launch"]
            status = "✅ Available" if available_template else "🔜 Coming soon"
            console.print(f"  • [cyan]{suggestion.replace('_', ' ').title()}[/cyan] - {status}")

if __name__ == "__main__":
    campaign()