"""Content preview and notification management commands."""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from aetherpost.core.preview.generator import ContentPreviewGenerator, PreviewSession, PreviewContent
from aetherpost.core.preview.notifiers import (
    PreviewNotificationManager, 
    NotificationChannel,
    notification_manager
)
import logging
from aetherpost.cli.utils.ui import create_status_panel, print_success, print_error, print_warning

logger = logging.getLogger(__name__)
console = Console()

@click.group(name="preview")
@click.pass_context
def preview(ctx):
    """Content preview and notification management."""
    ctx.ensure_object(dict)

@preview.command()
@click.option("--campaign-name", "-c", required=True, help="Campaign name")
@click.option("--platform", "-p", multiple=True, help="Platforms to preview (can specify multiple)")
@click.option("--content-type", default="announcement", help="Content type")
@click.option("--text", "-t", help="Content text")
@click.option("--title", help="Content title (for platforms that support it)")
@click.option("--hashtags", help="Hashtags (comma-separated)")
@click.option("--output", "-o", help="Output file path")
@click.option("--format", "output_format", type=click.Choice(['markdown', 'json', 'html']), 
              default='markdown', help="Output format")
@click.option("--notify", is_flag=True, help="Send notifications to configured channels")
def generate(campaign_name, platform, content_type, text, title, hashtags, output, output_format, notify):
    """Generate content preview for review."""
    
    generator = ContentPreviewGenerator()
    
    # Parse hashtags
    hashtag_list = []
    if hashtags:
        hashtag_list = [tag.strip().lstrip('#') for tag in hashtags.split(',') if tag.strip()]
    
    # Default platforms if none specified
    if not platform:
        platform = ['twitter', 'instagram', 'reddit']
    
    # Default content if none specified
    if not text:
        text = f"Exciting update from {campaign_name}! Check out our latest features and improvements."
    
    # Create content items
    content_items = []
    for plat in platform:
        content_items.append({
            "platform": plat,
            "content_type": content_type,
            "title": title,
            "text": text,
            "hashtags": hashtag_list,
            "media_urls": [],
            "scheduled_time": None
        })
    
    # Create preview session
    session = generator.create_preview_session(campaign_name, content_items)
    
    # Display preview in console
    console.print(Panel(
        f"[bold green]Preview Generated[/bold green]\n\n"
        f"Campaign: {session.campaign_name}\n"
        f"Session ID: {session.session_id}\n"
        f"Platforms: {session.total_platforms}\n"
        f"Estimated Reach: {session.total_estimated_reach:,}",
        title="Content Preview"
    ))
    
    # Show platform breakdown
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Platform", style="cyan")
    table.add_column("Characters")
    table.add_column("Est. Reach", justify="right")
    table.add_column("Engagement", justify="right")
    table.add_column("Status")
    
    for item in session.content_items:
        char_display = str(item.character_count)
        if item.character_limit:
            char_display += f"/{item.character_limit}"
            if item.character_count > item.character_limit:
                status = "⚠️ Over Limit"
            elif item.character_count > item.character_limit * 0.9:
                status = "⚠️ Near Limit"
            else:
                status = "✅ Good"
        else:
            status = "✅ Good"
        
        table.add_row(
            item.platform.title(),
            char_display,
            f"{item.estimated_reach:,}",
            f"{item.engagement_prediction:.1%}",
            status
        )
    
    console.print(table)
    
    # Save to file if requested
    if output:
        if output_format == "markdown":
            file_path = generator.save_preview_to_file(session, output, "markdown")
        elif output_format == "json":
            file_path = generator.save_preview_to_file(session, output, "json")
        elif output_format == "html":
            html_content = generator.generate_html_email_preview(session)
            file_path = output if output.endswith('.html') else f"{output}.html"
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        print_success(f"Preview saved to: {file_path}")
    
    # Send notifications if requested
    if notify:
        async def send_notifications():
            results = await notification_manager.send_preview_to_all(session)
            
            success_count = sum(1 for r in results.values() if r.get("status") == "success")
            total_count = len(results)
            
            if success_count > 0:
                print_success(f"Notifications sent to {success_count}/{total_count} channels")
            else:
                print_warning("No notifications were sent successfully")
            
            for channel_name, result in results.items():
                status_icon = "✅" if result.get("status") == "success" else "❌"
                console.print(f"  {status_icon} {channel_name}: {result.get('message', 'Unknown')}")
        
        asyncio.run(send_notifications())

