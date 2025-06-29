"""Destroy command implementation."""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from ...core.config.parser import ConfigLoader
from ...core.state.manager import StateManager
from ...platforms.core.platform_factory import platform_factory

console = Console()
destroy_app = typer.Typer()


def destroy_main(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file"),
    platform: str = typer.Option(None, "--platform", help="Only delete posts from specific platform"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    no_profile_restore: bool = typer.Option(False, "--no-profile-restore", help="Skip profile restoration after cleanup"),
):
    """Delete posted content and clean up campaign resources."""
    
    console.print(Panel(
        "[bold red]🗑️ Campaign Destruction (New Platform System)[/bold red]",
        border_style="red"
    ))
    
    try:
        # Load state
        state_manager = StateManager()
        state = state_manager.load_state()
        
        if not state:
            console.print("❌ [red]No active campaign state found[/red]")
            return
        
        # Load configuration
        config_loader = ConfigLoader()
        config = config_loader.load_campaign_config(config_file)
        
        # Filter posts by platform if specified
        posts_to_delete = state.posts
        if platform:
            posts_to_delete = [p for p in posts_to_delete if p.platform == platform]
        
        if not posts_to_delete:
            console.print(f"❌ [yellow]No posts found{' for platform ' + platform if platform else ''}[/yellow]")
            return
        
        # Show what will be destroyed
        console.print(f"\n[bold]Posts to be deleted:[/bold]")
        table = Table()
        table.add_column("Platform", style="cyan")
        table.add_column("Post ID", style="blue")
        table.add_column("Content", style="white")
        table.add_column("Posted At", style="green")
        
        for post in posts_to_delete:
            content_preview = post.content.get('text', '')[:50] + "..." if len(post.content.get('text', '')) > 50 else post.content.get('text', '')
            table.add_row(
                post.platform,
                post.post_id,
                content_preview,
                post.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)
        
        # Confirm destruction
        if not yes:
            if not Confirm.ask(f"\n[bold red]Are you sure you want to delete {len(posts_to_delete)} posts?[/bold red]"):
                console.print("❌ [yellow]Operation cancelled[/yellow]")
                return
        
        # Execute destruction
        asyncio.run(execute_destruction(posts_to_delete, config, state_manager, target_platform=platform, no_profile_restore=no_profile_restore))
        
    except FileNotFoundError:
        console.print(f"❌ [red]Configuration file not found: {config_file}[/red]")
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


async def execute_destruction(posts_to_delete, config, state_manager, target_platform=None, no_profile_restore=False):
    """Execute the destruction of posts."""
    
    console.print(f"\n[bold]Deleting {len(posts_to_delete)} posts...[/bold]")
    
    # Load credentials
    config_loader = ConfigLoader()
    credentials = config_loader.load_credentials()
    
    deleted_count = 0
    failed_count = 0
    
    for post in posts_to_delete:
        platform_instance = None
        try:
            # Load platform credentials
            if isinstance(credentials, dict):
                platform_credentials = credentials.get(post.platform, {})
            else:
                platform_credentials = getattr(credentials, post.platform, {})
            
            # Convert to dictionary if needed
            if hasattr(platform_credentials, '__dict__'):
                platform_credentials = platform_credentials.__dict__
            
            if not platform_credentials:
                console.print(f"⚠️  [yellow]No credentials for {post.platform}, skipping post {post.post_id}[/yellow]")
                failed_count += 1
                continue
            
            # Create platform instance using new factory
            try:
                platform_instance = platform_factory.create_platform(
                    platform_name=post.platform,
                    credentials=platform_credentials
                )
            except Exception as e:
                console.print(f"❌ [red]Failed to create {post.platform} platform instance: {e}[/red]")
                failed_count += 1
                continue
            
            # Authenticate platform
            auth_success = await platform_instance.authenticate()
            if not auth_success:
                console.print(f"❌ [red]Authentication failed for {post.platform}[/red]")
                failed_count += 1
                continue
            
            # Delete the post using new platform system
            result = await platform_instance.delete_post(post.post_id)
            success = result.success
            
            if success:
                console.print(f"✅ [green]Deleted {post.platform} post {post.post_id}[/green]")
                deleted_count += 1
                
                # Remove from state
                state_manager.remove_post(post.post_id)
            else:
                console.print(f"❌ [red]Failed to delete {post.platform} post {post.post_id}: {result.error_message or 'Unknown error'}[/red]")
                failed_count += 1
                
        except Exception as e:
            console.print(f"❌ [red]Error deleting {post.platform} post {post.post_id}: {e}[/red]")
            failed_count += 1
        finally:
            # Always cleanup platform resources
            if platform_instance:
                try:
                    await platform_instance.cleanup()
                except Exception as e:
                    console.print(f"⚠️  [yellow]Warning: cleanup failed for {post.platform}: {e}[/yellow]")
    
    # Summary
    console.print(f"\n[bold]Destruction Summary:[/bold]")
    console.print(f"✅ [green]Successfully deleted: {deleted_count} posts[/green]")
    if failed_count > 0:
        console.print(f"❌ [red]Failed to delete: {failed_count} posts[/red]")
    
    # Clean up state if destroying all platforms
    if not target_platform and deleted_count > 0:
        if Confirm.ask("[bold red]Also clear local campaign state?[/bold red]"):
            state_manager.clear_state()
            console.print("🗑️  [green]Local campaign state cleared[/green]")
    
    # Profile restoration (default enabled, unless disabled)
    if not no_profile_restore and deleted_count > 0:
        # Always offer profile restoration after successful cleanup
        console.print("\n[bold blue]🔄 Profile Restoration[/bold blue]")
        console.print("Would you like to restore your profiles to their original state?")
        console.print("This will clear campaign-specific content from your social media profiles.")
        
        if Confirm.ask("Restore profiles to clean state?"):
            await _restore_original_profiles(config, target_platform)
        else:
            console.print("⏭️  [yellow]Profile restoration skipped[/yellow]")
            console.print("💡 [blue]To restore later, run: [cyan]aetherpost destroy --platform <platform>[/cyan][/blue]")


async def _restore_original_profiles(config, target_platform=None):
    """Restore original profiles by clearing campaign-specific content."""
    
    console.print("\n[bold blue]🔄 Profile Restoration[/bold blue]")
    
    # Load credentials
    config_loader = ConfigLoader()
    credentials = config_loader.load_credentials()
    
    # Determine platforms to restore
    platforms_to_restore = [target_platform] if target_platform else config.platforms
    
    for platform_name in platforms_to_restore:
        try:
            # Get platform credentials
            if isinstance(credentials, dict):
                platform_credentials = credentials.get(platform_name, {})
            else:
                platform_credentials = getattr(credentials, platform_name, {})
            
            if hasattr(platform_credentials, '__dict__'):
                platform_credentials = platform_credentials.__dict__
            
            if not platform_credentials:
                console.print(f"⚠️  [yellow]No credentials for {platform_name}, skipping profile restoration[/yellow]")
                continue
            
            # Create platform instance
            platform_instance = platform_factory.create_platform(
                platform_name=platform_name,
                credentials=platform_credentials
            )
            
            # Authenticate
            if not await platform_instance.authenticate():
                console.print(f"❌ [red]Authentication failed for {platform_name}, cannot restore profile[/red]")
                continue
            
            # Create a "clean" profile
            from ...platforms.core.base_platform import Profile
            clean_profile = Profile(
                display_name="",  # Clear display name
                bio="",          # Clear bio
                website_url="",  # Clear website
                location="",     # Clear location
            )
            
            # Update to clean profile
            result = await platform_instance.update_profile(clean_profile)
            
            if result.success:
                console.print(f"✅ [green]Restored {platform_name} profile to clean state[/green]")
            else:
                console.print(f"❌ [red]Failed to restore {platform_name} profile: {result.error_message or 'Unknown error'}[/red]")
            
            # Cleanup
            await platform_instance.cleanup()
            
        except Exception as e:
            console.print(f"❌ [red]Error restoring {platform_name} profile: {e}[/red]")
    
    console.print("🔄 [blue]Profile restoration completed[/blue]")
    console.print("💡 [yellow]Note: Profile restoration clears campaign content but may not restore exact original state[/yellow]")