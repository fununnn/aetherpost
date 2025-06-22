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

# Create main CLI app
app = typer.Typer(
    name="aetherpost",
    help="🚀 AetherPost - Promotion as Code",
    add_completion=False,
    rich_markup_mode="rich"
)

# Core commands - Terraform-style simplicity (4 commands only)
app.command(name="init", help="Initialize campaign configuration")(init_main)
app.command(name="plan", help="Preview campaign content")(plan_main)
app.command(name="apply", help="Execute campaign")(apply_main)
app.command(name="destroy", help="Delete posted content and clean up")(destroy_main)

console = Console()


# Removed version and status commands to maintain simplicity
# Use: aetherpost init --help for information instead


if __name__ == "__main__":
    app()