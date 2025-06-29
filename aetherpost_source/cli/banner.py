"""ASCII art banner and installation messages for AetherPost."""

import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

console = Console()

# AetherPost ASCII Art Banner
AETHERPOST_BANNER = """
     ___          __  __                  ____                __
    /   |  ___   / /_/ /_   ___   _____  / __ \ ____   _____ / /_
   / /| | / _ \ / __/ __ \ / _ \ / ___/ / /_/ // __ \ / ___// __/
  / ___ |/  __// /_/ / / //  __// /    / ____// /_/ /(__  )/ /_
 /_/  |_|\___/ \__/_/ /_/ \___//_/    /_/     \____//____/ \__/

"""

TAGLINE = "🚀 Promotion as Code - Automate your app promotion across social media platforms"

# Installation success message
INSTALL_SUCCESS = """
╭─────────────────────────────────────────────────────────────────────────────╮
│                                                                             │
│  🎉 AetherPost installed successfully!                                     │
│                                                                             │
│  📋 Quick Start:                                                           │
│     aetherpost init      # Initialize your campaign                        │
│     aetherpost plan      # Preview your content                            │
│     aetherpost apply     # Execute your campaign                           │
│                                                                             │
│  📚 Documentation: https://aether-post.com                                 │
│  🐛 Issues: https://github.com/fununnn/aetherpost/issues                   │
│                                                                             │
╰─────────────────────────────────────────────────────────────────────────────╯
"""

# Version display banner
VERSION_BANNER = """
  █████╗ ███████╗████████╗██╗  ██╗███████╗██████╗ ██████╗  ██████╗ ███████╗████████╗
 ██╔══██╗██╔════╝╚══██╔══╝██║  ██║██╔════╝██╔══██╗██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝
 ███████║█████╗     ██║   ███████║█████╗  ██████╔╝██████╔╝██║   ██║███████╗   ██║
 ██╔══██║██╔══╝     ██║   ██╔══██║██╔══╝  ██╔══██╗██╔═══╝ ██║   ██║╚════██║   ██║
 ██║  ██║███████╗   ██║   ██║  ██║███████╗██║  ██║██║     ╚██████╔╝███████║   ██║
 ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚══════╝   ╚═╝
"""

# Command banners for different commands
COMMAND_BANNERS = {
    "init": """
  ██╗███╗   ██╗██╗████████╗
  ██║████╗  ██║██║╚══██╔══╝
  ██║██╔██╗ ██║██║   ██║
  ██║██║╚██╗██║██║   ██║
  ██║██║ ╚████║██║   ██║
  ╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝
""",
    "plan": """
  ██████╗ ██╗      █████╗ ███╗   ██╗
  ██╔══██╗██║     ██╔══██╗████╗  ██║
  ██████╔╝██║     ███████║██╔██╗ ██║
  ██╔═══╝ ██║     ██╔══██║██║╚██╗██║
  ██║     ███████╗██║  ██║██║ ╚████║
  ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝
""",
    "apply": """
   █████╗ ██████╗ ██████╗ ██╗  ██╗   ██╗
  ██╔══██╗██╔══██╗██╔══██╗██║  ╚██╗ ██╔╝
  ███████║██████╔╝██████╔╝██║   ╚████╔╝
  ██╔══██║██╔═══╝ ██╔═══╝ ██║    ╚██╔╝
  ██║  ██║██║     ██║     ███████╗██║
  ╚═╝  ╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝
""",
    "destroy": """
  ██████╗ ███████╗███████╗████████╗██████╗  ██████╗ ██╗   ██╗
  ██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗╚██╗ ██╔╝
  ██║  ██║█████╗  ███████╗   ██║   ██████╔╝██║   ██║ ╚████╔╝
  ██║  ██║██╔══╝  ╚════██║   ██║   ██╔══██╗██║   ██║  ╚██╔╝
  ██████╔╝███████╗███████║   ██║   ██║  ██║╚██████╔╝   ██║
  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝    ╚═╝
""",
}

# Color themes
COLORS = {
    "primary": "bright_blue",
    "secondary": "bright_green", 
    "accent": "bright_magenta",
    "success": "bright_green",
    "warning": "bright_yellow",
    "error": "bright_red",
}


