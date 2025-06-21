"""Base command structure for unified CLI experience."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm, IntPrompt

from aetherpost.core.common.base_models import Platform, ContentType, OperationResult
from aetherpost.core.common.config_manager import config_manager
from aetherpost.core.common.error_handler import error_handler, handle_errors
from aetherpost.core.common.utils import generate_id, safe_filename

logger = logging.getLogger(__name__)


class CommandCategory(Enum):
    """Categories for organizing commands."""
    CORE = "core"           # Basic functionality
    CONTENT = "content"     # Content generation and management
    SOCIAL = "social"       # Social media specific
    AUTOMATION = "automation"  # Automated features
    ANALYTICS = "analytics" # Analytics and insights
    MANAGEMENT = "management"  # Configuration and management
    UTILITIES = "utilities" # Helper utilities


@dataclass
class CommandOption:
    """Standardized command option definition."""
    name: str
    short_name: Optional[str] = None
    help_text: str = ""
    option_type: type = str
    default: Any = None
    required: bool = False
    multiple: bool = False
    choices: Optional[List[str]] = None
    prompt: bool = False
    
    def to_click_option(self) -> Callable:
        """Convert to Click option decorator."""
        option_names = [f"--{self.name}"]
        if self.short_name:
            option_names.append(f"-{self.short_name}")
        
        kwargs = {
            "help": self.help_text,
            "type": self.option_type,
            "default": self.default,
            "required": self.required,
            "multiple": self.multiple,
            "prompt": self.prompt
        }
        
        if self.choices:
            kwargs["type"] = click.Choice(self.choices)
        
        return click.option(*option_names, **kwargs)


@dataclass
class CommandMetadata:
    """Metadata for command documentation and organization."""
    name: str
    description: str
    category: CommandCategory
    examples: List[str] = field(default_factory=list)
    related_commands: List[str] = field(default_factory=list)
    requires_auth: bool = False
    requires_config: bool = False
    experimental: bool = False
    deprecated: bool = False


class BaseCommand(ABC):
    """Abstract base class for all AetherPost commands."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.config = config_manager.config
        self.metadata: Optional[CommandMetadata] = None
        self.options: List[CommandOption] = []
        self._setup_command()
    
    @abstractmethod
    def _setup_command(self) -> None:
        """Setup command metadata and options."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> OperationResult:
        """Execute the command with given parameters."""
        pass
    
    def validate_prerequisites(self) -> OperationResult:
        """Validate command prerequisites."""
        errors = []
        
        if self.metadata and self.metadata.requires_config:
            config_issues = config_manager.validate_config()
            if config_issues:
                errors.extend(config_issues)
        
        if self.metadata and self.metadata.requires_auth:
            configured_platforms = self.config.get_configured_platforms()
            if not configured_platforms:
                errors.append("No platform credentials configured. Run 'aetherpost auth' first.")
        
        if errors:
            return OperationResult.error_result(
                "Prerequisites not met",
                errors=errors
            )
        
        return OperationResult.success_result("Prerequisites validated")
    
    def show_help(self) -> None:
        """Show command help information."""
        if not self.metadata:
            self.console.print("No help available for this command.")
            return
        
        # Command description
        help_content = f"[bold]{self.metadata.name}[/bold]\n\n{self.metadata.description}\n"
        
        # Category and status
        status_info = []
        status_info.append(f"Category: {self.metadata.category.value}")
        if self.metadata.experimental:
            status_info.append("[yellow]Experimental[/yellow]")
        if self.metadata.deprecated:
            status_info.append("[red]Deprecated[/red]")
        
        help_content += f"\n{' | '.join(status_info)}\n"
        
        # Prerequisites
        if self.metadata.requires_auth or self.metadata.requires_config:
            prereqs = []
            if self.metadata.requires_config:
                prereqs.append("Configuration")
            if self.metadata.requires_auth:
                prereqs.append("Authentication")
            help_content += f"\n[bold]Prerequisites:[/bold] {', '.join(prereqs)}\n"
        
        # Options
        if self.options:
            help_content += "\n[bold]Options:[/bold]\n"
            for option in self.options:
                option_line = f"  --{option.name}"
                if option.short_name:
                    option_line += f", -{option.short_name}"
                if option.option_type != str:
                    option_line += f" <{option.option_type.__name__}>"
                option_line += f": {option.help_text}"
                if option.default is not None:
                    option_line += f" (default: {option.default})"
                help_content += option_line + "\n"
        
        # Examples
        if self.metadata.examples:
            help_content += "\n[bold]Examples:[/bold]\n"
            for example in self.metadata.examples:
                help_content += f"  {example}\n"
        
        # Related commands
        if self.metadata.related_commands:
            help_content += f"\n[bold]Related Commands:[/bold] {', '.join(self.metadata.related_commands)}\n"
        
        self.console.print(Panel(help_content, title="Command Help"))
    
    def print_success(self, message: str, data: Any = None) -> None:
        """Print success message."""
        self.console.print(f"✅ [green]{message}[/green]")
        if data:
            self.console.print(data)
    
    def print_error(self, message: str, details: Optional[str] = None) -> None:
        """Print error message."""
        self.console.print(f"❌ [red]{message}[/red]")
        if details:
            self.console.print(f"[dim]{details}[/dim]")
    
    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"⚠️ [yellow]{message}[/yellow]")
    
    def print_info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"ℹ️ [blue]{message}[/blue]")
    
    def create_table(self, title: str, headers: List[str]) -> Table:
        """Create standardized table."""
        table = Table(title=title, show_header=True, header_style="bold magenta")
        for header in headers:
            table.add_column(header)
        return table
    
    def show_progress(self, task_description: str) -> Progress:
        """Create standardized progress indicator."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        )
    
    def prompt_selection(self, prompt_text: str, choices: List[str], 
                        default: Optional[str] = None) -> str:
        """Interactive selection prompt."""
        if len(choices) == 1:
            return choices[0]
        
        self.console.print(f"\n[bold]{prompt_text}[/bold]")
        for i, choice in enumerate(choices, 1):
            self.console.print(f"  {i}. {choice}")
        
        while True:
            try:
                selection = IntPrompt.ask(
                    "Select option",
                    choices=[str(i) for i in range(1, len(choices) + 1)],
                    default="1" if default is None else str(choices.index(default) + 1)
                )
                return choices[selection - 1]
            except (ValueError, IndexError):
                self.console.print("[red]Invalid selection. Please try again.[/red]")
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Confirmation prompt."""
        return Confirm.ask(message, default=default)
    
    def handle_async_execution(self, coro) -> Any:
        """Handle async execution in sync context."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)


