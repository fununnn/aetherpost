"""Main CLI entry point for AetherPost - Terraform-style simplicity."""

import typer
from rich.console import Console

# Import enhanced error handling and UI
from .utils.ui import ui, handle_cli_errors
from ..core.exceptions import AetherPostError, ErrorCode, create_user_friendly_error
from ..core.logging.logger import logger, audit
from ..core.config.unified import config_manager
from .banner import show_banner, show_command_header

from .commands.init import init_main
from .commands.plan import plan_main
from .commands.apply import apply_main
from .commands.destroy import destroy_main
from .commands.profile import profile_app
from .commands.scheduler import scheduler_app

# Create main CLI app
app = typer.Typer(
    name="aetherpost",
    help="🚀 AetherPost - Promotion as Code",
    add_completion=False,
    rich_markup_mode="rich"
)

console = Console()

def version_callback(value: bool):
    """Show version with cool banner."""
    if value:
        from ..version import __version__
        show_banner(version=__version__)
        raise typer.Exit()

@app.callback()
def main_callback(
    version: bool = typer.Option(False, "--version", "-v", callback=version_callback, help="Show version and exit"),
    banner: bool = typer.Option(True, "--banner/--no-banner", help="Show ASCII art banner")
):
    """🚀 AetherPost - Promotion as Code"""
    if banner:
        # Show banner for main command only, not subcommands
        import sys
        if len(sys.argv) == 1:  # No arguments = show help with banner
            show_banner()

# Wrapper functions to add banners
def init_with_banner(
    campaign_name: str = typer.Option(None, "--name", "-n", help="Campaign name"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Interactive setup"),
    platforms: list[str] = typer.Option([], "--platform", "-p", help="Target platforms"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be created")
):
    """Initialize campaign configuration"""
    show_command_header("init", "🎯 Initialize your social media campaign")
    return init_main(campaign_name, interactive, platforms, dry_run)

def plan_with_banner(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file"),
    platform: str = typer.Option(None, "--platform", help="Preview specific platform only"),
    output_format: str = typer.Option("rich", "--format", help="Output format (rich, json, markdown)")
):
    """Preview campaign content"""
    show_command_header("plan", "👀 Preview your campaign content")
    return plan_main(config_file, platform, output_format)

def apply_with_banner(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file"),
    no_scheduler: bool = typer.Option(False, "--no-scheduler", help="Disable automatic scheduler setup"),
    scheduler_interval: int = typer.Option(60, "--interval", help="Scheduler check interval in seconds")
):
    """Execute campaign"""
    show_command_header("apply", "🚀 Execute your campaign")
    return apply_main(config_file, no_scheduler, scheduler_interval)

def destroy_with_banner(
    config_file: str = typer.Option("campaign.yaml", "--config", "-c", help="Configuration file"),
    platform: str = typer.Option(None, "--platform", help="Only delete posts from specific platform"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    no_profile_restore: bool = typer.Option(False, "--no-profile-restore", help="Skip profile restoration after cleanup")
):
    """Delete posted content and clean up campaign resources"""
    show_command_header("destroy", "🗑️ Clean up your campaign")
    return destroy_main(config_file, platform, yes, no_profile_restore)

# Core commands - Terraform-style simplicity
app.command(name="init", help="Initialize campaign configuration")(init_with_banner)
app.command(name="plan", help="Preview campaign content")(plan_with_banner)
app.command(name="apply", help="Execute campaign")(apply_with_banner)
app.command(name="destroy", help="Delete posted content and clean up")(destroy_with_banner)

# Advanced management commands
app.add_typer(profile_app, name="profile", help="Generate and manage social media profiles")
app.add_typer(scheduler_app, name="scheduler", help="Manage automated posting schedules")


# Removed version and status commands to maintain simplicity
# Use: aetherpost init --help for information instead


if __name__ == "__main__":
    app()