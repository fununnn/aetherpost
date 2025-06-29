"""Apply command implementation with new unified platform system."""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

from ...core.config.parser import ConfigLoader
from ...core.content.generator import ContentGenerator
from ...core.state.manager import StateManager
from ...core.preview.notifiers import PreviewNotificationManager, NotificationChannel
from ...core.preview.generator import ContentPreviewGenerator, PreviewSession
from ...platforms.core.platform_factory import platform_factory
from ...platforms.core.base_platform import Content, Profile, ContentType, MediaFile
import requests
import json
from datetime import datetime

console = Console()
apply_app = typer.Typer()


async def send_real_preview_notification(config, platforms, content_items=None):
    """Send real preview notification using the notification system."""
    import os
    
    try:
        # Create notification manager
        notification_manager = PreviewNotificationManager()
        
        # Load notification channels from environment and config
        channels = []
        
        # Add Slack channel if configured
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if slack_webhook and hasattr(config, 'notifications'):
            slack_config = config.notifications.get('channels', {}).get('slack', {})
            if slack_config.get('enabled', False):
                channels.append(NotificationChannel(
                    name="slack",
                    type="slack",
                    webhook_url=slack_webhook,
                    channel_id=slack_config.get('channel', '#dev-updates'),
                    enabled=True
                ))
        
        # Add LINE channel if configured
        line_token = os.getenv('LINE_NOTIFY_TOKEN')
        if line_token and hasattr(config, 'notifications'):
            line_config = config.notifications.get('channels', {}).get('line', {})
            if line_config.get('enabled', False):
                channels.append(NotificationChannel(
                    name="line",
                    type="line",
                    webhook_url=line_token,  # For LINE, webhook_url contains access_token
                    enabled=True
                ))
        
        if not channels:
            console.print("🔕 [yellow]No notification channels configured. Skipping preview notification.[/yellow]")
            return {"status": "skipped", "message": "No channels configured"}
        
        # Create preview session
        preview_generator = ContentPreviewGenerator()
        
        # If content_items not provided, create mock content for preview
        if not content_items:
            content_items = []
            for platform in platforms:
                content_items.append({
                    'platform': platform,
                    'text': f"Sample {platform} content for {config.name}",
                    'character_count': 50,
                    'estimated_reach': 1000
                })
        
        session = preview_generator.create_preview_session(config.name, content_items)
        
        # Send notifications to all channels
        results = {}
        for channel in channels:
            notification_manager.channels = [channel]  # Set single channel
            result = await notification_manager.send_preview_to_channel(session, channel)
            results[channel.name] = result
            
            if result['status'] == 'success':
                console.print(f"✅ [green]Preview sent to {channel.name}[/green]")
            else:
                console.print(f"❌ [red]Failed to send to {channel.name}: {result.get('message', 'Unknown error')}[/red]")
        
        return results
        
    except Exception as e:
        console.print(f"❌ [red]Error sending notifications: {e}[/red]")
        return {"status": "error", "message": str(e)}


def send_preview_notification(config, platforms):
    """Legacy function - now calls real notification system."""
    try:
        # Run async function
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_real_preview_notification(config, platforms))
        loop.close()
        
        # Show summary
        success_count = sum(1 for r in result.values() if isinstance(r, dict) and r.get('status') == 'success')
        total_count = len([r for r in result.values() if isinstance(r, dict)])
        
        if success_count > 0:
            console.print(f"📩 [green]Notification sent to {success_count}/{total_count} channels[/green]")
        else:
            console.print("📩 [yellow]No notifications sent (check configuration)[/yellow]")
            
    except Exception as e:
        console.print(f"📩 [red]Notification error: {e}[/red]")
        console.print("📩 [yellow]Continuing without notifications...[/yellow]")


