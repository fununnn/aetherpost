"""Scheduler command for automated posting."""

import typer
import asyncio
import json
from typing import Optional, List
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from pathlib import Path

from ...core.scheduler.scheduler import PostingScheduler
from ...core.scheduler.background import BackgroundScheduler, create_scheduler_daemon, stop_scheduler_daemon
from ...core.scheduler.models import FrequencyType, ScheduleStatus
from ...core.config.parser import ConfigLoader

console = Console()

# Create scheduler app
scheduler_app = typer.Typer(name="scheduler", help="Manage automated posting schedules")


@scheduler_app.command()
def create(
    campaign_config: str = typer.Option("campaign.yaml", "--config", "-c", help="Campaign configuration file"),
    frequency: str = typer.Option("daily", "--frequency", "-f", help="Posting frequency (hourly, daily, weekly)"),
    duration_days: int = typer.Option(30, "--duration", "-d", help="Schedule duration in days"),
    platforms: Optional[List[str]] = typer.Option(None, "--platform", "-p", help="Target platforms"),
    start_time: Optional[str] = typer.Option(None, "--start-time", "-t", help="Start time (HH:MM)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview schedule without saving")
):
    """Create a new posting schedule."""
    
    console.print(Panel(
        "[bold green]Creating Automated Posting Schedule[/bold green]",
        title="📅 Schedule Creation"
    ))
    
    try:
        # Load campaign config
        config_loader = ConfigLoader()
        config = config_loader.load_campaign_config(campaign_config)
        
        # Override config with provided values
        if frequency:
            config.setdefault("content", {})["frequency"] = frequency
        if start_time:
            config.setdefault("content", {})["posting_time"] = start_time
        
        # Get platforms
        if not platforms:
            platforms = config.get("platforms", ["twitter", "bluesky"])
        
        console.print(f"📁 Campaign: {config.get('name', 'Unknown')}")
        console.print(f"🎯 Platforms: {', '.join(platforms)}")
        console.print(f"⏰ Frequency: {frequency}")
        console.print(f"📅 Duration: {duration_days} days")
        
        # Create scheduler
        scheduler = PostingScheduler()
        
        # Create schedule config
        schedule_config = scheduler.create_schedule(campaign_config, platforms)
        
        # Generate scheduled posts
        console.print("\n[bold blue]Generating scheduled posts...[/bold blue]")
        scheduled_posts = scheduler.generate_scheduled_posts(
            schedule_config, 
            campaign_config, 
            platforms, 
            duration_days
        )
        
        if not scheduled_posts:
            console.print("❌ [red]No posts were scheduled[/red]")
            return
        
        # Display schedule preview
        _display_schedule_preview(scheduled_posts)
        
        if dry_run:
            console.print("\n[yellow]Dry run - schedule not saved[/yellow]")
            return
        
        # Confirm creation
        if not typer.confirm("\nCreate this posting schedule?"):
            console.print("❌ [yellow]Schedule creation cancelled[/yellow]")
            return
        
        # Save schedule
        scheduler.save_schedule(scheduled_posts)
        
        console.print(f"\n✅ [green]Created schedule with {len(scheduled_posts)} posts[/green]")
        console.print(f"📝 Schedule saved to: {scheduler.schedule_file}")
        
        # Show next steps
        console.print("\n[bold blue]Next steps:[/bold blue]")
        console.print("• Run `aetherpost scheduler start` to begin automated posting")
        console.print("• Run `aetherpost scheduler status` to monitor progress")
        
    except Exception as e:
        console.print(f"❌ [red]Error creating schedule: {e}[/red]")
        raise typer.Exit(1)


