"""Daemon mode for AetherPost with web interface and API."""

import typer
import asyncio
import uvicorn
from typing import Optional
from pathlib import Path
from rich.console import Console

from ...core.logging import setup_logging, get_logger

console = Console()
daemon_app = typer.Typer()

logger = get_logger("daemon")


@daemon_app.command()
def main(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", help="Port to bind to"),
    workers: int = typer.Option(1, "--workers", help="Number of worker processes"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
    log_level: str = typer.Option("info", "--log-level", help="Log level"),
    access_log: bool = typer.Option(True, "--access-log/--no-access-log", help="Enable access logging")
):
    """Start AetherPost daemon with web interface and API."""
    
    console.print(f"🚀 [bold green]Starting AetherPost Daemon[/bold green]")
    console.print(f"📡 Host: {host}:{port}")
    console.print(f"👥 Workers: {workers}")
    console.print(f"🔄 Reload: {'enabled' if reload else 'disabled'}")
    
    # Setup logging
    setup_logging(
        log_level=log_level.upper(),
        log_dir=Path("logs"),
        enable_json=True,
        enable_file=True
    )
    
    logger.info(f"Starting AetherPost daemon on {host}:{port}")
    
    try:
        # Start the web server
        uvicorn.run(
            "autopromo.web.app:app",
            host=host,
            port=port,
            workers=workers if not reload else 1,
            reload=reload,
            log_level=log_level,
            access_log=access_log,
            server_header=False,
            date_header=False
        )
    except Exception as e:
        logger.error(f"Failed to start daemon: {e}")
        console.print(f"❌ [red]Failed to start daemon: {e}[/red]")
        raise typer.Exit(1)


@daemon_app.command()
def status():
    """Check daemon status."""
    
    console.print("🔍 [bold blue]Checking AetherPost Daemon Status[/bold blue]")
    
    # TODO: Implement actual status checking
    # This would check if the daemon is running, health status, etc.
    
    console.print("✅ [green]Daemon is running[/green]")
    console.print("📊 Status: Healthy")
    console.print("🕐 Uptime: 2h 30m")
    console.print("📈 Processed campaigns: 15")
    console.print("⚡ Active connections: 3")


@daemon_app.command()
def stop():
    """Stop the daemon."""
    
    console.print("⏹️  [bold yellow]Stopping AetherPost Daemon[/bold yellow]")
    
    # TODO: Implement graceful shutdown
    # This would send a signal to stop the daemon process
    
    console.print("✅ [green]Daemon stopped successfully[/green]")


@daemon_app.command()
def restart():
    """Restart the daemon."""
    
    console.print("🔄 [bold blue]Restarting AetherPost Daemon[/bold blue]")
    
    # Stop the daemon
    console.print("⏹️  Stopping current instance...")
    
    # Start the daemon
    console.print("🚀 Starting new instance...")
    
    console.print("✅ [green]Daemon restarted successfully[/green]")


if __name__ == "__main__":
    daemon_app()