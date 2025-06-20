"""Profile management command for social media accounts."""

import asyncio
import aiohttp
import typer
import os
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
import json
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.columns import Columns
from rich.text import Text

from aetherpost.core.profiles.generator import ProfileGenerator, ProfileContent
import logging
from aetherpost.cli.utils.ui import create_status_panel, print_success, print_error, print_warning

logger = logging.getLogger(__name__)
console = Console()

class ProfileExporter:
    """Export profiles to various formats for easy copying."""
    
    def __init__(self):
        self.output_dir = Path.cwd() / ".aetherpost" / "profiles"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_copyable_files(self, profiles: List[ProfileContent], app_name: str) -> Dict[str, str]:
        """Export profiles to individual copyable text files."""
        
        exported_files = {}
        timestamp = Path().cwd().name  # Use current directory name
        
        for profile in profiles:
            # Create platform-specific file
            filename = f"{app_name.lower()}_{profile.platform}_profile.txt"
            file_path = self.output_dir / filename
            
            # Generate copyable content
            content = self._generate_copyable_content(profile)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            exported_files[profile.platform] = str(file_path)
            logger.info(f"Exported {profile.platform} profile to {file_path}")
        
        # Create combined file
        combined_filename = f"{app_name.lower()}_all_profiles.md"
        combined_path = self.output_dir / combined_filename
        self._create_combined_markdown(profiles, str(combined_path), app_name)
        exported_files["combined"] = str(combined_path)
        
        return exported_files
    
    def _generate_copyable_content(self, profile: ProfileContent) -> str:
        """Generate copyable text content for a profile."""
        
        content = f"""=== {profile.platform.upper()} PROFILE ===
Generated: {Path().cwd().name}

DISPLAY NAME:
{profile.display_name}

BIO/DESCRIPTION ({profile.character_count}/{profile.character_limit} characters):
{profile.bio}
"""
        
        if profile.website_url:
            content += f"""
WEBSITE/LINK:
{profile.website_url}
"""
        
        if profile.location:
            content += f"""
LOCATION:
{profile.location}
"""
        
        if profile.pinned_post:
            content += f"""
PINNED POST/CONTENT:
{profile.pinned_post}
"""
        
        if profile.additional_links:
            content += f"""
ADDITIONAL LINKS:
"""
            for link in profile.additional_links:
                content += f"• {link['title']}: {link['url']}\n"
        
        content += f"""
PROFILE IMAGE SUGGESTION:
{profile.profile_image_suggestion or 'Use your standard logo/avatar'}

"""
        
        if profile.cover_image_suggestion and profile.cover_image_suggestion != "Not applicable":
            content += f"""COVER IMAGE SUGGESTION:
{profile.cover_image_suggestion}

"""
        
        content += """COPY INSTRUCTIONS:
1. Copy the bio text above
2. Paste into your {platform} profile bio/description field
3. Add the website URL to the appropriate field
4. Set your profile image and cover image as suggested
5. Create pinned content as described

Note: Some platforms may require manual updates as they don't support API changes to profiles.
""".format(platform=profile.platform.title())
        
        return content
    
    def _create_combined_markdown(self, profiles: List[ProfileContent], file_path: str, app_name: str) -> None:
        """Create a combined markdown file with all profiles."""
        
        content = f"""# {app_name} - Social Media Profiles

Generated on: {Path().cwd().name}

This file contains optimized profile content for all supported social media platforms. Copy and paste the relevant sections to update your profiles.

## 📋 Profile Overview

| Platform | Bio Length | Features |
|----------|------------|----------|
"""
        
        for profile in profiles:
            features = []
            if profile.website_url:
                features.append("Website")
            if profile.location:
                features.append("Location")
            if profile.pinned_post:
                features.append("Pinned Content")
            
            content += f"| {profile.platform.title()} | {profile.character_count}/{profile.character_limit} | {', '.join(features) or 'Basic'} |\n"
        
        content += "\n---\n\n"
        
        # Add each platform section
        for profile in profiles:
            content += f"""## {self._get_platform_emoji(profile.platform)} {profile.platform.title()}

### Display Name
```
{profile.display_name}
```

### Bio/Description
**Character count:** {profile.character_count}/{profile.character_limit}
```
{profile.bio}
```
"""
            
            if profile.website_url:
                content += f"""
### Website URL
```
{profile.website_url}
```
"""
            
            if profile.location:
                content += f"""
### Location
```
{profile.location}
```
"""
            
            if profile.pinned_post:
                content += f"""
### Pinned Content
```
{profile.pinned_post}
```
"""
            
            if profile.additional_links:
                content += "\n### Additional Links\n"
                for link in profile.additional_links:
                    content += f"- **{link['title']}:** {link['url']}\n"
            
            content += f"""
### Image Suggestions
- **Profile Image:** {profile.profile_image_suggestion or 'Standard logo/avatar'}
"""
            
            if profile.cover_image_suggestion and profile.cover_image_suggestion != "Not applicable":
                content += f"- **Cover Image:** {profile.cover_image_suggestion}\n"
            
            content += "\n### Copy Instructions\n"
            content += f"1. Navigate to your {profile.platform.title()} profile settings\n"
            content += "2. Copy and paste the bio text into the description field\n"
            content += "3. Add the website URL if supported\n"
            content += "4. Update location if applicable\n"
            content += "5. Create or update pinned content as described\n"
            
            content += "\n---\n\n"
        
        # Add footer
        content += f"""## 🚀 Next Steps

1. **Review**: Check each profile for accuracy and brand consistency
2. **Customize**: Modify any content to match your specific voice
3. **Update**: Copy and paste content to each platform
4. **Monitor**: Track engagement and adjust profiles as needed
5. **Refresh**: Use AetherPost to regenerate profiles when you have major updates

## 📝 Notes

- Some platforms (Instagram, TikTok) require manual profile updates
- LinkedIn allows longer descriptions in the "About" section
- GitHub profiles can use the README.md suggestions for your profile repository
- Consider A/B testing different bio variations to see what works best

Generated by AetherPost Profile Generator
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _get_platform_emoji(self, platform: str) -> str:
        """Get emoji for platform."""
        emojis = {
            "twitter": "🐦",
            "instagram": "📷",
            "linkedin": "💼",
            "github": "⚡",
            "youtube": "📺",
            "tiktok": "🎵",
            "reddit": "🔴",
            "discord": "💬"
        }
        return emojis.get(platform, "📱")
    
    def create_setup_checklist(self, profiles: List[ProfileContent], app_name: str) -> str:
        """Create a setup checklist for manual profile updates."""
        
        checklist_path = self.output_dir / f"{app_name.lower()}_profile_checklist.md"
        
        content = f"""# {app_name} Profile Setup Checklist

