"""AI-specific commands and configuration."""

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
import asyncio

console = Console()
ai_app = typer.Typer()


@ai_app.command()
def providers():
    """List available AI providers and their status."""
    
    console.print(Panel(
        "[bold blue]🤖 AI Providers[/bold blue]",
        border_style="blue"
    ))
    
    providers_table = Table(title="Available AI Providers")
    providers_table.add_column("Provider", style="cyan")
    providers_table.add_column("Status", style="green")
    providers_table.add_column("Features", style="white")
    providers_table.add_column("Cost", style="yellow")
    
    # Check provider availability
    from ...plugins.manager import plugin_manager
    
    provider_info = [
        {
            "name": "[AI Service]",
            "features": "Text generation, context-aware",
            "cost": "Pay per token",
            "available": check_provider_credentials("[AI Service]")
        },
        {
            "name": "openai",
            "features": "Text + image generation",
            "cost": "Pay per token/image",
            "available": check_provider_credentials("openai")
        }
    ]
    
    for provider in provider_info:
        status = "✅ Ready" if provider["available"] else "❌ Not configured"
        providers_table.add_row(
            provider["name"].title(),
            status,
            provider["features"],
            provider["cost"]
        )
    
    console.print(providers_table)
    
    console.print("\n[bold]Configuration:[/bold]")
    console.print("• [cyan]aetherpost ai configure[/cyan] - Set up AI providers")
    console.print("• [cyan]aetherpost ai test[/cyan] - Test AI generation")
    console.print("• [cyan]aetherpost ai prompts[/cyan] - Manage custom prompts")


@ai_app.command()
def configure(
    provider: str = typer.Option(None, "--provider", help="Specific provider to configure"),
):
    """Configure AI provider credentials and settings."""
    
    console.print(Panel(
        "[bold green]🔧 AI Provider Configuration[/bold green]",
        border_style="green"
    ))
    
    if provider:
        configure_single_provider(provider)
    else:
        configure_all_providers()


def configure_all_providers():
    """Configure all AI providers interactively."""
    
    console.print("Let's set up your AI providers for content generation.\n")
    
    # [AI Service] configuration
    if Confirm.ask("Configure [AI Service] (Anthropic)?", default=True):
        configure_claude_ai()
    
    # OpenAI configuration
    if Confirm.ask("\nConfigure OpenAI (GPT + DALL-E)?"):
        configure_openai()
    
    console.print("\n✅ [green]AI configuration completed![/green]")
    console.print("Test your setup with: [cyan]aetherpost ai test[/cyan]")


def configure_single_provider(provider_name: str):
    """Configure a specific AI provider."""
    
    if provider_name.lower() == "[AI Service]":
        configure_claude_ai()
    elif provider_name.lower() == "openai":
        configure_openai()
    else:
        console.print(f"❌ [red]Unknown provider: {provider_name}[/red]")
        console.print("Available providers: [AI Service], openai")


def configure_claude():
    """Configure [AI Service] API credentials."""
    
    console.print("[bold cyan][AI Service] (Anthropic) Configuration[/bold cyan]")
    console.print("You'll need an API key from: https://ai-provider.com/console")
    
    api_key = Prompt.ask("[AI Service] API key", password=True)
    
    if not api_key.startswith("sk-ant-"):
        console.print("⚠️ [yellow]Warning: [AI Service] API keys usually start with 'sk-ant-'[/yellow]")
    
    # Test the API key
    if Confirm.ask("Test the API key now?", default=True):
        if test_claude_connection_ai(api_key):
            console.print("✅ [green][AI Service] connection successful![/green]")
        else:
            console.print("❌ [red][AI Service] connection failed. Please check your API key.[/red]")
            return
    
    # Save credentials
    save_ai_credentials("[AI Service]", {"api_key": api_key})
    console.print("💾 [green][AI Service] credentials saved[/green]")


