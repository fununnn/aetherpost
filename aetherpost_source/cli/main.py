"""Main CLI entry point for AetherPost - Terraform-style simplicity."""

import typer
from rich.console import Console

# Import enhanced error handling and UI
from .utils.ui import ui, handle_cli_errors
from ..core.exceptions import AetherPostError, ErrorCode, create_user_friendly_error
from ..core.logging.logger import logger, audit
from ..core.config.unified import config_manager

from .commands.init import init_app
from .commands.plan import plan_app, main as plan_main
from .commands.apply import apply_app, main as apply_main
from .commands.destroy import destroy_app, main as destroy_main
from .commands.auth import auth_app

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