def show_banner(command: str = None, version: str = None):
    """Display the main AetherPost banner."""
    
    try:
        # Clear screen for dramatic effect
        if sys.stdout.isatty():  # Only if running in terminal
            os.system('clear' if os.name == 'posix' else 'cls')
        
        console.print()
        
        if command and command in COMMAND_BANNERS:
            # Show command-specific banner
            banner_text = Text(COMMAND_BANNERS[command], style=COLORS["primary"])
            console.print(Align.center(banner_text))
        else:
            # Show main banner
            banner_text = Text(AETHERPOST_BANNER, style=COLORS["primary"])
            console.print(Align.center(banner_text))
        
        # Show tagline
        tagline_text = Text(TAGLINE, style=COLORS["secondary"])
        console.print(Align.center(tagline_text))
        
        if version:
            version_text = Text(f"v{version}", style=COLORS["accent"])
            console.print(Align.center(version_text))
        
        console.print()
        
    except Exception:
        # Fallback to simple text if rich formatting fails
        print("🚀 AetherPost - Promotion as Code")
        if version:
            print(f"v{version}")
        print()


def show_install_success():
    """Show installation success message."""
    
    try:
        console.print()
        
        # Show main banner first
        show_banner()
        
        # Show success message
        success_panel = Panel(
            INSTALL_SUCCESS.strip(),
            border_style=COLORS["success"],
            padding=(1, 2)
        )
        console.print(Align.center(success_panel))
        
        console.print()
        
    except Exception:
        # Fallback
        print("🎉 AetherPost installed successfully!")
        print("📋 Quick Start: aetherpost init")
        print("📚 Documentation: https://aether-post.com")


def show_version_info(version: str, build_info: dict = None):
    """Show detailed version information."""
    
    try:
        console.print()
        
        # Version banner
        version_text = Text(VERSION_BANNER, style=COLORS["primary"])
        console.print(Align.center(version_text))
        
        # Version details
        version_info = f"[bold {COLORS['accent']}]Version {version}[/bold {COLORS['accent']}]"
        console.print(Align.center(version_info))
        
        if build_info:
            console.print()
            info_lines = []
            
            if "build_date" in build_info:
                info_lines.append(f"📅 Built: {build_info['build_date']}")
            if "commit" in build_info:
                info_lines.append(f"🔨 Commit: {build_info['commit'][:8]}")
            if "python_version" in build_info:
                info_lines.append(f"🐍 Python: {build_info['python_version']}")
            
            for line in info_lines:
                console.print(Align.center(line))
        
        console.print()
        
    except Exception:
        # Fallback
        print(f"AetherPost v{version}")


def show_command_header(command: str, description: str = None):
    """Show command header with ASCII art."""
    
    try:
        # Don't clear screen for command headers
        console.print()
        
        if command in COMMAND_BANNERS:
            banner_text = Text(COMMAND_BANNERS[command], style=COLORS["primary"])
            console.print(Align.center(banner_text))
        
        if description:
            desc_text = Text(description, style=COLORS["secondary"])
            console.print(Align.center(desc_text))
        
        console.print()
        
    except Exception:
        # Fallback
        if description:
            print(f"🚀 {command.upper()}: {description}")
        else:
            print(f"🚀 {command.upper()}")
        print()


def show_loading_animation(message: str, duration: float = 2.0):
    """Show a loading animation with ASCII art."""
    
    try:
        import time
        from rich.progress import Progress, SpinnerColumn, TextColumn
        
        with Progress(
            SpinnerColumn(spinner_style=COLORS["primary"]),
            TextColumn("[bold blue]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(message, total=None)
            time.sleep(duration)
            
    except Exception:
        # Fallback
        print(f"⏳ {message}")


def get_terminal_size():
    """Get terminal size for centering."""
    try:
        return os.get_terminal_size()
    except:
        # Fallback size
        return os.terminal_size((80, 24))


def is_terminal_capable():
    """Check if terminal supports rich formatting."""
    try:
        return (
            sys.stdout.isatty() and 
            console.is_terminal and
            not os.getenv('CI')  # Don't show fancy output in CI
        )
    except:
        return False


# Export main functions
__all__ = [
    'show_banner',
    'show_install_success', 
    'show_version_info',
    'show_command_header',
    'show_loading_animation',
    'COLORS'
]