"""Main CLI entry point for AetherPost."""

import typer
import asyncio
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import enhanced error handling and UI
from .utils.ui import ui, handle_cli_errors, SetupWizard
from ..core.exceptions import AetherPostError, ErrorCode, create_user_friendly_error
from ..core.logging.logger import logger, audit
from ..core.config.unified import config_manager

from .commands.init import init_app
from .commands.plan import plan_app, main as plan_main
from .commands.apply import apply_app, main as apply_main
from .commands.destroy import destroy_app, main as destroy_main
from .commands.state import state_app
from .commands.auth import auth_app
from .commands.setup import setup_app
from .commands.content import content_app

# Create main CLI app
app = typer.Typer(
    name="aetherpost",
    help="🚀 AetherPost - Promotion as Code",
    add_completion=False,
    rich_markup_mode="rich"
)

# Core commands - Terraform-style simplicity
app.add_typer(init_app, name="init", help="Initialize campaign configuration")
app.command(name="plan", help="Preview campaign content")(plan_main)
app.command(name="apply", help="Execute campaign")(apply_main)
app.command(name="destroy", help="Delete posted content and clean up")(destroy_main)
app.add_typer(auth_app, name="auth", help="Manage authentication")

# Doctor command for troubleshooting
from .commands.doctor import doctor_app
app.add_typer(doctor_app, name="doctor", help="Check configuration")

console = Console()


@app.command()
@handle_cli_errors
def version():
    """Show AetherPost version."""
    try:
        from .. import __version__
        version_info = {
            "Version": __version__,
            "Config Dir": str(config_manager.config_dir),
            "Platforms": ", ".join(config_manager.config.get_configured_platforms()) or "None configured",
            "AI Provider": config_manager.config.ai.provider if config_manager.config.ai.is_valid() else "Not configured"
        }
        
        ui.header("AetherPost Version Information", icon="info")
        ui.status_table("System Information", version_info)
        
        logger.info("Version command executed", extra={"version": __version__})
        
    except Exception as e:
        logger.error(f"Failed to get version information: {e}")
        raise


@app.command()
def post(
    message: str = typer.Argument(..., help="Message to post"),
    platforms: Optional[str] = typer.Option(None, "--platforms", "-p", help="Platforms (default: all configured)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Post a message immediately."""
    import asyncio
    from ..core.review.content_reviewer import content_reviewer
    
    ui.header("AetherPost - Quick Post", icon="zap")
    
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",")]
    else:
        from ..core.config.unified import config_manager
        config = config_manager.config
        platform_list = config.get_configured_platforms()
    
    
    # Execute quick post with review
    async def run_quick_post():
        try:
            # Create content requests for each platform
            content_requests = []
            for platform in platform_list:
                content_requests.append({
                    "platform": platform,
                    "content_type": "announcement",
                    "context": {
                        "user_text": message,
                        "hashtags": [],
                        "style": "casual",
                        "quick_post": True
                    }
                })
            
            # Create review session
            session = await content_reviewer.create_review_session(
                campaign_name=f"quick-{message[:15]}",
                content_requests=content_requests,
                auto_approve=yes
            )
            
            # Conduct review if not skipped
            if not yes:
                session = await content_reviewer.review_session(session)
            
            # Get approved items
            approved_items = session.get_approved_items()
            
            if not approved_items:
                ui.warning("No content approved for posting")
                return
            
            # Execute posts
            ui.info(f"Posting to {len(approved_items)} platforms...")
            
            from ..core.connector_factory import connector_factory
            connectors = connector_factory.create_all_connectors()
            
            results = {}
            success_count = 0
            
            for item in approved_items:
                platform = item.platform
                try:
                    from ..core.config.unified import config_manager
                    config = config_manager.config
                    platform_creds = config.get_platform_credentials(platform)
                    
                    if not platform_creds or not platform_creds.is_valid():
                        ui.console.print(f"❌ No credentials for {platform}")
                        continue
                    
                    from ..plugins.manager import plugin_manager
                    connector = plugin_manager.load_connector(platform, platform_creds)
                    
                    # Authenticate
                    auth_success = await connector.authenticate(platform_creds)
                    if not auth_success:
                        ui.console.print(f"❌ Authentication failed for {platform}")
                        continue
                    
                    # Post content
                    post_data = {
                        'text': item.text,
                        'hashtags': item.hashtags
                    }
                    
                    ui.console.print(f"🔄 Posting to {platform}...")
                    result = await connector.post(post_data)
                    
                    if result.get("status") == "published":
                        ui.console.print(f"✅ Posted to {platform}: {result.get('url', 'Success')}")
                        success_count += 1
                        results[platform] = 'success'
                    else:
                        ui.console.print(f"❌ Failed to post to {platform}: {result.get('error', 'Unknown error')}")
                        results[platform] = 'failed'
                
                except Exception as e:
                    ui.console.print(f"❌ Error posting to {platform}: {e}")
                    results[platform] = 'error'
            
            # Summary
            if success_count > 0:
                ui.success(f"Successfully posted to {success_count}/{len(approved_items)} platforms!")
            else:
                ui.error("No posts were successful. Check your credentials and try again.")
            
            return results
            
        except Exception as e:
            logger.error(f"Quick post failed: {e}")
            ui.error(f"Quick post failed: {e}")
    
    asyncio.run(run_quick_post())


