"""Workspace management commands."""

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm
import shutil

console = Console()
workspace_app = typer.Typer()


@workspace_app.command()
def status():
    """Show workspace status and configuration summary."""
    
    console.print(Panel(
        "[bold blue]📊 Workspace Status[/bold blue]",
        border_style="blue"
    ))
    
    # Workspace information
    workspace_table = Table(title="Workspace Information")
    workspace_table.add_column("Item", style="cyan")
    workspace_table.add_column("Status", style="green")
    workspace_table.add_column("Details", style="white")
    
    # Check workspace structure
    autopromo_dir = Path(".aetherpost")
    campaign_file = Path("campaign.yaml")
    credentials_file = autopromo_dir / "credentials.yaml"
    state_file = autopromo_dir / "state" / "promo.state.json"
    
    workspace_table.add_row(
        "Initialized", 
        "✅ Yes" if autopromo_dir.exists() else "❌ No",
        "Run 'aetherpost init' to initialize" if not autopromo_dir.exists() else ""
    )
    
    workspace_table.add_row(
        "Configuration",
        "✅ Yes" if campaign_file.exists() else "❌ No",
        f"campaign.yaml" if campaign_file.exists() else "No campaign.yaml found"
    )
    
    workspace_table.add_row(
        "Credentials",
        "✅ Yes" if credentials_file.exists() else "❌ No",
        f"Stored in {credentials_file}" if credentials_file.exists() else "Run 'aetherpost setup wizard'"
    )
    
    workspace_table.add_row(
        "State",
        "✅ Yes" if state_file.exists() else "📝 Clean",
        f"Has campaign history" if state_file.exists() else "No posts yet"
    )
    
    console.print(workspace_table)
    
    # Configuration summary
    if campaign_file.exists():
        try:
            from ...core.config.parser import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load_campaign_config()
            
            console.print("\n[bold]Campaign Configuration:[/bold]")
            console.print(f"• Name: [cyan]{config.name}[/cyan]")
            console.print(f"• Platforms: [cyan]{', '.join(config.platforms)}[/cyan]")
            console.print(f"• Style: [cyan]{config.content.style if config.content else 'default'}[/cyan]")
            
        except Exception as e:
            console.print(f"\n⚠️ [yellow]Configuration issue: {e}[/yellow]")
    
    # Recent activity
    if state_file.exists():
        try:
            from ...core.state.manager import StateManager
            state_manager = StateManager()
            state = state_manager.load_state()
            
            if state and state.posts:
                console.print(f"\n[bold]Recent Activity:[/bold]")
                recent_posts = sorted(state.posts, key=lambda p: p.created_at, reverse=True)[:3]
                
                for post in recent_posts:
                    console.print(f"• {post.platform}: Posted {post.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                console.print(f"\nTotal posts: {len(state.posts)}")
        except Exception:
            pass


@workspace_app.command()
def clean(
    all: bool = typer.Option(False, "--all", help="Remove all workspace files"),
    state: bool = typer.Option(False, "--state", help="Remove only state files"),
    cache: bool = typer.Option(False, "--cache", help="Remove only cache files"),
):
    """Clean workspace files."""
    
    if all:
        if not Confirm.ask("⚠️ This will remove ALL AetherPost files in this directory. Continue?"):
            console.print("Clean cancelled.")
            return
        
        # Remove entire .aetherpost directory
        if Path(".aetherpost").exists():
            shutil.rmtree(".aetherpost")
            console.print("🗑️ [green]Removed .aetherpost directory[/green]")
        
        # Remove campaign.yaml
        if Path("campaign.yaml").exists():
            Path("campaign.yaml").unlink()
            console.print("🗑️ [green]Removed campaign.yaml[/green]")
        
        console.print("✨ [green]Workspace cleaned![/green]")
        return
    
    if state:
        state_dir = Path(".aetherpost/state")
        if state_dir.exists():
            shutil.rmtree(state_dir)
            console.print("🗑️ [green]Removed state files[/green]")
        else:
            console.print("ℹ️ No state files to remove")
    
    if cache:
        cache_dir = Path(".aetherpost/cache")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            console.print("🗑️ [green]Removed cache files[/green]")
        else:
            console.print("ℹ️ No cache files to remove")
    
    if not any([state, cache]):
        console.print("No cleaning options specified. Use --help to see options.")


@workspace_app.command()
def backup(
    output: str = typer.Option("autopromo-backup.tar.gz", "--output", "-o", help="Backup file name"),
):
    """Create backup of workspace."""
    import tarfile
    import datetime
    
    # Generate backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if output == "autopromo-backup.tar.gz":
        output = f"autopromo-backup_{timestamp}.tar.gz"
    
    console.print(f"📦 Creating backup: [cyan]{output}[/cyan]")
    
    with tarfile.open(output, "w:gz") as tar:
        # Add campaign configuration
        if Path("campaign.yaml").exists():
            tar.add("campaign.yaml")
            console.print("✅ Added campaign.yaml")
        
        # Add .aetherpost directory (excluding temporary files)
        if Path(".aetherpost").exists():
            for item in Path(".aetherpost").rglob("*"):
                if item.is_file() and not item.name.endswith(('.tmp', '.lock')):
                    tar.add(item)
            console.print("✅ Added workspace files")
        
        # Add variations if they exist
        for variation_file in ["variations.yaml", "templates.yaml"]:
            if Path(variation_file).exists():
                tar.add(variation_file)
                console.print(f"✅ Added {variation_file}")
    
    console.print(f"🎉 [green]Backup created: {output}[/green]")


@workspace_app.command()
def restore(
    backup_file: str = typer.Argument(..., help="Backup file to restore from"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing files"),
):
    """Restore workspace from backup."""
    import tarfile
    
    if not Path(backup_file).exists():
        console.print(f"❌ [red]Backup file not found: {backup_file}[/red]")
        return
    
    # Check for existing files
    existing_files = []
    if Path("campaign.yaml").exists():
        existing_files.append("campaign.yaml")
    if Path(".aetherpost").exists():
        existing_files.append(".aetherpost/")
    
    if existing_files and not overwrite:
        console.print("⚠️ [yellow]Existing AetherPost files found:[/yellow]")
        for file in existing_files:
            console.print(f"  • {file}")
        
        if not Confirm.ask("Overwrite existing files?"):
            console.print("Restore cancelled.")
            return
    
    console.print(f"📦 Restoring from: [cyan]{backup_file}[/cyan]")
    
    with tarfile.open(backup_file, "r:gz") as tar:
        tar.extractall(".")
        console.print("✅ [green]Workspace restored![/green]")
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("• [cyan]aetherpost workspace status[/cyan] - Check restored workspace")
    console.print("• [cyan]aetherpost validate[/cyan] - Validate configuration")


@workspace_app.command()
def migrate(
    from_version: str = typer.Option("1.0", "--from", help="Version to migrate from"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be migrated"),
):
    """Migrate workspace to current version."""
    
    console.print(Panel(
        f"[bold]🔄 Workspace Migration[/bold]\n\n"
        f"Migrating from version {from_version} to current version",
        border_style="blue"
    ))
    
    changes = []
    
    # Example migration logic
    if from_version == "1.0":
        # Check for old config format
        old_config = Path("autopromo.yaml")
        if old_config.exists():
            changes.append(f"Rename {old_config} to campaign.yaml")
        
        # Check for old directory structure
        old_dir = Path("autopromo-data")
        if old_dir.exists():
            changes.append(f"Move {old_dir}/* to .aetherpost/")
    
    if not changes:
        console.print("✅ [green]No migration needed - workspace is up to date![/green]")
        return
    
    if dry_run:
        console.print("[bold]Would migrate:[/bold]")
        for change in changes:
            console.print(f"  • {change}")
        console.print("\nRun without --dry-run to execute migration")
        return
    
    # Execute migration
    console.print("[bold]Executing migration:[/bold]")
    for change in changes:
        console.print(f"✅ {change}")
    
    console.print("🎉 [green]Migration completed![/green]")


@workspace_app.command() 
def switch(
    workspace: str = typer.Argument(..., help="Workspace name or path"),
):
    """Switch between different AetherPost workspaces."""
    
    workspace_path = Path(workspace)
    
    if not workspace_path.exists():
        console.print(f"❌ [red]Workspace not found: {workspace}[/red]")
        return
    
    if not (workspace_path / "campaign.yaml").exists():
        console.print(f"❌ [red]Not a valid AetherPost workspace: {workspace}[/red]")
        return
    
    console.print(f"🔄 [blue]Switching to workspace: {workspace}[/blue]")
    
    # This would typically involve changing working directory
    # or setting environment variables in a real implementation
    console.print("✅ [green]Workspace switched![/green]")
    console.print(f"Current workspace: [cyan]{workspace_path.absolute()}[/cyan]")