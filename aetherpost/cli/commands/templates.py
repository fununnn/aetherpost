"""Template management commands."""

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
import shutil
import yaml

console = Console()
templates_app = typer.Typer()


@templates_app.command()
def list():
    """List available campaign templates."""
    
    console.print(Panel(
        "[bold blue]📄 Available Templates[/bold blue]",
        border_style="blue"
    ))
    
    # Built-in templates
    builtin_templates = get_builtin_templates()
    
    if builtin_templates:
        builtin_table = Table(title="Built-in Templates")
        builtin_table.add_column("Name", style="cyan")
        builtin_table.add_column("Description", style="white")
        builtin_table.add_column("Use Case", style="green")
        
        for template in builtin_templates:
            builtin_table.add_row(
                template["name"],
                template["description"],
                template["use_case"]
            )
        
        console.print(builtin_table)
    
    # Custom templates
    custom_templates = get_custom_templates()
    
    if custom_templates:
        console.print("\n[bold]Custom Templates:[/bold]")
        custom_table = Table()
        custom_table.add_column("Name", style="cyan")
        custom_table.add_column("Description", style="white")
        custom_table.add_column("Created", style="dim")
        
        for template in custom_templates:
            custom_table.add_row(
                template["name"],
                template.get("description", "No description"),
                template.get("created", "Unknown")
            )
        
        console.print(custom_table)
    else:
        console.print("\n[dim]No custom templates found[/dim]")
    
    console.print("\n[bold]Usage:[/bold]")
    console.print("• [cyan]aetherpost init --template <name>[/cyan] - Use template")
    console.print("• [cyan]aetherpost templates create[/cyan] - Create custom template")
    console.print("• [cyan]aetherpost templates show <name>[/cyan] - View template details")


