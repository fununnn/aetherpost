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
from ...platforms.core.platform_factory import platform_factory
from ...platforms.core.base_platform import Content, Profile, ContentType, MediaFile
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
        
    except FileNotFoundError:
        console.print(f"❌ [red]Configuration file not found: {config_file}[/red]")
        console.print("Run [cyan]aetherpost init[/cyan] to create a configuration file.")
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


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