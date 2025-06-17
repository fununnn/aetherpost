"""Enhanced CLI user interface utilities."""

from typing import Optional, List, Dict, Any, Callable
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.syntax import Syntax
from rich.tree import Tree
from rich.status import Status
from rich.text import Text
from rich.align import Align
import time
import asyncio
from contextlib import contextmanager
import typer

from ...core.exceptions import AetherPostError, ErrorCode

console = Console()


class UITheme:
    """Centralized UI theme and styling."""
    
    PRIMARY = "blue"
    SUCCESS = "green"
    WARNING = "yellow"
    ERROR = "red"
    INFO = "cyan"
    MUTED = "bright_black"
    
    # Icons
    ICONS = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "loading": "⠋",
        "rocket": "🚀",
        "robot": "🤖",
        "chart": "📊",
        "gear": "⚙️",
        "sparkles": "✨",
        "fire": "🔥",
        "target": "🎯",
        "lightning": "⚡",
        "crown": "👑"
    }


class AetherPostUI:
    """Enhanced UI utilities for AetherPost CLI."""
    
    def __init__(self):
        self.console = console
        self.theme = UITheme()
    
    def header(self, title: str, subtitle: Optional[str] = None, icon: str = "rocket"):
        """Display a beautiful header."""
        icon_char = self.theme.ICONS.get(icon, icon)
        
        header_text = f"[bold {self.theme.PRIMARY}]{icon_char} {title}[/bold {self.theme.PRIMARY}]"
        if subtitle:
            header_text += f"\n\n{subtitle}"
        
        self.console.print(Panel(
            header_text,
            border_style=self.theme.PRIMARY,
            padding=(1, 2)
        ))
    
    def success(self, message: str, details: Optional[str] = None):
        """Display success message."""
        icon = self.theme.ICONS["success"]
        text = f"[bold {self.theme.SUCCESS}]{icon} {message}[/bold {self.theme.SUCCESS}]"
        
        if details:
            text += f"\n[{self.theme.MUTED}]{details}[/{self.theme.MUTED}]"
        
        self.console.print(text)
    
    def error(self, error: AetherPostError):
        """Display error with helpful suggestions."""
        icon = self.theme.ICONS["error"]
        
        # Main error message
        error_panel = Panel(
            f"[bold {self.theme.ERROR}]{icon} {error.message}[/bold {self.theme.ERROR}]",
            title=f"Error {error.error_code.value}",
            border_style=self.theme.ERROR
        )
        self.console.print(error_panel)
        
        # Suggestions
        if error.suggestions:
            suggestions_text = "\n".join(f"• {suggestion}" for suggestion in error.suggestions)
            self.console.print(Panel(
                suggestions_text,
                title="💡 Suggested Solutions",
                border_style=self.theme.INFO,
                padding=(0, 1)
            ))
        
        # Details for debugging
        if error.details and console.options.legacy_windows:
            details_text = "\n".join(f"{k}: {v}" for k, v in error.details.items())
            self.console.print(Panel(
                details_text,
                title="🔍 Details",
                border_style=self.theme.MUTED,
                padding=(0, 1)
            ))
    
    def warning(self, message: str, suggestions: Optional[List[str]] = None):
        """Display warning message."""
        icon = self.theme.ICONS["warning"]
        text = f"[bold {self.theme.WARNING}]{icon} {message}[/bold {self.theme.WARNING}]"
        
        self.console.print(text)
        
        if suggestions:
            for suggestion in suggestions:
                self.console.print(f"  💡 {suggestion}")
    
    def info(self, message: str):
        """Display info message."""
        icon = self.theme.ICONS["info"]
        self.console.print(f"[{self.theme.INFO}]{icon} {message}[/{self.theme.INFO}]")
    
    def status_table(self, title: str, data: Dict[str, Any], icon: str = "chart"):
        """Display status information in a table."""
        icon_char = self.theme.ICONS.get(icon, icon)
        
        table = Table(title=f"{icon_char} {title}")
        table.add_column("Property", style=self.theme.INFO)
        table.add_column("Value", style=self.theme.SUCCESS)
        
        for key, value in data.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        
        self.console.print(table)
    
    def progress_task(self, description: str, tasks: List[Dict[str, Any]]):
        """Display progress for multiple tasks."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            
            task_ids = {}
            
            # Add all tasks
            for task in tasks:
                task_id = progress.add_task(
                    task["description"], 
                    total=task.get("total", 100)
                )
                task_ids[task["name"]] = task_id
            
            # Execute tasks
            for task in tasks:
                task_id = task_ids[task["name"]]
                
                if "function" in task:
                    # Execute function and update progress
                    task["function"](lambda advance: progress.update(task_id, advance=advance))
                else:
                    # Simulate progress
                    for i in range(task.get("total", 100)):
                        time.sleep(0.01)
                        progress.update(task_id, advance=1)
    
    @contextmanager
    def spinner(self, message: str):
        """Context manager for spinner."""
        with Status(message, console=self.console, spinner="dots"):
            yield
    
    def confirm_action(
        self, 
        message: str, 
        default: bool = True,
        danger: bool = False
    ) -> bool:
        """Enhanced confirmation prompt."""
        style = self.theme.ERROR if danger else self.theme.PRIMARY
        icon = "⚠️" if danger else "❓"
        
        prompt_text = f"[{style}]{icon} {message}[/{style}]"
        self.console.print(prompt_text)
        
        return Confirm.ask("Continue?", default=default)
    
    def select_option(
        self, 
        message: str, 
        options: List[str],
        descriptions: Optional[List[str]] = None
    ) -> str:
        """Enhanced option selection."""
        self.console.print(f"[{self.theme.INFO}]❓ {message}[/{self.theme.INFO}]")
        
        # Display options
        for i, option in enumerate(options, 1):
            desc = descriptions[i-1] if descriptions else ""
            desc_text = f" - {desc}" if desc else ""
            self.console.print(f"  [{self.theme.PRIMARY}]{i}[/{self.theme.PRIMARY}]. {option}{desc_text}")
        
        while True:
            try:
                choice = IntPrompt.ask(
                    "Select option",
                    choices=[str(i) for i in range(1, len(options) + 1)]
                )
                return options[choice - 1]
            except (ValueError, IndexError):
                self.error("Invalid selection. Please try again.")
    
    def code_preview(self, code: str, language: str = "yaml", title: str = "Preview"):
        """Display code with syntax highlighting."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(Panel(
            syntax,
            title=title,
            border_style=self.theme.INFO
        ))
    
    def tree_view(self, title: str, data: Dict[str, Any]) -> Tree:
        """Create a tree view of hierarchical data."""
        tree = Tree(f"[bold {self.theme.PRIMARY}]{title}[/bold {self.theme.PRIMARY}]")
        
        def add_to_tree(node: Tree, items: Dict[str, Any]):
            for key, value in items.items():
                if isinstance(value, dict):
                    branch = node.add(f"[{self.theme.INFO}]{key}[/{self.theme.INFO}]")
                    add_to_tree(branch, value)
                elif isinstance(value, list):
                    branch = node.add(f"[{self.theme.INFO}]{key}[/{self.theme.INFO}]")
                    for item in value:
                        branch.add(str(item))
                else:
                    node.add(f"[{self.theme.SUCCESS}]{key}[/{self.theme.SUCCESS}]: {value}")
        
        add_to_tree(tree, data)
        return tree
    
    def celebration(self, message: str):
        """Display celebration message."""
        celebration_text = Text(f"🎉 {message} 🎉", style=f"bold {self.theme.SUCCESS}")
        self.console.print(Align.center(celebration_text))
        
        # Add some sparkles
        sparkle_line = " ".join("✨" for _ in range(10))
        self.console.print(Align.center(sparkle_line))


