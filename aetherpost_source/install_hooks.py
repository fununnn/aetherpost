"""Installation hooks for AetherPost."""

import os
import sys
import subprocess
from pathlib import Path

def post_install():
    """Run after successful installation."""
    try:
        # Try to show install success banner
        from .cli.banner import show_install_success
        show_install_success()
    except ImportError:
        # Fallback if rich not available yet
        print("🎉 AetherPost installed successfully!")
        print("📋 Quick Start: aetherpost init")
        print("📚 Documentation: https://aether-post.com")

def check_dependencies():
    """Check if all dependencies are available."""
    required_packages = [
        'rich',
        'typer', 
        'pydantic',
        'PyYAML',
        'aiohttp'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"⚠️  Missing dependencies: {', '.join(missing)}")
        print("Please install with: pip install aetherpost[all]")
        return False
    
    return True

def create_desktop_entry():
    """Create desktop entry for GUI environments (optional)."""
    try:
        if os.name != 'posix':
            return  # Only for Unix-like systems
        
        home = Path.home()
        desktop_dir = home / ".local" / "share" / "applications"
        
        if not desktop_dir.exists():
            return
        
        desktop_file = desktop_dir / "aetherpost.desktop"
        
        content = f"""[Desktop Entry]
Name=AetherPost
Comment=Social Media Automation Tool
Exec=aetherpost
Icon=terminal
Terminal=true
Type=Application
Categories=Development;Utility;
Keywords=social;media;automation;promotion;
"""
        
        with open(desktop_file, 'w') as f:
            f.write(content)
            
    except Exception:
        # Ignore errors in desktop entry creation
        pass

if __name__ == "__main__":
    # Can be called directly during installation
    post_install()