def apply_main(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file"),
    no_scheduler: bool = typer.Option(False, "--no-scheduler", help="Disable automatic scheduler setup"),
    scheduler_interval: int = typer.Option(60, "--interval", help="Scheduler check interval in seconds"),
):
    """Execute the campaign and post to social media platforms."""
    
    console.print(Panel(
        "[bold green]🚀 Campaign Execution (New Platform System)[/bold green]",
        border_style="green"
    ))
    
    try:
        # Load configuration
        config_loader = ConfigLoader()
        config = config_loader.load_campaign_config(config_file)
        
        # Validate configuration
        issues = config_loader.validate_config(config)
        if issues:
            console.print("❌ [red]Configuration issues found:[/red]")
            for issue in issues:
                console.print(f"  • {issue}")
            return
        
        platforms = config.platforms
        
        # Load credentials
        credentials = config_loader.load_credentials()
        
        # Check notification settings from config
        notification_config = getattr(config, 'notifications', {})
        auto_apply_enabled = notification_config.get('auto_apply', False)
        notifications_enabled = notification_config.get('enabled', True)
        
        # Override settings based on config
        skip_confirm = auto_apply_enabled
        notify = notifications_enabled
        preview = notifications_enabled and not auto_apply_enabled
        
        if auto_apply_enabled:
            console.print("⚡ [yellow]自動実行モード: 設定に基づいて確認なしで実行します[/yellow]")
        
        # Run execution with notification settings
        asyncio.run(execute_campaign_new(config, platforms, credentials, False, skip_confirm, False, notify, preview))
        
        # After successful execution, offer scheduler setup
        _offer_scheduler_setup(config_file, no_scheduler, scheduler_interval, config)
        
    except FileNotFoundError:
        console.print(f"❌ [red]Configuration file not found: {config_file}[/red]")
        console.print("Run [cyan]aetherpost init[/cyan] to create a configuration file.")
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


def _offer_scheduler_setup(config_file: str, no_scheduler: bool, scheduler_interval: int, config):
    """Offer to set up continuous posting scheduler after successful apply."""
    
    # Check if user explicitly disabled scheduler
    if no_scheduler:
        console.print("⏭️  [yellow]Scheduler setup skipped (--no-scheduler flag used)[/yellow]")
        return
    
    # Check if campaign has scheduling settings
    content_config = getattr(config, 'content', {})
    frequency = content_config.get('frequency', 'manual')
    
    console.print("\n" + "="*60)
    console.print(Panel(
        "[bold blue]🔄 Continuous Posting Setup[/bold blue]",
        border_style="blue"
    ))
    
    if frequency != 'manual':
        # Campaign has frequency setting - automatically set up scheduler
        console.print(f"⚡ [yellow]Campaign configured for {frequency} posting - setting up scheduler automatically...[/yellow]")
        _setup_scheduler(config_file, scheduler_interval, config)
    else:
        # Ask user if they want to set up scheduler
        console.print("🤔 [blue]Your campaign is set to manual posting mode.[/blue]")
        console.print("   Would you like to enable continuous automated posting?")
        
        if Confirm.ask("Enable continuous posting?"):
            # Update config to daily posting if user agrees
            console.print("📝 [blue]Setting posting frequency to 'daily'[/blue]")
            from .helper import update_campaign_frequency
            update_campaign_frequency(config_file, 'daily')
            
            # Reload config with updated frequency
            from ...core.config.parser import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load_campaign_config(config_file)
            
            _setup_scheduler(config_file, scheduler_interval, config)
        else:
            console.print("📝 [blue]To enable later:[/blue]")
            console.print("   1. Edit campaign.yaml: set content.frequency to 'daily'")
            console.print("   2. Run: [cyan]aetherpost apply[/cyan] (will auto-setup scheduler)")
            console.print("   Or run manually: [cyan]aetherpost scheduler create && aetherpost scheduler start[/cyan]")