Use this checklist to ensure all your social media profiles are updated consistently.

## 📋 Pre-Setup
- [ ] Review all generated content for accuracy
- [ ] Prepare profile images (square format recommended)
- [ ] Prepare cover images where applicable
- [ ] Have your website URL ready

## 🔄 Platform Updates

"""
        
        for profile in profiles:
            emoji = self._get_platform_emoji(profile.platform)
            content += f"""### {emoji} {profile.platform.title()}
- [ ] Update display name to: `{profile.display_name}`
- [ ] Update bio/description ({profile.character_count} characters)
- [ ] Add website URL: `{profile.website_url or 'N/A'}`
"""
            if profile.location:
                content += f"- [ ] Set location: `{profile.location}`\n"
            if profile.pinned_post:
                content += f"- [ ] Create/update pinned content\n"
            if profile.additional_links:
                content += f"- [ ] Add additional links ({len(profile.additional_links)} links)\n"
            
            content += f"- [ ] Update profile image\n"
            if profile.cover_image_suggestion and profile.cover_image_suggestion != "Not applicable":
                content += f"- [ ] Update cover image\n"
            content += "\n"
        
        content += f"""## ✅ Post-Setup
- [ ] Test all links and ensure they work
- [ ] Check that profiles look consistent across platforms
- [ ] Save profile URLs for future reference
- [ ] Schedule profile review for next quarter

## 📱 Platform-Specific Notes

**Instagram & TikTok:** These platforms typically require manual bio updates as they don't support automated profile changes.

**LinkedIn:** Consider using the longer "About" section for more detailed descriptions.

**GitHub:** Use the suggested README.md content for your profile repository.

**Twitter:** Take advantage of pinned tweets to showcase your best content.

## 🔗 Quick Links