@scheduler_app.command()
def start(
    campaign_config: str = typer.Option("campaign.yaml", "--config", "-c", help="Campaign configuration file"),
    check_interval: int = typer.Option(60, "--interval", "-i", help="Check interval in seconds"),
    daemon: bool = typer.Option(False, "--daemon", "-d", help="Run as background daemon"),
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run in foreground")
):
    """Start the automated posting scheduler."""
    
    if daemon and foreground:
        console.print("❌ [red]Cannot use both --daemon and --foreground[/red]")
        raise typer.Exit(1)
    
    # Check if schedule exists
    scheduler = PostingScheduler()
    scheduled_posts = scheduler.load_schedule()
    
    if not scheduled_posts:
        console.print("❌ [red]No schedule found. Run 'aetherpost scheduler create' first[/red]")
        raise typer.Exit(1)
    
    pending_count = len([p for p in scheduled_posts if p.status == ScheduleStatus.PENDING])
    if pending_count == 0:
        console.print("⚠️  [yellow]No pending posts in schedule[/yellow]")
        if not typer.confirm("Start scheduler anyway?"):
            return
    
    console.print(Panel(
        f"[bold green]Starting Automated Posting Scheduler[/bold green]\n"
        f"📁 Campaign: {campaign_config}\n"
        f"⏰ Check interval: {check_interval} seconds\n"
        f"📝 Pending posts: {pending_count}",
        title="🚀 Scheduler Startup"
    ))
    
    if daemon:
        # Run as daemon
        success = create_scheduler_daemon(
            campaign_file=campaign_config,
            check_interval=check_interval
        )
        
        if success:
            console.print("✅ [green]Scheduler daemon started successfully[/green]")
            console.print("📝 Check logs: .aetherpost/scheduler.log")
            console.print("🛑 Stop with: aetherpost scheduler stop")
        else:
            console.print("❌ [red]Failed to start scheduler daemon[/red]")
            raise typer.Exit(1)
    
    else:
        # Run in foreground
        async def run_foreground():
            background_scheduler = BackgroundScheduler(
                campaign_file=campaign_config,
                check_interval_seconds=check_interval
            )
            
            try:
                console.print("🔄 [blue]Starting scheduler (Press Ctrl+C to stop)[/blue]")
                await background_scheduler.start()
            except KeyboardInterrupt:
                console.print("\n🛑 [yellow]Stopping scheduler...[/yellow]")
                background_scheduler.stop()
                console.print("✅ [green]Scheduler stopped[/green]")
        
        try:
            asyncio.run(run_foreground())
        except KeyboardInterrupt:
            console.print("\n🛑 [yellow]Scheduler interrupted[/yellow]")


@scheduler_app.command()
def stop():
    """Stop the automated posting scheduler daemon."""
    
    console.print(Panel(
        "[bold red]Stopping Automated Posting Scheduler[/bold red]",
        title="🛑 Scheduler Stop"
    ))
    
    success = stop_scheduler_daemon()
    
    if success:
        console.print("✅ [green]Scheduler daemon stopped successfully[/green]")
    else:
        console.print("❌ [red]No running scheduler daemon found[/red]")