def _setup_scheduler(config_file: str, scheduler_interval: int, config):
    """Set up and start the posting scheduler."""
    
    try:
        from ...core.scheduler.scheduler import PostingScheduler
        from ...core.scheduler.background import create_scheduler_daemon
        
        console.print("📅 [blue]Creating posting schedule...[/blue]")
        
        # Create scheduler and schedule
        scheduler = PostingScheduler()
        schedule_config = scheduler.create_schedule(config_file)
        
        # Get duration from config or default
        content_config = getattr(config, 'content', {})
        duration_days = content_config.get('schedule_duration_days', 30)
        
        # Generate scheduled posts
        scheduled_posts = scheduler.generate_scheduled_posts(
            schedule_config,
            config_file,
            config.platforms,
            duration_days
        )
        
        if not scheduled_posts:
            console.print("❌ [red]Could not create posting schedule[/red]")
            return
        
        # Save schedule
        scheduler.save_schedule(scheduled_posts)
        console.print(f"✅ [green]Created schedule with {len(scheduled_posts)} posts[/green]")
        
        # Ask about starting daemon
        console.print("\n🤖 [blue]Start background posting daemon?[/blue]")
        console.print(f"   This will check for posts every {scheduler_interval} seconds")
        
        if Confirm.ask("Start background daemon?"):
            success = create_scheduler_daemon(
                campaign_file=config_file,
                check_interval=scheduler_interval
            )
            
            if success:
                console.print("🚀 [green]Background posting daemon started![/green]")
                console.print("📊 Monitor with: [cyan]aetherpost scheduler status[/cyan]")
                console.print("🛑 Stop with: [cyan]aetherpost scheduler stop[/cyan]")
                console.print("📝 Logs: [cyan].aetherpost/scheduler.log[/cyan]")
            else:
                console.print("❌ [red]Failed to start daemon[/red]")
        else:
            console.print("📝 [blue]To start later, run: [cyan]aetherpost scheduler start --daemon[/cyan][/blue]")
        
        # Show schedule summary
        from datetime import datetime
        pending_posts = [p for p in scheduled_posts if p.scheduled_time > datetime.utcnow()]
        if pending_posts:
            next_post = min(pending_posts, key=lambda p: p.scheduled_time)
            console.print(f"\n📅 [green]Next post scheduled: {next_post.scheduled_time.strftime('%Y-%m-%d %H:%M')} UTC[/green]")
            console.print(f"🎯 Platforms: {', '.join(next_post.platforms)}")
        
    except Exception as e:
        console.print(f"❌ [red]Error setting up scheduler: {e}[/red]")
        console.print("📝 [blue]Try manual setup: [cyan]aetherpost scheduler create[/cyan][/blue]")


async def execute_campaign_new(config, platforms, credentials, dry_run: bool, skip_confirm: bool, skip_review: bool = False, notify: bool = True, preview: bool = True):
    """Execute campaign across platforms using new unified system."""
    
    # Initialize components
    state_manager = StateManager()
    
    # Load or create campaign state
    state = state_manager.load_state()
    if not state:
        state = state_manager.initialize_campaign(config.name)
    
    # Use content review system
    from ...core.review.content_reviewer import content_reviewer
    
    # Check for campaign-level notification settings
    campaign_notifications = getattr(config, 'notifications', {})
    if campaign_notifications:
        notify = campaign_notifications.get('enabled', notify)
        if campaign_notifications.get('auto_apply', False):
            console.print("⚡ [yellow]自動実行モード有効: 確認なしで投稿を開始します[/yellow]")
            skip_confirm = True
            preview = False
    
    # Default notification settings
    if notify:
        console.print("📱 [yellow]Notifications enabled - will send preview to Slack/LINE before posting[/yellow]")
        
        # Send preview notification
        if preview:
            console.print("📋 [blue]Sending preview notification...[/blue]")
            send_preview_notification(config, platforms)
            
            if not skip_confirm:
                proceed = Confirm.ask("📩 Preview sent to notification channels. Continue with posting?")
                if not proceed:
                    console.print("❌ [yellow]Campaign cancelled by user[/yellow]")
                    return
    
    try:
        # Create content requests for each platform
        content_requests = []
        for platform in platforms:
            content_requests.append({
                "platform": platform,
                "content_type": "promotional",
                "context": {
                    "campaign_config": config,
                    "concept": config.concept,
                    "style": config.content.style if hasattr(config, 'content') else "professional",
                    "hashtags": config.content.hashtags if hasattr(config, 'content') and hasattr(config.content, 'hashtags') else [],
                    "url": getattr(config, 'url', ''),
                    "image": getattr(config, 'image', '')
                }
            })
        
        # Create review session
        session = await content_reviewer.create_review_session(
            campaign_name=config.name,
            content_requests=content_requests,
            auto_approve=skip_review or skip_confirm
        )
        
        # Conduct review if not skipped
        if not skip_review and not skip_confirm and not dry_run:
            session = await content_reviewer.review_session(session)
        
        # Get approved items
        approved_items = session.get_approved_items()
        
        if not approved_items:
            console.print("❌ No content approved for posting")
            return
        
        # Convert to new platform format
        platform_content = {}
        for item in approved_items:
            # Create Content object for new platform system
            content = Content(
                text=item.text,
                hashtags=item.hashtags,
                content_type=ContentType.TEXT,  # Default to text, could be enhanced
                platform_data=item.metadata
            )
            
            # Add media if specified
            if hasattr(item, 'media_requirements') and item.media_requirements:
                # This would need to be enhanced to handle actual media files
                pass
            
            platform_content[item.platform] = content
        
        # Show preview
        show_execution_preview_new(platform_content, config)
        
        if dry_run:
            console.print("\n[yellow]Dry run completed. No posts were published.[/yellow]")
            return
        
        # Execute posting with new platform system
        await execute_posts_new(platform_content, credentials, state_manager)
        
    except Exception as e:
        console.print(f"❌ Campaign execution failed: {e}")
        return