def configure_openai():
    """Configure OpenAI API credentials."""
    
    console.print("[bold cyan]OpenAI Configuration[/bold cyan]")
    console.print("You'll need an API key from: https://platform.openai.com/api-keys")
    
    api_key = Prompt.ask("OpenAI API key", password=True)
    
    if not api_key.startswith("sk-"):
        console.print("⚠️ [yellow]Warning: OpenAI API keys usually start with 'sk-'[/yellow]")
    
    # Test the API key
    if Confirm.ask("Test the API key now?", default=True):
        if test_openai_connection(api_key):
            console.print("✅ [green]OpenAI connection successful![/green]")
        else:
            console.print("❌ [red]OpenAI connection failed. Please check your API key.[/red]")
            return
    
    # Save credentials
    save_ai_credentials("openai", {"api_key": api_key})
    console.print("💾 [green]OpenAI credentials saved[/green]")


@ai_app.command()
def test(
    provider: str = typer.Option(None, "--provider", help="Test specific provider"),
    prompt: str = typer.Option("Test message", "--prompt", help="Test prompt"),
):
    """Test AI provider connections and generation."""
    
    console.print(Panel(
        "[bold yellow]🧪 AI Provider Testing[/bold yellow]",
        border_style="yellow"
    ))
    
    if provider:
        test_single_provider(provider, prompt)
    else:
        test_all_providers(prompt)


def test_all_providers(prompt: str):
    """Test all configured AI providers."""
    
    console.print(f"Testing AI generation with prompt: [cyan]'{prompt}'[/cyan]\n")
    
    # Test [AI Service]
    if check_provider_credentials("[AI Service]"):
        console.print("[bold][AI Service] Test:[/bold]")
        test_claude_generation(prompt)
    else:
        console.print("[dim][AI Service]: Not configured[/dim]")
    
    # Test OpenAI
    if check_provider_credentials("openai"):
        console.print("\n[bold]OpenAI Test:[/bold]")
        test_openai_generation(prompt)
    else:
        console.print("\n[dim]OpenAI: Not configured[/dim]")


def test_single_provider(provider_name: str, prompt: str):
    """Test a specific AI provider."""
    
    console.print(f"Testing {provider_name} with prompt: [cyan]'{prompt}'[/cyan]\n")
    
    if provider_name.lower() == "[AI Service]":
        if check_provider_credentials("[AI Service]"):
            test_claude_generation(prompt)
        else:
            console.print("❌ [red][AI Service] not configured. Run 'aetherpost ai configure --provider [AI Service]'[/red]")
    
    elif provider_name.lower() == "openai":
        if check_provider_credentials("openai"):
            test_openai_generation(prompt)
        else:
            console.print("❌ [red]OpenAI not configured. Run 'aetherpost ai configure --provider openai'[/red]")
    
    else:
        console.print(f"❌ [red]Unknown provider: {provider_name}[/red]")


@ai_app.command()
def prompts():
    """Manage custom AI prompts and templates."""
    
    console.print(Panel(
        "[bold purple]📝 AI Prompt Management[/bold purple]",
        border_style="purple"
    ))
    
    prompts_table = Table(title="Available Prompt Templates")
    prompts_table.add_column("Name", style="cyan")
    prompts_table.add_column("Description", style="white")
    prompts_table.add_column("Style", style="green")
    
    # Built-in prompts
    builtin_prompts = get_builtin_prompts()
    for prompt in builtin_prompts:
        prompts_table.add_row(
            prompt["name"],
            prompt["description"],
            prompt["style"]
        )
    
    console.print(prompts_table)
    
    console.print("\n[bold]Commands:[/bold]")
    console.print("• [cyan]aetherpost ai prompts create[/cyan] - Create custom prompt")
    console.print("• [cyan]aetherpost ai prompts edit <name>[/cyan] - Edit prompt")
    console.print("• [cyan]aetherpost ai prompts test <name>[/cyan] - Test prompt")


@ai_app.command()
def usage():
    """Show AI usage statistics and costs."""
    
    console.print(Panel(
        "[bold magenta]📊 AI Usage Statistics[/bold magenta]",
        border_style="magenta"
    ))
    
    # This would connect to actual usage tracking
    usage_table = Table(title="AI Usage (Last 30 Days)")
    usage_table.add_column("Provider", style="cyan")
    usage_table.add_column("Requests", style="white")
    usage_table.add_column("Tokens", style="yellow")
    usage_table.add_column("Est. Cost", style="green")
    
    # Mock data - in real implementation, this would come from usage tracking
    usage_data = [
        {"provider": "[AI Service]", "requests": 42, "tokens": "15.2K", "cost": "$2.15"},
        {"provider": "OpenAI", "requests": 28, "tokens": "8.7K", "cost": "$1.85"}
    ]
    
    for data in usage_data:
        usage_table.add_row(
            data["provider"],
            str(data["requests"]),
            data["tokens"],
            data["cost"]
        )
    
    console.print(usage_table)
    
    console.print("\n[bold]Cost Optimization Tips:[/bold]")
    console.print("• Use shorter, more focused prompts")
    console.print("• Choose the right model for your needs")
    console.print("• Enable caching for repeated content")
    console.print("• Monitor usage regularly")


