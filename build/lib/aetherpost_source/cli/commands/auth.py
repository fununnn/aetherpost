"""Authentication management commands."""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from ...core.config.parser import ConfigLoader
from ...core.config.models import CredentialsConfig
from ...core.security.encryption import APIKeyValidator
from ...plugins.manager import plugin_manager

console = Console()
auth_app = typer.Typer()


@auth_app.command("setup")
def setup_auth(
    platform: str = typer.Option(None, "--platform", help="Setup specific platform"),
):
    """Setup authentication credentials."""
    
    console.print(Panel(
        "[bold blue]🔐 Authentication Setup[/bold blue]",
        border_style="blue"
    ))
    
    config_loader = ConfigLoader()
    
    # Load existing credentials
    try:
        credentials = config_loader.load_credentials()
    except:
        credentials = CredentialsConfig()
    
    if platform:
        setup_platform_auth(platform, credentials, config_loader)
    else:
        setup_all_auth(credentials, config_loader)


def setup_platform_auth(platform: str, credentials: CredentialsConfig, config_loader: ConfigLoader):
    """Setup authentication for a specific platform."""
    
    console.print(f"[bold]Setting up {platform.title()} authentication[/bold]\n")
    
    if platform == "twitter":
        setup_twitter_auth(credentials, config_loader)
    elif platform == "[AI Service]":
        setup_claude_auth(credentials, config_loader)
    elif platform == "openai":
        setup_openai_auth(credentials, config_loader)
    elif platform == "bluesky":
        setup_bluesky_auth(credentials, config_loader)
    else:
        console.print(f"❌ [red]Unknown platform: {platform}[/red]")


def setup_all_auth(credentials: CredentialsConfig, config_loader: ConfigLoader):
    """Setup authentication for all platforms."""
    
    platforms = ["twitter", "[AI Service]", "openai", "bluesky"]
    
    for platform in platforms:
        if Confirm.ask(f"Setup {platform.title()} credentials?"):
            setup_platform_auth(platform, credentials, config_loader)
            console.print()


def setup_twitter_auth(credentials: CredentialsConfig, config_loader: ConfigLoader):
    """Setup Twitter API credentials."""
    
    console.print("Twitter API v2 requires:")
    console.print("• API Key (Consumer Key)")
    console.print("• API Secret (Consumer Secret)")
    console.print("• Access Token")
    console.print("• Access Token Secret")
    console.print("\nGet these from: https://developer.twitter.com/\n")
    
    api_key = Prompt.ask("API Key")
    api_secret = Prompt.ask("API Secret", password=True)
    access_token = Prompt.ask("Access Token")
    access_token_secret = Prompt.ask("Access Token Secret", password=True)
    
    twitter_creds = {
        "api_key": api_key,
        "api_secret": api_secret,
        "access_token": access_token,
        "access_token_secret": access_token_secret
    }
    
    # Validate credentials
    if APIKeyValidator.validate_twitter_keys(twitter_creds):
        credentials.twitter = twitter_creds
        config_loader.save_credentials(credentials)
        console.print("✅ [green]Twitter credentials saved[/green]")
    else:
        console.print("❌ [red]Invalid Twitter credentials format[/red]")


def setup_claude_auth_ai(credentials: CredentialsConfig, config_loader: ConfigLoader):
    """Setup [AI Service] API credentials."""
    
    console.print("[AI Service] API requires:")
    console.print("• API Key (starts with sk-ant-)")
    console.print("\nGet this from: https://ai-provider.com/console")
    
    api_key = Prompt.ask("[AI Service] API Key", password=True)
    
    # Validate key format
    if APIKeyValidator.validate_anthropic_key(api_key):
        credentials.ai_service = {"api_key": api_key}
        config_loader.save_credentials(credentials)
        console.print("✅ [green][AI Service] credentials saved[/green]")
    else:
        console.print("❌ [red]Invalid [AI Service] API key format[/red]")


def setup_openai_auth(credentials: CredentialsConfig, config_loader: ConfigLoader):
    """Setup OpenAI API credentials."""
    
    console.print("OpenAI API requires:")
    console.print("• API Key (starts with sk-)")
    console.print("\nGet this from: https://platform.openai.com/\n")
    
    api_key = Prompt.ask("OpenAI API Key", password=True)
    
    # Validate key format
    if APIKeyValidator.validate_openai_key(api_key):
        credentials.openai = {"api_key": api_key}
        config_loader.save_credentials(credentials)
        console.print("✅ [green]OpenAI credentials saved[/green]")
    else:
        console.print("❌ [red]Invalid OpenAI API key format[/red]")