def show_execution_preview_new(platform_content: dict, config):
    """Show preview of content to be posted."""
    
    console.print(Panel(
        "[bold blue]📋 Campaign Preview (New Platform System)[/bold blue]",
        border_style="blue"
    ))
    
    for platform_name, content in platform_content.items():
        console.print(f"\n[bold]{platform_name.title()}[/bold]")
        console.print("─" * 20)
        console.print(content.text)
        
        if content.media:
            console.print(f"📎 Media: {len(content.media)} file(s)")
        
        if content.hashtags:
            console.print(f"🏷️  {' '.join(content.hashtags)}")


async def execute_posts_new(platform_content: dict, credentials, state_manager: StateManager):
    """Execute posts across platforms using new unified platform system."""
    
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        for platform_name, content in platform_content.items():
            task = progress.add_task(f"Posting to {platform_name}...", total=None)
            
            try:
                # Get platform credentials
                platform_creds = getattr(credentials, platform_name, None)
                if not platform_creds:
                    progress.update(task, description=f"❌ No credentials for {platform_name}")
                    results.append({"platform": platform_name, "status": "failed", "error": "No credentials"})
                    continue
                
                # Create platform instance using factory
                try:
                    platform = platform_factory.create_platform(
                        platform_name=platform_name,
                        credentials=platform_creds.__dict__ if hasattr(platform_creds, '__dict__') else platform_creds
                    )
                except Exception as e:
                    progress.update(task, description=f"❌ Failed to create {platform_name} platform")
                    results.append({"platform": platform_name, "status": "failed", "error": f"Platform creation failed: {str(e)}"})
                    continue
                
                # Authenticate
                auth_success = await platform.authenticate()
                if not auth_success:
                    progress.update(task, description=f"❌ Authentication failed for {platform_name}")
                    results.append({"platform": platform_name, "status": "failed", "error": "Authentication failed"})
                    continue
                
                # Validate content
                validation_result = await platform.validate_content(content)
                if not validation_result['is_valid']:
                    error_msg = '; '.join(validation_result['errors'])
                    progress.update(task, description=f"❌ Content validation failed for {platform_name}")
                    results.append({"platform": platform_name, "status": "failed", "error": f"Validation failed: {error_msg}"})
                    continue
                
                # Post content
                result = await platform.post_content(content)
                
                if result.success:
                    progress.update(task, description=f"✅ Posted to {platform_name}")
                    
                    # Record in state
                    state_manager.add_post(
                        platform=platform_name,
                        post_id=result.post_id or "unknown",
                        url=result.post_url or "unknown",
                        content={
                            'text': content.text,
                            'hashtags': content.hashtags,
                            'content_type': content.content_type.value
                        }
                    )
                    
                    results.append({
                        "platform": platform_name,
                        "status": "success",
                        "url": result.post_url,
                        "post_id": result.post_id
                    })
                else:
                    error = result.error_message or "Unknown error"
                    progress.update(task, description=f"❌ Failed to post to {platform_name}")
                    results.append({"platform": platform_name, "status": "failed", "error": error})
                
                # Cleanup platform resources
                await platform.cleanup()
            
            except Exception as e:
                progress.update(task, description=f"❌ Error posting to {platform_name}")
                results.append({"platform": platform_name, "status": "failed", "error": str(e)})
    
    # Show results
    show_execution_results_new(results)