class ContentCommand(BaseCommand):
    """Base class for content-related commands."""
    
    def __init__(self, console: Optional[Console] = None):
        super().__init__(console)
        self.common_options = [
            CommandOption(
                name="platforms",
                short_name="p",
                help_text="Target platforms (comma-separated)",
                multiple=True,
                choices=[platform.value for platform in Platform]
            ),
            CommandOption(
                name="content-type",
                short_name="t",
                help_text="Type of content to generate",
                choices=[ct.value for ct in ContentType],
                default="announcement"
            ),
            CommandOption(
                name="style",
                short_name="s",
                help_text="Content style",
                choices=["professional", "friendly", "creative", "technical"],
                default="friendly"
            ),
            CommandOption(
                name="dry-run",
                help_text="Preview without posting",
                option_type=bool,
                default=False
            )
        ]
        self.options.extend(self.common_options)
    
    def validate_platforms(self, platforms: List[str]) -> OperationResult:
        """Validate platform selection."""
        if not platforms:
            configured_platforms = self.config.get_configured_platforms()
            if not configured_platforms:
                return OperationResult.error_result(
                    "No platforms specified and none configured"
                )
            platforms = configured_platforms
        
        # Validate platform credentials
        invalid_platforms = []
        for platform in platforms:
            creds = self.config.get_platform_credentials(platform)
            if not creds or not creds.is_valid():
                invalid_platforms.append(platform)
        
        if invalid_platforms:
            return OperationResult.error_result(
                f"Invalid credentials for platforms: {', '.join(invalid_platforms)}"
            )
        
        return OperationResult.success_result(
            "Platforms validated",
            data=platforms
        )


class ManagementCommand(BaseCommand):
    """Base class for management/configuration commands."""
    
    def __init__(self, console: Optional[Console] = None):
        super().__init__(console)
        self.common_options = [
            CommandOption(
                name="interactive",
                short_name="i",
                help_text="Use interactive mode",
                option_type=bool,
                default=False
            ),
            CommandOption(
                name="force",
                short_name="f",
                help_text="Force operation without confirmation",
                option_type=bool,
                default=False
            ),
            CommandOption(
                name="backup",
                help_text="Create backup before changes",
                option_type=bool,
                default=True
            )
        ]
        self.options.extend(self.common_options)
    
    def create_backup(self, operation_name: str) -> OperationResult:
        """Create configuration backup."""
        try:
            backup_path = config_manager.config_dir / f"backup_{operation_name}_{generate_id()}.yaml"
            result = config_manager.export_config(backup_path, include_credentials=True)
            
            if result.success:
                self.print_info(f"Backup created: {backup_path}")
            
            return result
        except Exception as e:
            return OperationResult.error_result(f"Failed to create backup: {e}")