class SetupWizard:
    """Interactive setup wizard."""
    
    def __init__(self):
        self.ui = AetherPostUI()
        self.config = {}
    
    def run(self) -> Dict[str, Any]:
        """Run the complete setup wizard."""
        self.ui.header(
            "AetherPost Setup Wizard",
            "Let's get you set up in just a few minutes!",
            "gear"
        )
        
        # Project setup
        self._setup_project()
        
        # Platform selection
        self._setup_platforms()
        
        # AI provider setup
        self._setup_ai()
        
        # Preferences
        self._setup_preferences()
        
        # Summary
        self._show_summary()
        
        return self.config
    
    def _setup_project(self):
        """Setup project configuration."""
        self.ui.console.print("\n[bold]📁 Project Setup[/bold]")
        
        self.config["project_name"] = Prompt.ask(
            "Project name",
            default="my-aetherpost-project"
        )
        
        self.config["description"] = Prompt.ask(
            "Project description (optional)",
            default=""
        )
    
    def _setup_platforms(self):
        """Setup platform configuration."""
        self.ui.console.print("\n[bold]📱 Platform Selection[/bold]")
        
        platforms = [
            "Twitter",
            "Instagram", 
            "YouTube",
            "LinkedIn",
            "TikTok",
            "Reddit"
        ]
        
        descriptions = [
            "Microblogging and real-time updates",
            "Visual content and stories",
            "Video content and tutorials",
            "Professional networking",
            "Short-form viral videos",
            "Community discussions"
        ]
        
        self.ui.console.print("Select platforms you want to use (space-separated numbers):")
        
        for i, (platform, desc) in enumerate(zip(platforms, descriptions), 1):
            self.ui.console.print(f"  {i}. {platform} - {desc}")
        
        selection = Prompt.ask("Enter numbers (e.g., 1 3 5)")
        
        selected_indices = [int(x) - 1 for x in selection.split() if x.isdigit()]
        self.config["platforms"] = [platforms[i] for i in selected_indices if 0 <= i < len(platforms)]
    
    def _setup_ai(self):
        """Setup AI provider."""
        self.ui.console.print("\n[bold]🤖 AI Provider Setup[/bold]")
        
        ai_provider = self.ui.select_option(
            "Choose your AI provider",
            ["OpenAI", "AI Provider", "Both"],
            [
                "GPT-4 for content generation",
                "[AI Service] for advanced reasoning",
                "Use both for maximum capability"
            ]
        )
        
        self.config["ai_provider"] = ai_provider.lower().replace(" ", "_")
    
    def _setup_preferences(self):
        """Setup user preferences."""
        self.ui.console.print("\n[bold]⚙️ Preferences[/bold]")
        
        self.config["auto_post"] = self.ui.confirm_action(
            "Enable automatic posting?",
            default=False
        )
        
        self.config["analytics"] = self.ui.confirm_action(
            "Enable analytics tracking?",
            default=True
        )
        
        self.config["notifications"] = self.ui.confirm_action(
            "Enable notifications?",
            default=True
        )
    
    def _show_summary(self):
        """Show configuration summary."""
        self.ui.console.print("\n[bold]📋 Configuration Summary[/bold]")
        
        summary_tree = self.ui.tree_view("Your Setup", self.config)
        self.ui.console.print(summary_tree)
        
        if self.ui.confirm_action("Save this configuration?"):
            self.ui.celebration("Setup completed successfully!")
        else:
            self.ui.warning("Setup cancelled")