@preview.command()
@click.option("--name", required=True, help="Channel name")
@click.option("--type", "channel_type", required=True, 
              type=click.Choice(['slack', 'discord', 'teams', 'email', 'webhook']),
              help="Channel type")
@click.option("--webhook-url", help="Webhook URL (for Slack, Discord, Teams, webhook)")
@click.option("--email", multiple=True, help="Email recipients (can specify multiple)")
@click.option("--channel-id", help="Channel ID (for Slack)")
def add_channel(name, channel_type, webhook_url, email, channel_id):
    """Add notification channel for previews."""
    
    # Validate required parameters
    if channel_type in ['slack', 'discord', 'teams', 'webhook'] and not webhook_url:
        print_error(f"{channel_type.title()} channel requires --webhook-url")
        return
    
    if channel_type == 'email' and not email:
        print_error("Email channel requires at least one --email recipient")
        return
    
    # Create channel
    channel = NotificationChannel(
        name=name,
        type=channel_type,
        webhook_url=webhook_url,
        email_recipients=list(email) if email else None,
        channel_id=channel_id,
        enabled=True
    )
    
    # Add to manager
    notification_manager.add_channel(channel)
    
    print_success(f"Added {channel_type} notification channel: {name}")
    
    # Show configuration
    console.print(Panel(
        f"[bold]Channel Configuration[/bold]\n\n"
        f"Name: {channel.name}\n"
        f"Type: {channel.type}\n" +
        (f"Webhook URL: {channel.webhook_url}\n" if channel.webhook_url else "") +
        (f"Email Recipients: {', '.join(channel.email_recipients)}\n" if channel.email_recipients else "") +
        (f"Channel ID: {channel.channel_id}\n" if channel.channel_id else "") +
        f"Enabled: {channel.enabled}",
        title="Channel Added"
    ))

@preview.command()
@click.option("--name", required=True, help="Channel name to remove")
def remove_channel(name):
    """Remove notification channel."""
    
    if notification_manager.remove_channel(name):
        print_success(f"Removed notification channel: {name}")
    else:
        print_error(f"Channel not found: {name}")