# Helper functions

def check_provider_credentials(provider: str) -> bool:
    """Check if provider credentials are configured."""
    try:
        from ...core.config.parser import ConfigLoader
        config_loader = ConfigLoader()
        credentials = config_loader.load_credentials()
        
        if provider == "[AI Service]":
            return hasattr(credentials, 'ai_service') and credentials.ai_service
        elif provider == "openai":
            return hasattr(credentials, 'openai') and credentials.openai
        
        return False
    except Exception:
        return False


def test_claude_connection(api_key: str) -> bool:
    """Test [AI Service] API connection."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test message
        message = client.messages.create(
            model="ai-model-lite-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'OK'"}]
        )
        return "OK" in message.content[0].text
    except Exception:
        return False


def test_openai_connection(api_key: str) -> bool:
    """Test OpenAI API connection."""
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # Simple test completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5
        )
        return "OK" in response.choices[0].message.content
    except Exception:
        return False


def test_claude_generation(prompt: str):
    """Test [AI Service] text generation."""
    try:
        console.print("⠋ Testing [AI Service]...")
        
        from ...core.config.parser import ConfigLoader
        
        config_loader = ConfigLoader()
        credentials = config_loader.load_credentials()
        
        provider = ClaudeProvider(credentials.claude.api_key)
        
        # Run async function
        result = asyncio.run(provider.generate_text(
            f"Create a short social media post about: {prompt}",
            {"max_tokens": 100}
        ))
        
        console.print(f"✅ [green][AI Service] result:[/green] {result}")
    
    except Exception as e:
        console.print(f"❌ [red][AI Service] test failed: {e}[/red]")


def test_openai_generation(prompt: str):
    """Test OpenAI text generation."""
    try:
        console.print("⠋ Testing OpenAI...")
        
        from ...plugins.ai_providers.openai.provider import OpenAIProvider
        from ...core.config.parser import ConfigLoader
        
        config_loader = ConfigLoader()
        credentials = config_loader.load_credentials()
        
        provider = OpenAIProvider(credentials.openai.api_key)
        
        # Run async function
        result = asyncio.run(provider.generate_text(
            f"Create a short social media post about: {prompt}",
            {"max_tokens": 100}
        ))
        
        console.print(f"✅ [green]OpenAI result:[/green] {result}")
    
    except Exception as e:
        console.print(f"❌ [red]OpenAI test failed: {e}[/red]")


def save_ai_credentials(provider: str, credentials: dict):
    """Save AI provider credentials."""
    try:
        from ...core.config.parser import ConfigLoader
        config_loader = ConfigLoader()
        
        # Load existing credentials
        try:
            existing_creds = config_loader.load_credentials()
        except Exception:
            from ...core.config.models import CredentialsConfig
            existing_creds = CredentialsConfig()
        
        # Update provider credentials
        if provider == "[AI Service]":
            from ...core.config.models import ClaudeCredentials
            existing_creds.claude = ClaudeCredentials(**credentials)
        elif provider == "openai":
            from ...core.config.models import OpenAICredentials
            existing_creds.openai = OpenAICredentials(**credentials)
        
        # Save updated credentials
        config_loader.save_credentials(existing_creds)
    
    except Exception as e:
        console.print(f"❌ [red]Failed to save credentials: {e}[/red]")


def get_builtin_prompts():
    """Get list of built-in prompt templates."""
    return [
        {
            "name": "casual",
            "description": "Friendly, approachable tone with emojis",
            "style": "casual"
        },
        {
            "name": "professional",
            "description": "Business-focused, formal language",
            "style": "professional"
        },
        {
            "name": "technical",
            "description": "Developer-oriented, precise terminology",
            "style": "technical"
        },
        {
            "name": "humorous",
            "description": "Playful, witty, engaging",
            "style": "humorous"
        }
    ]