Copy these for easy access:
"""
        
        for profile in profiles:
            platform_url = {
                "twitter": "https://twitter.com/settings/profile",
                "instagram": "https://www.instagram.com/accounts/edit/",
                "linkedin": "https://www.linkedin.com/in/me/edit/",
                "github": "https://github.com/settings/profile",
                "youtube": "https://studio.youtube.com/channel/UC.../editing/details",
                "tiktok": "https://www.tiktok.com/setting/account",
                "reddit": "https://www.reddit.com/settings/profile",
                "discord": "Discord App > User Settings > My Account"
            }
            
            url = platform_url.get(profile.platform, f"https://{profile.platform}.com/settings")
            content += f"- [{profile.platform.title()} Settings]({url})\n"
        
        with open(checklist_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(checklist_path)

@click.group(name="profile")
@click.pass_context
def profile(ctx):
    """Generate and manage social media profiles."""
    ctx.ensure_object(dict)

@profile.command()
@click.option("--app-name", "-n", help="Your app/product name")
@click.option("--description", "-d", help="App description")
@click.option("--github-url", "-g", help="GitHub repository URL")
@click.option("--website-url", "-w", help="Website URL")
@click.option("--location", "-l", help="Location (for platforms that support it)")
@click.option("--project-path", "-p", help="Path to project (for auto-detection)")
@click.option("--platform", "-P", multiple=True, help="Specific platforms (default: all)")
@click.option("--style", "-s", type=click.Choice(['professional', 'friendly', 'creative', 'technical']), 
              default='friendly', help="Profile style")
@click.option("--export", "-e", is_flag=True, help="Export to copyable files")
@click.option("--variations", "-v", is_flag=True, help="Generate multiple style variations")
def generate(app_name, description, github_url, website_url, location, project_path, platform, style, export, variations):
    """Generate optimized social media profiles."""
    
    generator = ProfileGenerator()
    
    # Auto-detect project info if path provided
    if project_path or github_url:
        console.print("🔍 Detecting project information...")
        project_info = generator.extract_project_info(project_path, github_url)
    else:
        project_info = {}
    
    # Override with provided values
    if app_name:
        project_info["name"] = app_name
    if description:
        project_info["description"] = description
    if website_url:
        project_info["website_url"] = website_url
    if location:
        project_info["location"] = location
    if github_url:
        project_info["github_url"] = github_url
    
    # Set defaults if nothing detected
    if not project_info.get("name"):
        project_info["name"] = Prompt.ask("App/Product name", default="AetherPost")
    if not project_info.get("description"):
        project_info["description"] = Prompt.ask("Description", default="Social media automation for developers")
    
    # Select platforms
    available_platforms = generator.get_supported_platforms()
    if not platform:
        # Interactive platform selection
        console.print("\n[bold]Available Platforms:[/bold]")
        for i, plat in enumerate(available_platforms, 1):
            console.print(f"  {i}. {plat.title()}")
        
        console.print("\nSelect platforms (enter numbers separated by commas, or 'all'):")
        selection = Prompt.ask("Platforms", default="all")
        
        if selection.lower() == "all":
            selected_platforms = available_platforms
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                selected_platforms = [available_platforms[i] for i in indices if 0 <= i < len(available_platforms)]
            except (ValueError, IndexError):
                print_error("Invalid selection. Using all platforms.")
                selected_platforms = available_platforms
    else:
        selected_platforms = list(platform)
    
    console.print(f"\n🚀 Generating profiles for {len(selected_platforms)} platforms...")
    
    generated_profiles = []
    
    # Generate profiles
    for plat in selected_platforms:
        try:
            if variations:
                # Generate multiple variations
                variations_list = generator.generate_multiple_variations(plat, project_info)
                for i, var_profile in enumerate(variations_list):
                    var_profile.display_name += f" (Style {i+1})"
                    generated_profiles.append(var_profile)
            else:
                # Generate single profile
                profile_content = generator.generate_profile(plat, project_info, style)
                generated_profiles.append(profile_content)
            
        except Exception as e:
            print_error(f"Failed to generate {plat} profile: {e}")
    
    if not generated_profiles:
        print_error("No profiles were generated successfully.")
        return
    
    # Display generated profiles
    console.print(f"\n✅ Generated {len(generated_profiles)} profiles!")
    
    # Show summary table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Platform", style="cyan")
    table.add_column("Display Name")
    table.add_column("Bio Preview")
    table.add_column("Length")
    table.add_column("Status")
    
    for profile in generated_profiles:
        bio_preview = profile.bio[:50] + "..." if len(profile.bio) > 50 else profile.bio
        
        # Status based on character count
        if profile.character_count > profile.character_limit:
            status = "⚠️ Over limit"
        elif profile.character_count > profile.character_limit * 0.9:
            status = "⚠️ Near limit"
        else:
            status = "✅ Good"
        
        table.add_row(
            profile.platform.title(),
            profile.display_name,
            bio_preview,
            f"{profile.character_count}/{profile.character_limit}",
            status
        )
    
    console.print(table)
    
    # Show detailed preview for each platform
    if Confirm.ask("\nShow detailed preview?", default=True):
        for profile in generated_profiles:
            _show_detailed_profile(profile)
    
    # Export to files
    if export or Confirm.ask("\nExport to copyable files?", default=True):
        exporter = ProfileExporter()
        exported_files = exporter.export_to_copyable_files(generated_profiles, project_info["name"])
        checklist_file = exporter.create_setup_checklist(generated_profiles, project_info["name"])
        
        console.print(f"\n📁 Files exported to [cyan]./.aetherpost/profiles/[/cyan]")
        
        files_table = Table(show_header=True, header_style="bold green")
        files_table.add_column("File Type", style="cyan")
        files_table.add_column("File Path")
        
        for platform, file_path in exported_files.items():
            files_table.add_row(
                platform.title(),
                Path(file_path).name
            )
        
        files_table.add_row("Setup Checklist", Path(checklist_file).name)
        console.print(files_table)
        
        print_success("✅ All profile files generated and ready for copy-paste!")
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("1. Open the generated files")
        console.print("2. Copy and paste content to each platform")
        console.print("3. Use the checklist to track your progress")

def _show_detailed_profile(profile: ProfileContent) -> None:
    """Show detailed profile information."""
    
    # Create content for the panel
    content_parts = []
    
    content_parts.append(f"[bold]Display Name:[/bold] {profile.display_name}")
    content_parts.append(f"[bold]Bio ({profile.character_count}/{profile.character_limit} chars):[/bold]")
    content_parts.append(f"[dim]{profile.bio}[/dim]")
    
    if profile.website_url:
        content_parts.append(f"[bold]Website:[/bold] {profile.website_url}")
    
    if profile.location:
        content_parts.append(f"[bold]Location:[/bold] {profile.location}")
    
    if profile.pinned_post:
        pinned_preview = profile.pinned_post[:100] + "..." if len(profile.pinned_post) > 100 else profile.pinned_post
        content_parts.append(f"[bold]Pinned Content:[/bold] {pinned_preview}")
    
    if profile.additional_links:
        content_parts.append(f"[bold]Additional Links:[/bold] {len(profile.additional_links)} links")
    
    content_parts.append(f"[bold]Profile Image:[/bold] {profile.profile_image_suggestion}")
    
    if profile.cover_image_suggestion and profile.cover_image_suggestion != "Not applicable":
        content_parts.append(f"[bold]Cover Image:[/bold] {profile.cover_image_suggestion}")
    
    # Determine panel color based on character count
    if profile.character_count > profile.character_limit:
        border_style = "red"
    elif profile.character_count > profile.character_limit * 0.9:
        border_style = "yellow"
    else:
        border_style = "green"
    
    console.print(Panel(
        "\n".join(content_parts),
        title=f"📱 {profile.platform.title()} Profile",
        border_style=border_style
    ))

@profile.command()
def platforms():
    """Show supported platforms and their requirements."""
    
    generator = ProfileGenerator()
    
    console.print(Panel(
        "[bold green]Supported Social Media Platforms[/bold green]",
        title="📱 Platform Support"
    ))
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Platform", style="cyan")
    table.add_column("Bio Limit")
    table.add_column("Features")
    table.add_column("API Update")
    
    for platform_name in generator.get_supported_platforms():
        config = generator.get_platform_requirements(platform_name)
        
        features = []
        if config.supports_website:
            features.append("Website")
        if config.supports_location:
            features.append("Location")
        if config.supports_pinned_post:
            features.append("Pinned")
        if config.emoji_friendly:
            features.append("Emoji")
        
        # Most platforms don't support API profile updates
        api_support = "❌ Manual only"
        if platform_name in ["twitter"]:  # Only Twitter supports some profile API updates
            api_support = "⚠️ Limited API"
        
        table.add_row(
            platform_name.title(),
            f"{config.bio_max_length} chars",
            ", ".join(features) if features else "Basic",
            api_support
        )
    
    console.print(table)
    
    console.print("\n[yellow]Note:[/yellow] Most platforms require manual profile updates.")
    console.print("AetherPost generates copyable content for easy manual updating.")

@profile.command()
@click.option("--app-name", default="AetherPost", help="App name for demo")
def demo():
    """Show profile generation demo with sample data."""
    
    console.print(Panel(
        "[bold green]AetherPost Profile Generator Demo[/bold green]\n"
        "This demo shows how to generate optimized profiles for your app.",
        title="🎭 Profile Demo"
    ))
    
    # Sample project info
    sample_project = {
        "name": "AetherPost",
        "description": "Social media automation for developers",
        "github_url": "https://github.com/fununnn/autopromo",
        "website_url": "https://autopromo.dev",
        "location": "San Francisco, CA",
        "language": "Python",
        "tech_stack": ["Python", "FastAPI", "React", "AWS", "OpenAI"],
        "features": ["automation", "AI-powered", "multi-platform"]
    }
    
    generator = ProfileGenerator()
    
    # Generate profiles for main platforms
    demo_platforms = ["twitter", "instagram", "linkedin", "github"]
    
    console.print(f"\n🚀 Generating demo profiles for {len(demo_platforms)} platforms...")
    
    demo_profiles = []
    for platform in demo_platforms:
        try:
            profile = generator.generate_profile(platform, sample_project, "friendly")
            demo_profiles.append(profile)
        except Exception as e:
            console.print(f"❌ Failed to generate {platform}: {e}")
    
    # Show results
    if demo_profiles:
        console.print(f"\n✅ Generated {len(demo_profiles)} demo profiles:")
        
        for profile in demo_profiles:
            _show_detailed_profile(profile)
        
        # Show export capability
        console.print("\n[bold cyan]Export Capability:[/bold cyan]")
        console.print("• Individual .txt files for each platform")
        console.print("• Combined .md file with all profiles")
        console.print("• Setup checklist for manual updates")
        console.print("• Copy-paste ready format")
        
        if Confirm.ask("\nExport demo files?", default=False):
            exporter = ProfileExporter()
            exported_files = exporter.export_to_copyable_files(demo_profiles, "AetherPost")
            console.print(f"📁 Demo files saved to [cyan]./.aetherpost/profiles/[/cyan]")

@profile.command()
@click.argument("project_path", type=click.Path(exists=True))
def detect(project_path):
    """Detect project information from source code."""
    
    generator = ProfileGenerator()
    
    console.print(f"🔍 Analyzing project at: [cyan]{project_path}[/cyan]")
    
    try:
        project_info = generator.extract_project_info(project_path)
        
        console.print("\n📊 Detected Information:")
        
        info_table = Table(show_header=True, header_style="bold magenta")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value")
        
        for key, value in project_info.items():
            if value:
                if isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value[:5])
                    if len(value) > 5:
                        value_str += f" (+{len(value)-5} more)"
                else:
                    value_str = str(value)
                
                info_table.add_row(key.replace("_", " ").title(), value_str)
        
        console.print(info_table)
        
        if Confirm.ask("\nGenerate profiles with this information?", default=True):
            # Auto-generate with detected info
            selected_platforms = ["twitter", "instagram", "linkedin", "github"]
            generated_profiles = []
            
            for platform in selected_platforms:
                try:
                    profile = generator.generate_profile(platform, project_info, "friendly")
                    generated_profiles.append(profile)
                except Exception as e:
                    console.print(f"❌ Failed to generate {platform}: {e}")
            
            if generated_profiles:
                console.print(f"\n✅ Generated {len(generated_profiles)} profiles!")
                
                # Quick preview
                for profile in generated_profiles[:2]:  # Show first 2
                    _show_detailed_profile(profile)
                
                if len(generated_profiles) > 2:
                    console.print(f"... and {len(generated_profiles) - 2} more")
                
                # Export
                if Confirm.ask("\nExport to files?", default=True):
                    exporter = ProfileExporter()
                    exported_files = exporter.export_to_copyable_files(generated_profiles, project_info["name"])
                    console.print(f"📁 Files saved to [cyan]./.aetherpost/profiles/[/cyan]")
    
    except Exception as e:
        print_error(f"Failed to analyze project: {e}")

if __name__ == "__main__":
    profile()