@scheduler_app.command()
def status(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed status")
):
    """Show scheduler status and statistics."""
    
    console.print(Panel(
        "[bold blue]Automated Posting Scheduler Status[/bold blue]",
        title="📊 Scheduler Status"
    ))
    
    # Check daemon status
    pid_file = Path(".aetherpost/scheduler.pid")
    daemon_running = False
    daemon_pid = None
    
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                daemon_pid = int(f.read().strip())
            
            import os
            os.kill(daemon_pid, 0)  # Check if process exists
            daemon_running = True
        except (ValueError, OSError):
            daemon_running = False
    
    # Load schedule
    scheduler = PostingScheduler()
    stats = scheduler.get_schedule_stats()
    
    # Display daemon status
    status_table = Table(show_header=False, box=None)
    status_table.add_column("Item", style="cyan", width=20)
    status_table.add_column("Value", style="white")
    
    status_table.add_row("Daemon Status", "🟢 Running" if daemon_running else "🔴 Stopped")
    if daemon_running and daemon_pid:
        status_table.add_row("Process ID", str(daemon_pid))
    
    console.print(status_table)
    
    # Display schedule statistics
    console.print("\n[bold blue]Schedule Statistics:[/bold blue]")
    
    stats_table = Table(show_header=False, box=None)
    stats_table.add_column("Metric", style="cyan", width=20)
    stats_table.add_column("Count", style="white")
    
    stats_table.add_row("Total Posts", str(stats["total_posts"]))
    stats_table.add_row("Pending", f"🟡 {stats['pending']}")
    stats_table.add_row("Completed", f"🟢 {stats['completed']}")
    stats_table.add_row("Failed", f"🔴 {stats['failed']}")
    stats_table.add_row("Paused", f"⏸️  {stats['paused']}")
    
    console.print(stats_table)
    
    # Show next and last posts
    if stats["next_post"]:
        next_time = datetime.fromisoformat(stats["next_post"]["time"])
        console.print(f"\n📅 [bold green]Next Post:[/bold green] {next_time.strftime('%Y-%m-%d %H:%M')} UTC")
        console.print(f"🎯 Platforms: {', '.join(stats['next_post']['platforms'])}")
    
    if stats["last_post"]:
        last_time = datetime.fromisoformat(stats["last_post"]["time"])
        console.print(f"\n📝 [bold blue]Last Post:[/bold blue] {last_time.strftime('%Y-%m-%d %H:%M')} UTC")
        console.print(f"🎯 Platforms: {', '.join(stats['last_post']['platforms'])}")
    
    # Show detailed status if requested
    if detailed:
        _show_detailed_status(scheduler)


@scheduler_app.command()
def pause():
    """Pause all scheduled posts."""
    
    scheduler = PostingScheduler()
    scheduler.pause_schedule()
    
    console.print("⏸️  [yellow]All scheduled posts have been paused[/yellow]")
    console.print("📝 Run 'aetherpost scheduler resume' to continue")


@scheduler_app.command()
def resume():
    """Resume all paused posts."""
    
    scheduler = PostingScheduler()
    scheduler.resume_schedule()
    
    console.print("▶️  [green]All paused posts have been resumed[/green]")