@preview.command()
def list_channels():
    """List configured notification channels."""
    
    channels = notification_manager.channels
    
    if not channels:
        console.print("No notification channels configured.")
        console.print("\nAdd channels using: [cyan]aetherpost preview add-channel[/cyan]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("Configuration")
    table.add_column("Status")
    
    for channel in channels:
        config_text = ""
        if channel.webhook_url:
            config_text = f"Webhook: {channel.webhook_url[:50]}..."
        elif channel.email_recipients:
            config_text = f"Email: {', '.join(channel.email_recipients[:2])}"
            if len(channel.email_recipients) > 2:
                config_text += f" (+{len(channel.email_recipients)-2} more)"
        
        status = "🟢 Enabled" if channel.enabled else "🔴 Disabled"
        
        table.add_row(
            channel.name,
            channel.type.title(),
            config_text,
            status
        )
    
    console.print(table)

@preview.command()
@click.option("--name", required=True, help="Channel name")
@click.option("--enabled/--disabled", default=True, help="Enable or disable channel")
def toggle_channel(name, enabled):
    """Enable or disable notification channel."""
    
    channel = notification_manager.get_channel(name)
    if not channel:
        print_error(f"Channel not found: {name}")
        return
    
    channel.enabled = enabled
    notification_manager.save_configuration()
    
    status = "enabled" if enabled else "disabled"
    print_success(f"Channel {name} {status}")

@preview.command()
@click.option("--session-id", help="Test with specific session ID")
def test_notifications():
    """Test notification channels with sample preview."""
    
    # Create sample preview session
    generator = ContentPreviewGenerator()
    
    sample_content = [
        {
            "platform": "twitter",
            "content_type": "announcement",
            "text": "🚀 Excited to announce AetherPost v2.0! Now with enhanced automation, AI-powered content generation, and multi-platform support. Perfect for developers who want to automate their social media without the hassle. #AetherPost #DevTools #SocialMedia",
            "hashtags": ["AetherPost", "DevTools", "SocialMedia"],
            "media_urls": []
        },
        {
            "platform": "instagram", 
            "content_type": "announcement",
            "text": "🎉 AetherPost v2.0 is here! \n\nAfter months of development, we're thrilled to share our biggest update yet. New features include:\n\n✨ AI-powered content generation\n🤖 Smart scheduling optimization\n📊 Advanced analytics dashboard\n🔗 Multi-platform automation\n\nBuilt by developers, for developers. Because your time should be spent coding, not crafting social media posts.\n\n#AetherPost #DevLife #Productivity #SocialMediaAutomation #TechTools",
            "hashtags": ["AetherPost", "DevLife", "Productivity", "SocialMediaAutomation", "TechTools"],
            "media_urls": ["https://example.com/autopromo-v2-announcement.jpg"]
        }
    ]
    
    session = generator.create_preview_session("Test Campaign", sample_content)
    
    console.print(Panel(
        f"[bold yellow]Testing Notifications[/bold yellow]\n\n"
        f"Campaign: {session.campaign_name}\n"
        f"Session ID: {session.session_id}\n"
        f"Platforms: {session.total_platforms}",
        title="Notification Test"
    ))
    
    async def run_test():
        results = await notification_manager.send_preview_to_all(session)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Channel", style="cyan")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Message")
        
        for channel_name, result in results.items():
            channel = notification_manager.get_channel(channel_name)
            status_icon = "✅" if result.get("status") == "success" else "❌"
            status_text = f"{status_icon} {result.get('status', 'unknown').title()}"
            
            table.add_row(
                channel_name,
                channel.type.title() if channel else "Unknown",
                status_text,
                result.get("message", "No message")[:50] + "..." if len(result.get("message", "")) > 50 else result.get("message", "")
            )
        
        console.print(table)
        
        success_count = sum(1 for r in results.values() if r.get("status") == "success")
        total_count = len(results)
        
        if success_count == total_count and total_count > 0:
            print_success("All notification channels working correctly!")
        elif success_count > 0:
            print_warning(f"Some channels failed: {success_count}/{total_count} successful")
        else:
            print_error("All notification channels failed")
    
    if not notification_manager.channels:
        print_warning("No notification channels configured. Add some first:")
        console.print("  [cyan]aetherpost preview add-channel --name slack-team --type slack --webhook-url https://hooks.slack.com/...[/cyan]")
    else:
        asyncio.run(run_test())

