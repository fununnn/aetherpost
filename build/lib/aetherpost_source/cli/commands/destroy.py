"""Destroy command implementation."""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from ...core.config.parser import ConfigLoader
from ...core.state.manager import StateManager
from ...plugins.manager import plugin_manager

console = Console()
destroy_app = typer.Typer()


def destroy_main(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file"),
):
    """Delete posted content and clean up campaign resources."""
    
    console.print(Panel(
        "[bold red]🗑️ Campaign Destruction[/bold red]",
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
        asyncio.run(execute_destruction(posts_to_delete, config, state_manager, platform))
        
    except FileNotFoundError:
        console.print(f"❌ [red]Configuration file not found: {config_file}[/red]")
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


async def execute_destruction(posts_to_delete, config, state_manager, target_platform=None):
    """Execute the destruction of posts."""
    
    console.print(f"\n[bold]Deleting {len(posts_to_delete)} posts...[/bold]")
    
    # Load credentials
    config_loader = ConfigLoader()
    credentials = config_loader.load_credentials()
    
    deleted_count = 0
    failed_count = 0
    
    for post in posts_to_delete:
        try:
            # Load platform connector
            platform_credentials = getattr(credentials, post.platform, {})
            if not platform_credentials:
                console.print(f"⚠️  [yellow]No credentials for {post.platform}, skipping post {post.post_id}[/yellow]")
                failed_count += 1
                continue
            
            connector = plugin_manager.load_connector(post.platform, platform_credentials)
            
            # Delete the post
            success = await connector.delete(post.post_id)
            
            if success:
                console.print(f"✅ [green]Deleted {post.platform} post {post.post_id}[/green]")
                deleted_count += 1
                
                # Remove from state
                state_manager.remove_post(post.post_id)
            else:
                console.print(f"❌ [red]Failed to delete {post.platform} post {post.post_id}[/red]")
                failed_count += 1
                
        except Exception as e:
            console.print(f"❌ [red]Error deleting {post.platform} post {post.post_id}: {e}[/red]")
            failed_count += 1
    
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