def show_execution_results_new(results: list):
    """Show campaign execution results."""
    
    console.print(Panel(
        "[bold green]✅ Campaign Complete (New Platform System)[/bold green]",
        border_style="green"
    ))
    
    # Create results table
    table = Table(title="📊 Results")
    table.add_column("Platform", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("URL/Error", style="blue")
    
    success_count = 0
    for result in results:
        if result["status"] == "success":
            table.add_row(
                result["platform"],
                "✅ Published",
                result["url"] or "No URL"
            )
            success_count += 1
        else:
            table.add_row(
                result["platform"],
                "❌ Failed",
                result["error"]
            )
    
    console.print(table)
    
    # Summary
    total = len(results)
    if success_count > 0:
        console.print(f"\n🎉 Successfully posted to {success_count}/{total} platforms!")
        console.print("\n💡 Track performance: [cyan]aetherpost stats[/cyan]")
        
        # Show platform info
        console.print("\n📊 Platform System Info:")
        from ...platforms.core.platform_registry import platform_registry
        stats = platform_registry.get_registry_stats()
        console.print(f"   • Available platforms: {stats['total_platforms']}")
        console.print(f"   • Platform implementations: {', '.join(stats['platform_names'])}")
    else:
        console.print(f"\n😞 No posts were successful. Check your credentials and try again.")


# Utility function to get credentials in dict format
def get_platform_credentials(credentials_obj, platform_name: str) -> dict:
    """Get platform credentials as dictionary."""
    platform_creds = getattr(credentials_obj, platform_name, None)
    if not platform_creds:
        return {}
    
    if hasattr(platform_creds, '__dict__'):
        return platform_creds.__dict__
    elif isinstance(platform_creds, dict):
        return platform_creds
    else:
        # Try to convert to dict if possible
        try:
            return vars(platform_creds)
        except:
            return {}


# Function to upgrade avatar generation and profile management
async def execute_avatar_and_profile_updates(config, credentials):
    """Execute avatar generation and profile updates for all platforms."""
    
    console.print(Panel(
        "[bold blue]🎨 Avatar & Profile Management[/bold blue]",
        border_style="blue"
    ))
    
    # Generate avatar if needed
    from ...core.media.avatar_generator import get_or_generate_avatar
    
    # Convert credentials to dictionary format for avatar generator
    creds_dict = {}
    if hasattr(credentials, 'openai') and credentials.openai:
        creds_dict['openai'] = credentials.openai if isinstance(credentials.openai, dict) else credentials.openai.__dict__
    
    avatar_path = await get_or_generate_avatar(config, creds_dict)
    if avatar_path:
        console.print(f"✅ [green]Avatar ready: {avatar_path}[/green]")
    else:
        console.print("⚠️  [yellow]Avatar generation skipped[/yellow]")
    
    for platform_name in config.platforms:
        try:
            platform_creds = getattr(credentials, platform_name, None)
            if not platform_creds:
                continue
            
            # Create platform instance
            platform = platform_factory.create_platform(
                platform_name=platform_name,
                credentials=get_platform_credentials(credentials, platform_name)
            )
            
            # Authenticate
            if not await platform.authenticate():
                console.print(f"❌ Authentication failed for {platform_name}")
                continue
            
            # Create profile from config with generated avatar
            profile = Profile(
                display_name=getattr(config, 'name', None),
                bio=getattr(config, 'description', None),
                website_url=getattr(config, 'url', None),
                avatar_path=avatar_path
            )
            
            # Update profile
            result = await platform.update_profile(profile)
            
            if result.success:
                console.print(f"✅ Updated profile for {platform_name}")
            else:
                console.print(f"❌ Failed to update profile for {platform_name}: {result.error_message}")
            
            await platform.cleanup()
            
        except Exception as e:
            console.print(f"❌ Error updating {platform_name} profile: {e}")


# Export the main function for backward compatibility
def main():
    """Main entry point for apply command."""
    apply_main()


if __name__ == "__main__":
    main()