@preview.command()
@click.option("--campaign-file", help="Load campaign from YAML file")
def demo():
    """Show preview system demonstration."""
    
    console.print(Panel(
        "[bold green]AetherPost Preview System Demo[/bold green]\n\n"
        "This demo shows how the preview system works:\n"
        "1. Generate content for multiple platforms\n"
        "2. Create rich previews with metrics\n"
        "3. Send notifications for approval\n"
        "4. Support multiple output formats",
        title="Preview Demo"
    ))
    
    # Create sample content
    generator = ContentPreviewGenerator()
    
    demo_content = [
        {
            "platform": "twitter",
            "content_type": "announcement",
            "text": "🚀 Big news! We just launched AetherPost v2.0 with AI-powered content generation. No more writer's block for developers! Try it now and automate your social media in minutes. #AetherPost #AI #DevTools",
            "hashtags": ["AetherPost", "AI", "DevTools"],
            "media_urls": []
        },
        {
            "platform": "reddit",
            "content_type": "community",
            "title": "Show HN: AetherPost v2.0 - AI-powered social media automation for developers",
            "text": "Hey everyone! I've been working on AetherPost for the past year, and I'm excited to share v2.0.\n\n**What it does:**\nAetherPost automates your social media posting across Twitter, Instagram, Reddit, YouTube, and more. It's designed specifically for developers and technical projects.\n\n**Key features:**\n• AI-powered content generation\n• Platform-specific optimization\n• Smart scheduling\n• Git integration for automatic release announcements\n• CLI-first approach\n\n**Why I built this:**\nAs a developer, I was spending way too much time on social media marketing instead of coding. I wanted something that understood developer workflows and could handle the marketing automatically.\n\n**What's new in v2.0:**\n• [AI Service]/GPT integration for content generation\n• Advanced analytics dashboard\n• Multi-language support\n• Better Reddit integration (like this post!)\n\nIt's open source and available at: https://github.com/fununnn/autopromo\n\nI'd love to hear your thoughts and feedback!",
            "hashtags": [],
            "media_urls": []
        },
        {
            "platform": "linkedin",
            "content_type": "professional",
            "text": "Excited to announce AetherPost v2.0! 🚀\n\nAfter a year of development and feedback from the developer community, we've launched our biggest update yet.\n\nKey improvements:\n✅ AI-powered content generation using [AI Service]/GPT\n✅ Smart scheduling based on audience analytics\n✅ Multi-platform optimization (Twitter, Instagram, Reddit, YouTube)\n✅ Seamless Git integration for release announcements\n✅ Advanced analytics and insights\n\nBuilt by developers, for developers. Because your time should be spent building amazing products, not crafting social media posts.\n\nTry it out and let me know what you think! Link in comments.\n\n#SocialMediaAutomation #DeveloperTools #ProductLaunch #OpenSource",
            "hashtags": ["SocialMediaAutomation", "DeveloperTools", "ProductLaunch", "OpenSource"],
            "media_urls": ["https://example.com/autopromo-linkedin-banner.jpg"]
        }
    ]
    
    session = generator.create_preview_session("AetherPost v2.0 Launch", demo_content)
    
    # Show preview in different formats
    console.print("\n[bold]1. Console Preview:[/bold]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Platform", style="cyan")
    table.add_column("Content Preview")
    table.add_column("Metrics")
    
    for item in session.content_items:
        content_preview = item.text[:100] + "..." if len(item.text) > 100 else item.text
        metrics = f"Reach: {item.estimated_reach:,}\nEng: {item.engagement_prediction:.1%}\nChars: {item.character_count}"
        
        table.add_row(
            item.platform.title(),
            content_preview,
            metrics
        )
    
    console.print(table)
    
    # Show markdown preview sample
    console.print("\n[bold]2. Markdown Preview Sample:[/bold]")
    markdown_preview = generator.generate_markdown_preview(session)
    console.print(Panel(
        markdown_preview[:500] + "\n\n[... truncated for demo ...]",
        title="Markdown Preview"
    ))
    
    # Save demo files
    console.print("\n[bold]3. Generated Files:[/bold]")
    
    demo_dir = Path("./demo_previews")
    demo_dir.mkdir(exist_ok=True)
    
    # Save markdown
    md_file = generator.save_preview_to_file(session, str(demo_dir / "demo_preview"), "markdown")
    console.print(f"📄 Markdown: {md_file}")
    
    # Save JSON
    json_file = generator.save_preview_to_file(session, str(demo_dir / "demo_preview"), "json")
    console.print(f"📊 JSON: {json_file}")
    
    # Save HTML
    html_content = generator.generate_html_email_preview(session)
    html_file = demo_dir / "demo_preview.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    console.print(f"🌐 HTML: {html_file}")
    
    console.print(f"\n[green]Demo completed! Check the files in {demo_dir}[/green]")

if __name__ == "__main__":
    preview()