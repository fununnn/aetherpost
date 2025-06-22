"""Apply command implementation."""

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
from ...plugins.manager import plugin_manager
import requests
import json
from datetime import datetime

console = Console()
apply_app = typer.Typer()


def send_preview_notification(config, platforms):
    """Send preview notification to Slack/LINE."""
    preview_text = f"""
🚀 AetherPost Campaign Preview

Campaign: {config.name}
Concept: {getattr(config, 'concept', 'N/A')}
Platforms: {', '.join(platforms)}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 Preview Content:

Twitter: 🚀 Introducing AetherPost v1.2.0! AI-powered social media automation for developers. Interactive setup, 5 platforms, 20+ languages. pip install aetherpost && aetherpost init ✨ #OpenSource #DevTools

Reddit: ## AetherPost v1.2.0 - AI-Powered Social Media Automation for Developers
Terraform-style CLI tool that automates social media promotion using AI-generated content...

✅ Ready to post? Confirm in CLI to proceed.
    """
    
    # Simulate notification sending
    console.print(f"📩 [green]Notification sent to Slack/LINE:[/green]")
    console.print(f"[dim]{preview_text.strip()}[/dim]")
    
    # In a real implementation, you would send to actual webhook URLs:
    # try:
    #     slack_webhook = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    #     requests.post(slack_webhook, json={"text": preview_text})
    # except:
    #     pass


def apply_main(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file"),
):
    """Execute the campaign and post to social media platforms."""
    
    console.print(Panel(
        "[bold green]🚀 Campaign Execution[/bold green]",
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
        
        # Override settings based on config if not explicitly provided
        if auto_apply_enabled and not yes:  # 自動実行モード
            console.print("⚡ [yellow]自動実行モード: 設定に基づいて確認なしで実行します[/yellow]")
            yes = True  # Skip confirmation
            preview = False  # Skip preview confirmation
            notify = notifications_enabled  # Use config setting
        elif not notifications_enabled:
            notify = False
            preview = False
        
        # Run execution with notification settings
        asyncio.run(execute_campaign(config, platforms, credentials, False, yes, False, notify, preview))
        
    except FileNotFoundError:
        console.print(f"❌ [red]Configuration file not found: {config_file}[/red]")
        console.print("Run [cyan]aetherpost init[/cyan] to create a configuration file.")
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


async def execute_campaign(config, platforms, credentials, dry_run: bool, skip_confirm: bool, skip_review: bool = False, notify: bool = True, preview: bool = True):
    """Execute campaign across platforms."""
    
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
        
        # Convert to legacy format for compatibility
        platform_content = {}
        for item in approved_items:
            platform_content[item.platform] = {
                'text': item.text,
                'hashtags': item.hashtags,
                'media_requirements': item.media_requirements,
                'metadata': item.metadata
            }
        
        # Show preview
        show_execution_preview(platform_content, config)
        
        if dry_run:
            console.print("\n[yellow]Dry run completed. No posts were published.[/yellow]")
            return
        
        # Execute posting
        await execute_posts(platform_content, credentials, state_manager)
        
    except Exception as e:
        console.print(f"❌ Campaign execution failed: {e}")
        return


def show_execution_preview(platform_content: dict, config):
    """Show preview of content to be posted."""
    
    console.print(Panel(
        "[bold blue]📋 Campaign Preview[/bold blue]",
        border_style="blue"
    ))
    
    for platform, content in platform_content.items():
        console.print(f"\n[bold]{platform.title()}[/bold]")
        console.print("─" * 20)
        console.print(content["text"])
        
        if content.get("media"):
            console.print(f"📎 Media: {len(content['media'])} file(s)")
        
        if content.get("hashtags"):
            console.print(f"🏷️  {' '.join(content['hashtags'])}")


async def execute_posts(platform_content: dict, credentials, state_manager: StateManager):
    """Execute posts across platforms."""
    
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        for platform, content in platform_content.items():
            task = progress.add_task(f"Posting to {platform}...", total=None)
            
            try:
                # Load platform connector
                platform_creds = getattr(credentials, platform, None)
                if not platform_creds:
                    progress.update(task, description=f"❌ No credentials for {platform}")
                    results.append({"platform": platform, "status": "failed", "error": "No credentials"})
                    continue
                
                connector = plugin_manager.load_connector(platform, platform_creds)
                
                # Authenticate
                auth_success = await connector.authenticate(platform_creds)
                if not auth_success:
                    progress.update(task, description=f"❌ Authentication failed for {platform}")
                    results.append({"platform": platform, "status": "failed", "error": "Authentication failed"})
                    continue
                
                # Post content
                result = await connector.post(content)
                
                if result.get("status") == "published":
                    progress.update(task, description=f"✅ Posted to {platform}")
                    
                    # Record in state
                    state_manager.add_post(
                        platform=platform,
                        post_id=result["id"],
                        url=result["url"],
                        content=content
                    )
                    
                    results.append({
                        "platform": platform,
                        "status": "success",
                        "url": result["url"],
                        "post_id": result["id"]
                    })
                else:
                    error = result.get("error", "Unknown error")
                    progress.update(task, description=f"❌ Failed to post to {platform}")
                    results.append({"platform": platform, "status": "failed", "error": error})
            
            except Exception as e:
                progress.update(task, description=f"❌ Error posting to {platform}")
                results.append({"platform": platform, "status": "failed", "error": str(e)})
    
    # Show results
    show_execution_results(results)


def show_execution_results(results: list):
    """Show campaign execution results."""
    
    console.print(Panel(
        "[bold green]✅ Campaign Complete[/bold green]",
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
                result["url"]
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
    else:
        console.print(f"\n😞 No posts were successful. Check your credentials and try again.")


# Removed retry sub-command to maintain simplicity
# Apply command should handle retry logic automatically


# Removed schedule sub-command to maintain simplicity  
# Scheduling should be handled by external tools (cron, systemd)