@templates_app.command()
def show(
    name: str = typer.Argument(..., help="Template name to show"),
):
    """Show template details and content."""
    
    template = find_template(name)
    
    if not template:
        console.print(f"❌ [red]Template '{name}' not found[/red]")
        return
    
    console.print(Panel(
        f"[bold]📄 Template: {name}[/bold]",
        border_style="blue"
    ))
    
    # Template metadata
    info_table = Table(title="Template Information")
    info_table.add_column("Field", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Name", template["name"])
    info_table.add_row("Description", template["description"])
    info_table.add_row("Use Case", template.get("use_case", "General"))
    info_table.add_row("Type", "Built-in" if template.get("builtin") else "Custom")
    
    console.print(info_table)
    
    # Template content
    if "content" in template:
        console.print("\n[bold]Template Content:[/bold]")
        console.print("```yaml")
        console.print(template["content"])
        console.print("```")
    
    console.print(f"\n[bold]Usage:[/bold] [cyan]aetherpost init --template {name}[/cyan]")


@templates_app.command()
def create(
    name: str = typer.Argument(..., help="Template name"),
    from_config: str = typer.Option(None, "--from", help="Create from existing campaign.yaml"),
    description: str = typer.Option("", "--description", help="Template description"),
):
    """Create a new custom template."""
    
    console.print(Panel(
        f"[bold green]📝 Creating Template: {name}[/bold green]",
        border_style="green"
    ))
    
    # Check if template already exists
    if template_exists(name):
        if not Confirm.ask(f"Template '{name}' already exists. Overwrite?"):
            console.print("Template creation cancelled.")
            return
    
    # Get template content
    if from_config:
        # Create from existing configuration
        config_path = Path(from_config)
        if not config_path.exists():
            console.print(f"❌ [red]Configuration file not found: {from_config}[/red]")
            return
        
        with open(config_path) as f:
            template_content = f.read()
    
    else:
        # Create interactively
        template_content = create_template_interactively()
    
    # Get description if not provided
    if not description:
        description = Prompt.ask("Template description", default="Custom campaign template")
    
    # Save template
    try:
        save_custom_template(name, description, template_content)
        console.print(f"✅ [green]Template '{name}' created successfully![/green]")
        console.print(f"Usage: [cyan]aetherpost init --template {name}[/cyan]")
    
    except Exception as e:
        console.print(f"❌ [red]Failed to create template: {e}[/red]")


@templates_app.command()
def edit(
    name: str = typer.Argument(..., help="Template name to edit"),
):
    """Edit an existing custom template."""
    
    template = find_template(name)
    
    if not template:
        console.print(f"❌ [red]Template '{name}' not found[/red]")
        return
    
    if template.get("builtin"):
        console.print(f"❌ [red]Cannot edit built-in template '{name}'[/red]")
        console.print("Create a custom version with: [cyan]aetherpost templates create[/cyan]")
        return
    
    console.print(Panel(
        f"[bold yellow]✏️ Editing Template: {name}[/bold yellow]",
        border_style="yellow"
    ))
    
    # Show current content
    console.print("[bold]Current content:[/bold]")
    console.print("```yaml")
    console.print(template["content"])
    console.print("```")
    
    if Confirm.ask("Edit this template?"):
        # Create temporary file for editing
        temp_file = Path(f"/tmp/autopromo-template-{name}.yaml")
        with open(temp_file, "w") as f:
            f.write(template["content"])
        
        console.print(f"📝 [blue]Edit the template file: {temp_file}[/blue]")
        console.print("Press Enter when finished editing...")
        input()
        
        # Read back the edited content
        try:
            with open(temp_file) as f:
                new_content = f.read()
            
            # Validate YAML
            yaml.safe_load(new_content)
            
            # Save updated template
            save_custom_template(name, template["description"], new_content)
            console.print(f"✅ [green]Template '{name}' updated![/green]")
            
            # Clean up temp file
            temp_file.unlink()
        
        except yaml.YAMLError as e:
            console.print(f"❌ [red]Invalid YAML: {e}[/red]")
        except Exception as e:
            console.print(f"❌ [red]Failed to update template: {e}[/red]")


@templates_app.command()
def delete(
    name: str = typer.Argument(..., help="Template name to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Delete a custom template."""
    
    template = find_template(name)
    
    if not template:
        console.print(f"❌ [red]Template '{name}' not found[/red]")
        return
    
    if template.get("builtin"):
        console.print(f"❌ [red]Cannot delete built-in template '{name}'[/red]")
        return
    
    if not force:
        if not Confirm.ask(f"⚠️ Delete template '{name}'?"):
            console.print("Deletion cancelled.")
            return
    
    try:
        delete_custom_template(name)
        console.print(f"🗑️ [green]Template '{name}' deleted[/green]")
    
    except Exception as e:
        console.print(f"❌ [red]Failed to delete template: {e}[/red]")


@templates_app.command()
def export(
    name: str = typer.Argument(..., help="Template name to export"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Export template to file."""
    
    template = find_template(name)
    
    if not template:
        console.print(f"❌ [red]Template '{name}' not found[/red]")
        return
    
    if not output:
        output = f"{name}-template.yaml"
    
    try:
        with open(output, "w") as f:
            f.write(template["content"])
        
        console.print(f"📤 [green]Template exported to: {output}[/green]")
    
    except Exception as e:
        console.print(f"❌ [red]Failed to export template: {e}[/red]")


@templates_app.command()
def import_template(
    file: str = typer.Argument(..., help="Template file to import"),
    name: str = typer.Option(None, "--name", help="Template name (default: filename)"),
    description: str = typer.Option("", "--description", help="Template description"),
):
    """Import template from file."""
    
    file_path = Path(file)
    
    if not file_path.exists():
        console.print(f"❌ [red]File not found: {file}[/red]")
        return
    
    if not name:
        name = file_path.stem
    
    try:
        with open(file_path) as f:
            content = f.read()
        
        # Validate YAML
        yaml.safe_load(content)
        
        if not description:
            description = f"Imported from {file}"
        
        save_custom_template(name, description, content)
        console.print(f"📥 [green]Template '{name}' imported successfully![/green]")
    
    except yaml.YAMLError as e:
        console.print(f"❌ [red]Invalid YAML file: {e}[/red]")
    except Exception as e:
        console.print(f"❌ [red]Failed to import template: {e}[/red]")


def get_builtin_templates():
    """Get list of built-in templates."""
    return [
        {
            "name": "basic",
            "description": "Simple campaign with essential fields",
            "use_case": "Quick setup",
            "builtin": True,
            "content": """name: ""
concept: ""
platforms: [twitter]
content:
  style: "casual"
  action: "Learn more"
"""
        },
        {
            "name": "minimal",
            "description": "Absolute minimum configuration",
            "use_case": "Testing",
            "builtin": True,
            "content": """name: ""
concept: ""
platforms: [twitter]
"""
        },
        {
            "name": "professional",
            "description": "Business-focused campaign template",
            "use_case": "Corporate announcements",
            "builtin": True,
            "content": """name: ""
concept: ""
url: ""
platforms: [twitter, linkedin]
content:
  style: "professional"
  action: "Learn more"
  max_length: 280
schedule:
  type: "immediate"
analytics: true
"""
        },
        {
            "name": "developer",
            "description": "Technical project template",
            "use_case": "Open source projects",
            "builtin": True,
            "content": """name: ""
concept: ""
url: ""
platforms: [twitter, dev_to, mastodon]
content:
  style: "technical"
  action: "Check it out on GitHub"
  hashtags: ["opensource", "dev", "programming"]
image: "auto"
analytics: true
"""
        },
        {
            "name": "launch",
            "description": "Product launch template",
            "use_case": "Product releases",
            "builtin": True,
            "content": """name: ""
concept: ""
url: ""
platforms: [twitter, bluesky, linkedin]
content:
  style: "casual"
  action: "Try it now!"
  hashtags: ["ProductLaunch", "NewProduct"]
image: "generate"
schedule:
  type: "immediate"
analytics: true
experiments:
  enabled: false
"""
        }
    ]


def get_custom_templates():
    """Get list of custom templates."""
    templates_dir = Path(".aetherpost/templates")
    
    if not templates_dir.exists():
        return []
    
    templates = []
    for template_file in templates_dir.glob("*.yaml"):
        try:
            with open(template_file) as f:
                data = yaml.safe_load(f)
            
            templates.append({
                "name": template_file.stem,
                "description": data.get("_description", "No description"),
                "created": data.get("_created", "Unknown"),
                "content": open(template_file).read()
            })
        except Exception:
            continue
    
    return templates


def find_template(name):
    """Find template by name in built-in and custom templates."""
    
    # Check built-in templates
    for template in get_builtin_templates():
        if template["name"] == name:
            return template
    
    # Check custom templates
    for template in get_custom_templates():
        if template["name"] == name:
            return template
    
    return None


def template_exists(name):
    """Check if template exists."""
    return find_template(name) is not None


def save_custom_template(name, description, content):
    """Save custom template to disk."""
    templates_dir = Path(".aetherpost/templates")
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    template_file = templates_dir / f"{name}.yaml"
    
    # Add metadata to content
    template_data = yaml.safe_load(content)
    template_data["_description"] = description
    template_data["_created"] = "2025-06-14"  # You could use datetime.now()
    
    with open(template_file, "w") as f:
        yaml.dump(template_data, f, default_flow_style=False)


def delete_custom_template(name):
    """Delete custom template."""
    template_file = Path(f".aetherpost/templates/{name}.yaml")
    
    if template_file.exists():
        template_file.unlink()
    else:
        raise FileNotFoundError(f"Template file not found: {template_file}")


def create_template_interactively():
    """Create template content interactively."""
    
    console.print("[bold]Let's create your template step by step...[/bold]")
    
    template = {}
    
    # Basic fields
    console.print("\n[cyan]Basic Information:[/cyan]")
    template["name"] = '""'  # Placeholder
    template["concept"] = '""'  # Placeholder
    
    if Confirm.ask("Include URL field?"):
        template["url"] = '""'
    
    # Platforms
    console.print("\n[cyan]Platforms:[/cyan]")
    available_platforms = ["twitter", "bluesky", "mastodon", "linkedin", "dev_to"]
    selected_platforms = []
    
    for platform in available_platforms:
        if Confirm.ask(f"Include {platform}?", default=platform == "twitter"):
            selected_platforms.append(platform)
    
    template["platforms"] = selected_platforms
    
    # Content settings
    if Confirm.ask("\nInclude content configuration?", default=True):
        content = {}
        
        style = Prompt.ask(
            "Default style", 
            choices=["casual", "professional", "technical", "humorous"],
            default="casual"
        )
        content["style"] = style
        
        content["action"] = '"Learn more"'  # Placeholder
        
        if Confirm.ask("Include hashtags?"):
            content["hashtags"] = ["example", "template"]
        
        template["content"] = content
    
    # Additional features
    if Confirm.ask("\nInclude scheduling?"):
        template["schedule"] = {"type": "immediate"}
    
    if Confirm.ask("Include image generation?"):
        template["image"] = "auto"
    
    if Confirm.ask("Include analytics?"):
        template["analytics"] = True
    
    # Convert to YAML string
    return yaml.dump(template, default_flow_style=False)