@app.command()
def stats():
    """Show campaign analytics."""
    from ..core.state.manager import StateManager
    
    state_manager = StateManager()
    state = state_manager.load_state()
    
    if not state:
        console.print("❌ No active campaign found")
        return
    
    analytics = state_manager.calculate_analytics()
    
    # Create analytics table
    table = Table(title="📊 Campaign Analytics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Total Reach", str(analytics.total_reach))
    table.add_row("Total Engagement", str(analytics.total_engagement))
    table.add_row("Total Posts", str(len(state.posts)))
    table.add_row("Successful Posts", str(len(state_manager.get_successful_posts())))
    
    console.print(table)
    
    # Platform performance
    if analytics.platform_performance:
        console.print("\n[bold]Platform Performance:[/bold]")
        for platform, perf in analytics.platform_performance.items():
            console.print(f"• {platform}: {perf['total_engagement']} engagement from {perf['posts']} posts")


@app.command()
def promote(
    text: str = typer.Argument(..., help="Text content to promote"),
    platforms: str = typer.Option("all", "--platforms", "-p", help="Target platforms (comma-separated)"),
    hashtags: Optional[str] = typer.Option(None, "--hashtags", "--tags", help="Hashtags (comma-separated, # optional)"),
    schedule: Optional[str] = typer.Option(None, "--schedule", "-s", help="Schedule (now, 1h, 2d, etc.)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without posting"),
    skip_review: bool = typer.Option(False, "--skip-review", help="Skip content review phase"),
):
    """Promote content across social media platforms."""
    import asyncio
    from ..core.review.content_reviewer import content_reviewer
    from ..core.content.strategy import ContentType
    
    ui.header("AetherPost - Content Promotion", icon="rocket")
    
    # Parse platforms
    from ..core.config.unified import config_manager
    config = config_manager.config
    
    if platforms == "all":
        platform_list = config.get_configured_platforms()
    else:
        platform_list = [p.strip() for p in platforms.split(",")]
    
    # Parse hashtags
    hashtag_list = []
    if hashtags:
        hashtag_list = [tag.strip() for tag in hashtags.split(',') if tag.strip()]
    
    # Execute promotion with review
    async def run_promotion_with_review():
        try:
            # Create content requests for each platform
            content_requests = []
            for platform in platform_list:
                content_requests.append({
                    "platform": platform,
                    "content_type": "announcement",  # Default content type
                    "context": {
                        "user_text": text,
                        "hashtags": hashtag_list,
                        "schedule": schedule,
                        "dry_run": dry_run
                    }
                })
            
            # Create review session
            session = await content_reviewer.create_review_session(
                campaign_name=f"promote-{text[:20]}",
                content_requests=content_requests,
                auto_approve=skip_review
            )
            
            # Conduct review if not skipped
            if not skip_review and not dry_run:
                session = await content_reviewer.review_session(session)
            
            # Get approved items
            approved_items = session.get_approved_items()
            
            if not approved_items:
                ui.warning("No content approved for posting")
                return
            
            if dry_run:
                ui.info("Dry run mode - showing approved content preview")
                for item in approved_items:
                    ui.console.print(f"\n[cyan]{item.platform}:[/cyan] {item.text}")
                return
            
            # Execute posts for approved content
            ui.info(f"Posting to {len(approved_items)} platforms...")
            
            from ..core.connector_factory import connector_factory
            connectors = connector_factory.create_all_connectors()
            
            results = {}
            for item in approved_items:
                platform = item.platform
                if platform in connectors:
                    try:
                        post_data = {
                            'text': item.text,
                            'hashtags': item.hashtags
                        }
                        
                        ui.console.print(f"🔄 Posting to {platform}...")
                        result = await connectors[platform].post(post_data)
                        
                        if result.get('status') == 'published':
                            ui.console.print(f"✅ {platform}: Posted successfully")
                            results[platform] = 'success'
                        else:
                            ui.console.print(f"❌ {platform}: Failed - {result.get('error', 'Unknown error')}")
                            results[platform] = 'failed'
                            
                    except Exception as e:
                        ui.console.print(f"❌ {platform}: Exception - {str(e)}")
                        results[platform] = 'error'
                else:
                    ui.console.print(f"⚠️  {platform}: Not configured")
                    results[platform] = 'not_configured'
            
            # Summary
            success_count = sum(1 for r in results.values() if r == 'success')
            if success_count > 0:
                ui.success(f"Successfully posted to {success_count}/{len(approved_items)} platforms!")
            else:
                ui.error("No posts were successful. Check your credentials and try again.")
            
            return results
            
        except Exception as e:
            logger.error(f"Promotion failed: {e}")
            ui.error(f"Promotion failed: {e}")
    
    asyncio.run(run_promotion_with_review())