def setup_bluesky_auth(credentials: CredentialsConfig, config_loader: ConfigLoader):
    """Setup Bluesky credentials."""
    
    console.print("Bluesky requires:")
    console.print("• Handle (e.g., username.bsky.social)")
    console.print("• Password or App Password")
    console.print("\nCreate account at: https://bsky.app/\n")
    
    handle = Prompt.ask("Bluesky Handle")
    password = Prompt.ask("Password", password=True)
    
    bluesky_creds = {
        "handle": handle,
        "password": password
    }
    
    # Validate credentials format
    if APIKeyValidator.validate_bluesky_credentials(bluesky_creds):
        credentials.bluesky = bluesky_creds
        config_loader.save_credentials(credentials)
        console.print("✅ [green]Bluesky credentials saved[/green]")
    else:
        console.print("❌ [red]Invalid Bluesky credentials format[/red]")


@auth_app.command("test")
def test_auth(
    platform: str = typer.Argument(..., help="Platform to test"),
):
    """Test authentication for a platform."""
    
    console.print(Panel(
        f"[bold yellow]🧪 Testing {platform.title()} Authentication[/bold yellow]",
        border_style="yellow"
    ))
    
    config_loader = ConfigLoader()
    
    try:
        credentials = config_loader.load_credentials()
        asyncio.run(test_platform_auth(platform, credentials))
    except Exception as e:
        console.print(f"❌ [red]Error loading credentials: {e}[/red]")


async def test_platform_auth(platform: str, credentials: CredentialsConfig):
    """Test authentication for a specific platform."""
    
    platform_creds = getattr(credentials, platform, None)
    if not platform_creds:
        console.print(f"❌ [red]No credentials found for {platform}[/red]")
        console.print(f"Run [cyan]aetherpost auth setup --platform {platform}[/cyan] first")
        return
    
    try:
        # Load connector and test authentication
        connector = plugin_manager.load_connector(platform, platform_creds)
        
        console.print(f"⠋ Testing {platform} authentication...")
        
        success = await connector.authenticate(platform_creds)
        
        if success:
            console.print(f"✅ [green]{platform.title()} authentication successful[/green]")
        else:
            console.print(f"❌ [red]{platform.title()} authentication failed[/red]")
            console.print("Check your credentials and try again")
    
    except Exception as e:
        console.print(f"❌ [red]Error testing {platform}: {e}[/red]")


@auth_app.command("list")
def list_auth():
    """List configured authentication credentials."""
    
    console.print(Panel(
        "[bold blue]🔑 Authentication Status[/bold blue]",
        border_style="blue"
    ))
    
    config_loader = ConfigLoader()
    
    try:
        credentials = config_loader.load_credentials()
        
        # Create status table
        table = Table(title="Platform Credentials")
        table.add_column("Platform", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="dim")
        
        platforms = ["twitter", "[AI Service]", "openai", "bluesky"]
        
        for platform in platforms:
            platform_creds = getattr(credentials, platform, None)
            
            if platform_creds:
                if platform == "twitter":
                    details = f"API Key: {platform_creds.get('api_key', '')[:10]}..."
                elif platform in ["[AI Service]", "openai"]:
                    details = f"API Key: {platform_creds.get('api_key', '')[:15]}..."
                elif platform == "bluesky":
                    details = f"Handle: {platform_creds.get('handle', '')}"
                else:
                    details = "Configured"
                
                table.add_row(platform.title(), "✅ Configured", details)
            else:
                table.add_row(platform.title(), "❌ Not configured", "Run auth setup")
        
        console.print(table)
    
    except Exception as e:
        console.print(f"❌ [red]Error loading credentials: {e}[/red]")


@auth_app.command("remove")
def remove_auth(
    platform: str = typer.Argument(..., help="Platform to remove credentials for"),
):
    """Remove authentication credentials for a platform."""
    
    if not Confirm.ask(f"Remove {platform} credentials?"):
        console.print("Operation cancelled.")
        return
    
    config_loader = ConfigLoader()
    
    try:
        credentials = config_loader.load_credentials()
        
        # Remove platform credentials
        if hasattr(credentials, platform):
            setattr(credentials, platform, None)
            config_loader.save_credentials(credentials)
            console.print(f"✅ [green]{platform.title()} credentials removed[/green]")
        else:
            console.print(f"❌ [red]No credentials found for {platform}[/red]")
    
    except Exception as e:
        console.print(f"❌ [red]Error removing credentials: {e}[/red]")