# Global UI instance
ui = AetherPostUI()


# Helper functions for backward compatibility
def create_status_panel(message: str, title: str = "Status", style: str = "blue"):
    """Create a status panel."""
    return Panel(message, title=title, border_style=style)


def print_success(message: str, details: Optional[str] = None):
    """Print success message."""
    ui.success(message, details)


def print_error(message: str):
    """Print error message."""
    error = AetherPostError(
        message=message,
        error_code=ErrorCode.GENERAL_ERROR,
        recoverable=True
    )
    ui.error(error)


def print_warning(message: str, suggestions: Optional[List[str]] = None):
    """Print warning message."""
    ui.warning(message, suggestions)


# Decorator for CLI commands to handle errors gracefully
def handle_cli_errors(func):
    """Decorator to handle CLI errors with beautiful output."""
    
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AetherPostError as e:
            ui.error(e)
            raise typer.Exit(1)
        except KeyboardInterrupt:
            ui.warning("Operation cancelled by user")
            raise typer.Exit(130)
        except Exception as e:
            # Unexpected error
            error = AetherPostError(
                message=f"Unexpected error: {str(e)}",
                error_code=ErrorCode.SYSTEM_ERROR,
                suggestions=[
                    "Please report this issue to GitHub",
                    "Include the full error details below"
                ],
                recoverable=False
            )
            ui.error(error)
            raise typer.Exit(1)
    
    return wrapper