@app.command()
def plugins():
    """List available plugins."""
    from ..plugins.manager import plugin_manager
    
    console.print("[bold]Available Plugins:[/bold]\n")
    
    # Connectors
    connectors = plugin_manager.list_connectors()
    if connectors:
        console.print("[cyan]SNS Connectors:[/cyan]")
        for connector in connectors:
            console.print(f"  • {connector}")
    
    # AI Providers
    ai_providers = plugin_manager.list_ai_providers()
    if ai_providers:
        console.print("\n[cyan]AI Providers:[/cyan]")
        for provider in ai_providers:
            console.print(f"  • {provider}")
    
    # Analytics Providers
    analytics_providers = plugin_manager.list_analytics_providers()
    if analytics_providers:
        console.print("\n[cyan]Analytics Providers:[/cyan]")
        for provider in analytics_providers:
            console.print(f"  • {provider}")


@app.command()
def validate(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file to validate")
):
    """Validate campaign configuration."""
    from ..core.config.parser import ConfigLoader
    
    config_loader = ConfigLoader()
    
    try:
        config = config_loader.load_campaign_config(config_file)
        issues = config_loader.validate_config(config)
        
        if not issues:
            console.print("✅ [green]Configuration is valid![/green]")
        else:
            console.print("❌ [red]Configuration issues found:[/red]")
            for issue in issues:
                console.print(f"  • {issue}")
    
    except FileNotFoundError:
        console.print(f"❌ [red]{config_file} not found. Run 'aetherpost init' first.[/red]")
    except Exception as e:
        console.print(f"❌ [red]Configuration error: {e}[/red]")


