"""State management commands."""

import typer
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.json import JSON

from ...core.state.manager import StateManager

console = Console()
state_app = typer.Typer()


@state_app.command("show")
def show_state():
    """Display current campaign state."""
    
    state_manager = StateManager()
    state = state_manager.load_state()
    
    if not state:
        console.print("❌ [red]No active campaign state found[/red]")
        return
    
    # Show state summary
    summary = state_manager.get_state_summary()
    
    console.print(Panel(
        "[bold blue]📊 Campaign State[/bold blue]",
        border_style="blue"
    ))
    
    # Basic info table
    info_table = Table(title="Campaign Information")
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Campaign ID", summary["campaign_id"])
    info_table.add_row("Created", str(summary["created_at"]))
    info_table.add_row("Total Posts", str(summary["total_posts"]))
    info_table.add_row("Successful Posts", str(summary["successful_posts"]))
    info_table.add_row("Platforms", ", ".join(summary["platforms"]))
    info_table.add_row("Total Media", str(summary["total_media"]))
    
    console.print(info_table)
    
    # Posts table
    if state.posts:
        console.print("\n[bold]Posts:[/bold]")
        posts_table = Table()
        posts_table.add_column("Platform", style="cyan")
        posts_table.add_column("Status", style="green")
        posts_table.add_column("URL", style="blue")
        posts_table.add_column("Created", style="dim")
        
        for post in state.posts:
            status_emoji = "✅" if post.status == "published" else "❌"
            posts_table.add_row(
                post.platform,
                f"{status_emoji} {post.status}",
                post.url if post.status == "published" else "N/A",
                post.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(posts_table)
    
    # Analytics
    if summary["analytics"]["total_reach"] > 0:
        console.print("\n[bold]Analytics:[/bold]")
        analytics_table = Table()
        analytics_table.add_column("Metric", style="cyan")
        analytics_table.add_column("Value", style="white")
        
        analytics_table.add_row("Total Reach", str(summary["analytics"]["total_reach"]))
        analytics_table.add_row("Total Engagement", str(summary["analytics"]["total_engagement"]))
        
        console.print(analytics_table)


@state_app.command("refresh")
def refresh_metrics():
    """Refresh metrics from social media platforms."""
    
    console.print(Panel(
        "[bold yellow]🔄 Refreshing Metrics[/bold yellow]",
        border_style="yellow"
    ))
    
    state_manager = StateManager()
    state = state_manager.load_state()
    
    if not state:
        console.print("❌ [red]No active campaign state found[/red]")
        return
    
    # This would refresh metrics from each platform
    console.print("⚠️  [yellow]Metrics refresh feature coming soon![/yellow]")
    console.print("Will update metrics for all published posts automatically.")


@state_app.command("export")
def export_state(
    format: str = typer.Option("json", "--format", help="Export format (json, csv)"),
    output: str = typer.Option("campaign_export", "--output", "-o", help="Output file prefix"),
):
    """Export campaign state to file."""
    
    state_manager = StateManager()
    state = state_manager.load_state()
    
    if not state:
        console.print("❌ [red]No active campaign state found[/red]")
        return
    
    if format == "json":
        filename = f"{output}.json"
        with open(filename, 'w') as f:
            json.dump(state.dict(), f, indent=2, default=str)
        console.print(f"✅ [green]Exported to {filename}[/green]")
    
    elif format == "csv":
        import csv
        filename = f"{output}.csv"
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Platform', 'Post ID', 'URL', 'Created', 'Status', 'Likes', 'Retweets', 'Replies'])
            
            for post in state.posts:
                writer.writerow([
                    post.platform,
                    post.post_id,
                    post.url,
                    post.created_at,
                    post.status,
                    post.metrics.get('likes', 0),
                    post.metrics.get('retweets', 0),
                    post.metrics.get('replies', 0)
                ])
        
        console.print(f"✅ [green]Exported to {filename}[/green]")
    
    else:
        console.print(f"❌ [red]Unsupported format: {format}[/red]")


@state_app.command("clear")
def clear_state():
    """Clear campaign state."""
    
    from rich.prompt import Confirm
    
    if Confirm.ask("⚠️  This will delete all campaign state. Continue?"):
        import os
        if os.path.exists("promo.state.json"):
            os.remove("promo.state.json")
        console.print("✅ [green]Campaign state cleared[/green]")
    else:
        console.print("Operation cancelled.")


@state_app.command("backup")
def backup_state():
    """Create a backup of current state."""
    
    import shutil
    from datetime import datetime
    
    if not os.path.exists("promo.state.json"):
        console.print("❌ [red]No state file to backup[/red]")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"promo.state.backup.{timestamp}.json"
    
    shutil.copy2("promo.state.json", backup_name)
    console.print(f"✅ [green]State backed up to {backup_name}[/green]")


@state_app.command("raw")
def show_raw_state():
    """Show raw state file content."""
    
    state_manager = StateManager()
    state = state_manager.load_state()
    
    if not state:
        console.print("❌ [red]No active campaign state found[/red]")
        return
    
    console.print(Panel(
        "[bold blue]📄 Raw State Data[/bold blue]",
        border_style="blue"
    ))
    
    # Display as formatted JSON
    state_json = JSON(json.dumps(state.dict(), default=str, indent=2))
    console.print(state_json)