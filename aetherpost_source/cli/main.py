"""Main CLI entry point for AetherPost - Terraform-style simplicity."""

import typer
from rich.console import Console

# Import enhanced error handling and UI
from .utils.ui import ui, handle_cli_errors
from ..core.exceptions import AetherPostError, ErrorCode, create_user_friendly_error
from ..core.logging.logger import logger, audit
from ..core.config.unified import config_manager

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

# Core commands - Terraform-style simplicity
app.command(name="init", help="Initialize campaign configuration")(init_main)
app.command(name="plan", help="Preview campaign content")(plan_main)
app.command(name="apply", help="Execute campaign")(apply_main)
app.command(name="destroy", help="Delete posted content and clean up")(destroy_main)

# Advanced management commands
app.add_typer(profile_app, name="profile", help="Generate and manage social media profiles")
app.add_typer(scheduler_app, name="scheduler", help="Manage automated posting schedules")

console = Console()


# Removed version and status commands to maintain simplicity
# Use: aetherpost init --help for information instead


if __name__ == "__main__":
    app()