async def execute_quick_post(config, skip_confirm: bool):
    """Execute quick post without config file."""
    from ..core.content.generator import ContentGenerator
    from ..core.config.parser import ConfigLoader
    from ..plugins.manager import plugin_manager
    from rich.prompt import Confirm
    
    try:
        # Load credentials
        config_loader = ConfigLoader()
        credentials = config_loader.load_credentials()
        
        # Generate content
        content_generator = ContentGenerator(credentials)
        
        console.print("⠋ Generating content...")
        
        platform_content = {}
        for platform in config.platforms:
            try:
                content = await content_generator.generate_content(config, platform)
                platform_content[platform] = content
            except Exception as e:
                console.print(f"❌ Failed to generate content for {platform}: {e}")
                return
        
        # Show preview
        console.print("\n[bold]Preview:[/bold]")
        for platform, content in platform_content.items():
            console.print(f"\n[cyan]{platform}:[/cyan] {content['text']}")
        
        # Confirm posting
        if not skip_confirm:
            if not Confirm.ask("\n? Post now?"):
                console.print("Quick post cancelled.")
                return
        
        # Execute posts
        console.print("\n⠋ Posting...")
        success_count = 0
        
        for platform, content in platform_content.items():
            try:
                platform_creds = getattr(credentials, platform, None)
                if not platform_creds:
                    console.print(f"❌ No credentials for {platform}")
                    continue
                
                connector = plugin_manager.load_connector(platform, platform_creds)
                
                # Authenticate
                auth_success = await connector.authenticate(platform_creds)
                if not auth_success:
                    console.print(f"❌ Authentication failed for {platform}")
                    continue
                
                # Post content
                result = await connector.post(content)
                
                if result.get("status") == "published":
                    console.print(f"✅ Posted to {platform}: {result['url']}")
                    success_count += 1
                else:
                    console.print(f"❌ Failed to post to {platform}: {result.get('error', 'Unknown error')}")
            
            except Exception as e:
                console.print(f"❌ Error posting to {platform}: {e}")
        
        if success_count > 0:
            console.print(f"\n🎉 Successfully posted to {success_count}/{len(config.platforms)} platforms!")
        else:
            console.print("\n😞 No posts were successful. Check your credentials and try again.")
    
    except Exception as e:
        console.print(f"❌ Error: {e}")


@app.command()
def demo():
    """Run AetherPost demonstration."""
    from .commands.quickstart import demo as demo_main
    demo_main()


@app.command()
def wizard():
    """Step-by-step campaign creation wizard."""
    from .commands.interactive import wizard as wizard_main
    wizard_main()


@app.command()
@handle_cli_errors
def setup():
    """Interactive setup wizard for AetherPost."""
    try:
        ui.header(
            "AetherPost Setup Wizard",
            "Let's configure AetherPost for your needs!",
            "gear"
        )
        
        # Run setup wizard
        wizard = SetupWizard()
        config_data = wizard.run()
        
        if config_data:
            # Update configuration
            config_manager.update_config(config_data)
            config_manager.save_config()
            
            # Log successful setup
            audit("setup_completed", {
                "platforms": config_data.get("platforms", []),
                "ai_provider": config_data.get("ai_provider", "none")
            })
            
            ui.success("Setup completed successfully!")
            ui.info("You can now start using AetherPost commands")
            
    except Exception as e:
        logger.error(f"Setup wizard failed: {e}")
        raise


@app.command()
@handle_cli_errors
def status():
    """Show AetherPost system status."""
    try:
        ui.header("AetherPost System Status", icon="chart")
        
        # System information
        config = config_manager.config
        
        system_info = {
            "Project": config.project_name,
            "Config Valid": "✅" if not config.validate() else "❌",
            "Platforms Configured": len(config.get_configured_platforms()),
            "AI Provider": config.ai.provider if config.ai.is_valid() else "Not configured",
            "Auto-posting": "Enabled" if config.automation.auto_post else "Disabled",
            "Debug Mode": "Enabled" if config.debug else "Disabled"
        }
        
        ui.status_table("System Status", system_info)
        
        # Platform status
        if config.get_configured_platforms():
            ui.console.print("\n[bold]📱 Platform Status:[/bold]")
            for platform in config.get_configured_platforms():
                creds = config.get_platform_credentials(platform)
                status_icon = "✅" if creds and creds.is_valid() else "❌"
                ui.console.print(f"  {status_icon} {platform.title()}")
        
        # Configuration issues
        issues = config.validate()
        if issues:
            ui.warning("Configuration Issues Found:")
            for issue in issues:
                ui.console.print(f"  • {issue}")
        
        logger.info("Status command executed")
        
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise


if __name__ == "__main__":
    app()