@scheduler_app.command()
def cleanup(
    days_old: int = typer.Option(30, "--days", "-d", help="Remove posts older than this many days"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """Clean up old completed/failed posts."""
    
    scheduler = PostingScheduler()
    
    if not confirm:
        if not typer.confirm(f"Remove posts older than {days_old} days?"):
            console.print("❌ [yellow]Cleanup cancelled[/yellow]")
            return
    
    scheduler.cleanup_old_posts(days_old)
    console.print(f"🗑️  [green]Cleaned up posts older than {days_old} days[/green]")


@scheduler_app.command()
def list(
    status_filter: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (pending, completed, failed, paused)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum posts to show")
):
    """List scheduled posts."""
    
    scheduler = PostingScheduler()
    scheduled_posts = scheduler.load_schedule()
    
    if not scheduled_posts:
        console.print("📭 [yellow]No scheduled posts found[/yellow]")
        return
    
    # Filter by status if specified
    if status_filter:
        try:
            filter_status = ScheduleStatus(status_filter)
            scheduled_posts = [p for p in scheduled_posts if p.status == filter_status]
        except ValueError:
            console.print(f"❌ [red]Invalid status: {status_filter}[/red]")
            console.print("Valid statuses: pending, completed, failed, paused")
            raise typer.Exit(1)
    
    # Sort by scheduled time
    scheduled_posts.sort(key=lambda p: p.scheduled_time)
    
    # Limit results
    if len(scheduled_posts) > limit:
        scheduled_posts = scheduled_posts[:limit]
        show_truncated = True
    else:
        show_truncated = False
    
    # Display posts
    console.print(Panel(
        f"[bold blue]Scheduled Posts{' (filtered)' if status_filter else ''}[/bold blue]",
        title="📝 Post List"
    ))
    
    table = Table()
    table.add_column("Scheduled Time", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Platforms", style="green")
    table.add_column("Attempts", style="yellow")
    
    for post in scheduled_posts:
        status_emoji = {
            ScheduleStatus.PENDING: "🟡",
            ScheduleStatus.COMPLETED: "🟢",
            ScheduleStatus.FAILED: "🔴",
            ScheduleStatus.PAUSED: "⏸️",
            ScheduleStatus.RUNNING: "🔄"
        }.get(post.status, "⚪")
        
        table.add_row(
            post.scheduled_time.strftime("%Y-%m-%d %H:%M"),
            f"{status_emoji} {post.status.value}",
            ", ".join(post.platforms),
            f"{post.attempts}/{post.max_attempts}"
        )
    
    console.print(table)
    
    if show_truncated:
        console.print(f"\n[yellow]Showing first {limit} posts. Use --limit to see more.[/yellow]")


def _display_schedule_preview(scheduled_posts: List):
    """Display a preview of the scheduling."""
    
    console.print(f"\n[bold blue]📅 Schedule Preview ({len(scheduled_posts)} posts):[/bold blue]")
    
    # Group by date
    posts_by_date = {}
    for post in scheduled_posts:
        date_key = post.scheduled_time.date()
        if date_key not in posts_by_date:
            posts_by_date[date_key] = []
        posts_by_date[date_key].append(post)
    
    # Show first 7 days
    dates = sorted(posts_by_date.keys())[:7]
    
    for date in dates:
        day_posts = posts_by_date[date]
        console.print(f"\n📅 {date.strftime('%Y-%m-%d')} ({len(day_posts)} posts)")
        
        for post in day_posts[:3]:  # Show first 3 posts per day
            time_str = post.scheduled_time.strftime('%H:%M')
            platforms_str = ', '.join(post.platforms)
            console.print(f"   ⏰ {time_str} → {platforms_str}")
        
        if len(day_posts) > 3:
            console.print(f"   ... and {len(day_posts) - 3} more posts")
    
    if len(dates) < len(posts_by_date):
        remaining_days = len(posts_by_date) - len(dates)
        console.print(f"\n[yellow]... and {remaining_days} more days[/yellow]")


def _show_detailed_status(scheduler: PostingScheduler):
    """Show detailed scheduler status."""
    
    console.print("\n[bold blue]📋 Detailed Status:[/bold blue]")
    
    scheduled_posts = scheduler.load_schedule()
    
    if not scheduled_posts:
        console.print("No scheduled posts")
        return
    
    # Recent failures
    failed_posts = [p for p in scheduled_posts if p.status == ScheduleStatus.FAILED]
    if failed_posts:
        console.print("\n[bold red]Recent Failures:[/bold red]")
        
        for post in failed_posts[-5:]:  # Show last 5 failures
            console.print(f"🔴 {post.scheduled_time.strftime('%Y-%m-%d %H:%M')} - {post.last_error or 'Unknown error'}")
    
    # Upcoming posts
    pending_posts = [p for p in scheduled_posts if p.status == ScheduleStatus.PENDING]
    upcoming = [p for p in pending_posts if p.scheduled_time > datetime.utcnow()][:5]
    
    if upcoming:
        console.print("\n[bold green]Upcoming Posts:[/bold green]")
        
        for post in upcoming:
            time_until = post.scheduled_time - datetime.utcnow()
            hours_until = int(time_until.total_seconds() / 3600)
            console.print(f"🟡 {post.scheduled_time.strftime('%Y-%m-%d %H:%M')} (in {hours_until}h) - {', '.join(post.platforms)}")
    
    # Platform distribution
    platform_counts = {}
    for post in scheduled_posts:
        for platform in post.platforms:
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    if platform_counts:
        console.print("\n[bold blue]Platform Distribution:[/bold blue]")
        for platform, count in sorted(platform_counts.items()):
            console.print(f"🎯 {platform}: {count} posts")