class AnalyticsCommand(BaseCommand):
    """Base class for analytics/reporting commands."""
    
    def __init__(self, console: Optional[Console] = None):
        super().__init__(console)
        self.common_options = [
            CommandOption(
                name="period",
                help_text="Time period for analysis",
                choices=["24h", "7d", "30d", "90d"],
                default="7d"
            ),
            CommandOption(
                name="format",
                help_text="Output format",
                choices=["table", "json", "csv"],
                default="table"
            ),
            CommandOption(
                name="export",
                short_name="e",
                help_text="Export results to file",
                option_type=bool,
                default=False
            )
        ]
        self.options.extend(self.common_options)
    
    def format_output(self, data: Any, format_type: str, title: str = "Results") -> None:
        """Format and display output based on requested format."""
        if format_type == "json":
            import json
            self.console.print(json.dumps(data, indent=2, default=str))
        elif format_type == "csv":
            # Simple CSV output for lists of dictionaries
            if isinstance(data, list) and data and isinstance(data[0], dict):
                import csv
                import io
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                self.console.print(output.getvalue())
            else:
                self.console.print("CSV format not supported for this data type")
        else:  # table
            if isinstance(data, dict):
                table = self.create_table(title, ["Key", "Value"])
                for key, value in data.items():
                    table.add_row(str(key), str(value))
                self.console.print(table)
            elif isinstance(data, list) and data and isinstance(data[0], dict):
                headers = list(data[0].keys())
                table = self.create_table(title, headers)
                for item in data:
                    table.add_row(*[str(item.get(h, "")) for h in headers])
                self.console.print(table)
            else:
                self.console.print(data)


def create_click_command(command_class: type) -> click.Command:
    """Convert BaseCommand to Click command."""
    
    def command_wrapper(**kwargs):
        """Wrapper function for Click command."""
        command_instance = command_class()
        
        # Validate prerequisites
        prereq_result = command_instance.validate_prerequisites()
        if not prereq_result.success:
            command_instance.print_error(prereq_result.message)
            for error in prereq_result.errors:
                command_instance.print_error(f"  • {error}")
            return
        
        # Execute command
        try:
            result = command_instance.execute(**kwargs)
            
            if result.success:
                command_instance.print_success(result.message, result.data)
            else:
                command_instance.print_error(result.message)
                for error in result.errors:
                    command_instance.print_error(f"  • {error}")
                for warning in result.warnings:
                    command_instance.print_warning(f"  • {warning}")
        
        except Exception as e:
            error = error_handler.handle_exception(e)
            command_instance.print_error(error.message)
            if error.suggestions:
                command_instance.print_info("Suggestions:")
                for suggestion in error.suggestions:
                    command_instance.print_info(f"  • {suggestion}")
    
    # Create Click command
    cmd = click.command()(command_wrapper)
    
    # Add options from command class
    temp_instance = command_class()
    for option in reversed(temp_instance.options):  # Reverse for proper decorator order
        cmd = option.to_click_option()(cmd)
    
    # Set command name and help from metadata
    if temp_instance.metadata:
        cmd.name = temp_instance.metadata.name
        cmd.help = temp_instance.metadata.description
    
    return cmd


# Common option sets for reuse
PLATFORM_OPTIONS = [
    CommandOption(
        name="platforms",
        short_name="p",
        help_text="Target platforms (comma-separated)",
        multiple=True,
        choices=[platform.value for platform in Platform]
    )
]

CONTENT_OPTIONS = [
    CommandOption(
        name="content-type",
        short_name="t",
        help_text="Type of content",
        choices=[ct.value for ct in ContentType],
        default="announcement"
    ),
    CommandOption(
        name="style",
        short_name="s",
        help_text="Content style",
        choices=["professional", "friendly", "creative", "technical"],
        default="friendly"
    )
]

OUTPUT_OPTIONS = [
    CommandOption(
        name="format",
        help_text="Output format",
        choices=["table", "json", "yaml", "csv"],
        default="table"
    ),
    CommandOption(
        name="output",
        short_name="o",
        help_text="Output file path"
    )
]

COMMON_FLAGS = [
    CommandOption(
        name="interactive",
        short_name="i",
        help_text="Interactive mode",
        option_type=bool,
        default=False
    ),
    CommandOption(
        name="dry-run",
        help_text="Preview without executing",
        option_type=bool,
        default=False
    ),
    CommandOption(
        name="verbose",
        short_name="v",
        help_text="Verbose output",
        option_type=bool,
        default=False
    ),
    CommandOption(
        name="quiet",
        short_name="q",
        help_text="Suppress output",
        option_type=bool,
        default=False
    )
]