"""Quickstart command for new users."""

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()
quickstart_app = typer.Typer()


@quickstart_app.command()
def main(
    skip_setup: bool = typer.Option(False, "--skip-setup", help="Skip authentication setup"),
    example: bool = typer.Option(False, "--example", help="Create example project"),
):
    """Complete quickstart guide for new AetherPost users."""
    
    console.print(Panel(
        "[bold green]🚀 AetherPost Quickstart Guide[/bold green]\n\n"
        "Welcome! This guide will help you set up AetherPost\n"
        "from scratch and make your first post.",
        border_style="green"
    ))
    
    # Step 1: Check if already initialized
    if Path("campaign.yaml").exists():
        console.print("✅ [green]AetherPost already initialized in this directory[/green]")
        if not Confirm.ask("Continue with existing setup?"):
            return
    else:
        # Initialize directory
        console.print("\n[bold]Step 1:[/bold] Initializing workspace...")
        from .init import main as init_main
        
        if example:
            init_main(name="my-awesome-app", template="example")
        else:
            init_main(quick=True)
    
    # Step 2: Authentication setup
    if not skip_setup and not check_credentials():
        console.print("\n[bold]Step 2:[/bold] Setting up authentication...")
        from .setup import wizard_main
        wizard_main()
    
    # Step 3: First campaign plan
    console.print("\n[bold]Step 3:[/bold] Previewing your campaign...")
    try:
        from .plan import main as plan_main
        plan_main()
    except Exception as e:
        console.print(f"⚠️ [yellow]Could not generate preview: {e}[/yellow]")
    
    # Step 4: Execution options
    console.print(Panel(
        "[bold]🎉 You're all set![/bold]\n\n"
        "[bold]What you can do now:[/bold]\n"
        "• [cyan]aetherpost plan[/cyan]     - Preview posts before publishing\n"
        "• [cyan]aetherpost apply[/cyan]    - Execute your campaign\n"
        "• [cyan]aetherpost now \"message\"[/cyan] - Quick post without config\n"
        "• [cyan]aetherpost stats[/cyan]    - View analytics\n\n"
        "[bold]Need help?[/bold]\n"
        "• [cyan]aetherpost --help[/cyan]   - View all commands\n"
        "• [cyan]aetherpost validate[/cyan] - Check configuration\n"
        "• Check the documentation online",
        title="Ready to Launch!",
        border_style="green"
    ))
    
    # Offer to execute first post
    if Confirm.ask("\n🚀 Ready to make your first post?"):
        console.print("\nGreat! Review the preview above and run:")
        console.print("[bold cyan]aetherpost apply[/bold cyan]")


def check_credentials() -> bool:
    """Check if credentials are configured."""
    creds_file = Path(".aetherpost/credentials.yaml")
    return creds_file.exists()


@quickstart_app.command()
def demo():
    """Run a demo campaign with sample data."""
    
    console.print(Panel(
        "[bold blue]🎭 AetherPost Demo Mode[/bold blue]\n\n"
        "This will create and execute a demo campaign\n"
        "using sample data (no real posts will be made).",
        border_style="blue"
    ))
    
    # Create demo configuration
    demo_config = """name: "TaskMaster Pro"
concept: "AI-powered task manager that learns your productivity patterns"
url: "https://taskmaster.app"
platforms: [twitter]
content:
  style: "casual"
  action: "Try it free!"
  hashtags: ["productivity", "AI", "SaaS"]
analytics: true
"""
    
    # Save demo config
    with open("demo-campaign.yaml", "w") as f:
        f.write(demo_config)
    
    console.print("📄 [green]Created demo-campaign.yaml[/green]")
    
    # Generate demo preview
    console.print("\n[bold]Demo Preview:[/bold]")
    demo_content = generate_demo_content()
    
    table = Table(title="Generated Content")
    table.add_column("Platform", style="cyan")
    table.add_column("Content", style="white")
    
    for platform, content in demo_content.items():
        table.add_row(platform, content)
    
    console.print(table)
    
    console.print("\n[bold]Demo State:[/bold]")
    console.print("• Configuration: ✅ Valid")
    console.print("• Content Generation: ✅ Success")
    console.print("• Platforms: ✅ Twitter configured")
    console.print("• Ready for execution: ✅ Yes")
    
    console.print("\n[green]Demo completed![/green] To run with real data:")
    console.print("1. [cyan]aetherpost init[/cyan] - Initialize your own campaign")
    console.print("2. [cyan]aetherpost setup wizard[/cyan] - Configure credentials")
    console.print("3. [cyan]aetherpost apply[/cyan] - Execute real campaign")


def generate_demo_content() -> dict:
    """Generate sample content for demo."""
    return {
        "twitter": "🚀 Introducing TaskMaster Pro - the AI-powered task manager that learns your productivity patterns!\n\nNever miss a deadline again. Smart organization meets intelligent automation.\n\nTry it free! 👉 https://taskmaster.app\n\n#productivity #AI #SaaS",
        "linkedin": "We're excited to announce TaskMaster Pro - a revolutionary AI-powered task management solution.\n\nOur intelligent system learns your work patterns and helps optimize your productivity automatically.\n\nJoin thousands of professionals who've transformed their workflow.\n\nTry it free: https://taskmaster.app"
    }


@quickstart_app.command()
def troubleshoot():
    """Diagnose common setup issues."""
    
    console.print(Panel(
        "[bold yellow]🔧 AetherPost Troubleshooting[/bold yellow]",
        border_style="yellow"
    ))
    
    issues = []
    
    # Check file structure
    console.print("\n[bold]Checking workspace structure...[/bold]")
    
    if not Path(".aetherpost").exists():
        issues.append("Missing .aetherpost directory - Run 'aetherpost init'")
    else:
        console.print("✅ .aetherpost directory exists")
    
    if not Path("campaign.yaml").exists():
        issues.append("Missing campaign.yaml - Run 'aetherpost init'")
    else:
        console.print("✅ campaign.yaml exists")
    
    # Check credentials
    console.print("\n[bold]Checking authentication...[/bold]")
    
    if not Path(".aetherpost/credentials.yaml").exists():
        issues.append("Missing credentials - Run 'aetherpost setup wizard'")
    else:
        console.print("✅ Credentials file exists")
    
    # Check configuration validity
    console.print("\n[bold]Checking configuration...[/bold]")
    
    try:
        from ..config.parser import ConfigLoader
        config_loader = ConfigLoader()
        config = config_loader.load_campaign_config()
        validation_issues = config_loader.validate_config(config)
        
        if validation_issues:
            issues.extend(validation_issues)
        else:
            console.print("✅ Configuration is valid")
    
    except Exception as e:
        issues.append(f"Configuration error: {e}")
    
    # Report results
    if issues:
        console.print("\n[bold red]Issues found:[/bold red]")
        for issue in issues:
            console.print(f"❌ {issue}")
        
        console.print("\n[bold]Quick fixes:[/bold]")
        console.print("• [cyan]aetherpost init[/cyan]        - Initialize workspace")
        console.print("• [cyan]aetherpost setup wizard[/cyan] - Configure authentication")
        console.print("• [cyan]aetherpost validate[/cyan]     - Check configuration")
    else:
        console.print("\n✅ [green]Everything looks good![/green]")
        console.print("Ready to run [cyan]aetherpost apply[/cyan]")