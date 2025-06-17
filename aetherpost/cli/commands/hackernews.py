"""Hacker News posting automation for technical projects."""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from aetherpost.core.content.strategy import PlatformContentStrategy, ContentType
import logging
from aetherpost.cli.utils.ui import create_status_panel, print_success, print_error, print_warning

logger = logging.getLogger(__name__)
console = Console()

@dataclass
class HackerNewsPost:
    """Hacker News post structure."""
    title: str
    url: Optional[str] = None
    text: Optional[str] = None
    post_type: str = "story"  # story, ask, show
    optimal_time: Optional[datetime] = None

@dataclass
class HNSubmissionGuidelines:
    """Hacker News submission guidelines and best practices."""
    title_max_length: int = 80
    title_guidelines: List[str] = field(default_factory=list)
    content_guidelines: List[str] = field(default_factory=list)
    optimal_times: List[str] = field(default_factory=list)
    avoid_patterns: List[str] = field(default_factory=list)
    success_patterns: List[str] = field(default_factory=list)

class HackerNewsManager:
    """Manage Hacker News submissions for technical projects."""
    
    def __init__(self):
        self.strategy = PlatformContentStrategy()
        self.guidelines = self._load_hn_guidelines()
        self.submission_history = []
    
    def _load_hn_guidelines(self) -> HNSubmissionGuidelines:
        """Load Hacker News submission guidelines."""
        return HNSubmissionGuidelines(
            title_max_length=80,
            title_guidelines=[
                "Be specific and descriptive",
                "Avoid clickbait or hyperbole",
                "Include what the project does",
                "Mention if it's open source",
                "Use technical language appropriately",
                "Don't use ALL CAPS or excessive punctuation",
                "Include 'Show HN:' prefix for projects",
                "Be honest about what it is"
            ],
            content_guidelines=[
                "Explain the technical problem you solved",
                "Include implementation details",
                "Mention interesting technical challenges",
                "Be transparent about limitations",
                "Explain why you built it",
                "Include relevant links (GitHub, demo, docs)",
                "Engage genuinely with comments",
                "Don't be overly promotional"
            ],
            optimal_times=[
                "08:00-10:00 EST (weekdays)",
                "14:00-16:00 EST (weekdays)", 
                "10:00-12:00 EST (weekends)"
            ],
            avoid_patterns=[
                "Marketing speak",
                "Excessive self-promotion",
                "Vague descriptions",
                "Missing technical details",
                "Broken or slow links",
                "No engagement with comments",
                "Duplicate submissions"
            ],
            success_patterns=[
                "Clear technical value proposition",
                "Open source projects",
                "Novel technical approaches",
                "Solving real developer problems",
                "Good documentation",
                "Active community engagement",
                "Interesting technical stories"
            ]
        )
    
    def generate_hn_title(self, context: Dict[str, Any]) -> str:
        """Generate Hacker News optimized title."""
        app_name = context.get("app_name", "AetherPost")
        description = context.get("description", "Social media automation for developers")
        is_open_source = context.get("open_source", True)
        
        # Different title patterns based on project type
        patterns = [
            f"Show HN: {app_name} – {description}",
            f"Show HN: {app_name}, {description}",
            f"{app_name}: {description}",
            f"Show HN: I built {app_name} to automate social media for developers"
        ]
        
        # Add open source indicator
        if is_open_source:
            patterns.extend([
                f"Show HN: {app_name} – Open source {description.lower()}",
                f"Show HN: {app_name} (open source) – {description}"
            ])
        
        # Choose best pattern based on length
        for pattern in patterns:
            if len(pattern) <= self.guidelines.title_max_length:
                return pattern
        
        # Fallback: truncate if all are too long
        return patterns[0][:self.guidelines.title_max_length-3] + "..."
    
    def generate_hn_description(self, context: Dict[str, Any]) -> str:
        """Generate Hacker News post description."""
        app_name = context.get("app_name", "AetherPost")
        
        # Template for HN description
        template = """I built {app_name} to solve the problem of time-consuming social media management for developers.

**The Problem:**
As developers, we spend too much time crafting social media posts instead of coding. Manual posting across platforms is time-consuming and inconsistent.

**The Solution:**
{app_name} automates your social media with a developer-first approach:
• CLI-based workflow that integrates with your development process
• Multi-platform support (Twitter, Instagram, Reddit, YouTube, etc.)
• AI-powered content generation optimized for each platform
• Git integration for automatic release announcements
• Smart scheduling based on audience analytics

**Technical Highlights:**
• Built with Python/FastAPI backend and React frontend
• AWS serverless architecture for scalability
• Robust API rate limiting and error handling
• Plugin architecture for extensibility
• Comprehensive test coverage

**What makes it different:**
Unlike traditional social media tools, this is built specifically for developers and technical projects. It understands GitHub releases, package.json files, and developer workflows.

{github_link}
{demo_link}

I'd love to hear your thoughts and feedback from the HN community!"""

        github_link = f"GitHub: {context.get('github_url', 'https://github.com/fununnn/autopromo')}"
        demo_link = f"Demo: {context.get('demo_url', '#')}" if context.get('demo_url') else ""
        
        return template.format(
            app_name=app_name,
            github_link=github_link,
            demo_link=demo_link
        ).strip()
    
    def validate_hn_submission(self, title: str, content: str, url: Optional[str] = None) -> Dict[str, Any]:
        """Validate submission against HN guidelines."""
        issues = []
        warnings = []
        suggestions = []
        
        # Title validation
        if len(title) > self.guidelines.title_max_length:
            issues.append(f"Title too long ({len(title)} chars, max {self.guidelines.title_max_length})")
        
        if title.isupper():
            issues.append("Title should not be in ALL CAPS")
        
        if any(word in title.lower() for word in ["amazing", "incredible", "revolutionary", "game-changing"]):
            warnings.append("Avoid hyperbolic language in title")
        
        if not title.startswith("Show HN:") and not title.startswith("Ask HN:"):
            suggestions.append("Consider adding 'Show HN:' prefix for project submissions")
        
        # Content validation
        if content:
            if len(content) < 200:
                warnings.append("Content might be too short for good engagement")
            
            if "github" not in content.lower() and "repo" not in content.lower():
                suggestions.append("Consider including GitHub repository link")
            
            if content.count("!") > 3:
                warnings.append("Reduce exclamation marks for professional tone")
        
        # URL validation
        if url:
            if "localhost" in url or "127.0.0.1" in url:
                issues.append("URL appears to be localhost - use public URL")
        
        score = 100
        score -= len(issues) * 20
        score -= len(warnings) * 10
        score = max(0, score)
        
        return {
            "score": score,
            "issues": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "is_submittable": len(issues) == 0
        }
    
    def suggest_optimal_timing(self) -> Dict[str, Any]:
        """Suggest optimal timing for HN submission."""
        now = datetime.now()
        
        # Calculate next optimal time slots
        optimal_slots = []
        
        for day_offset in range(7):
            target_date = now + timedelta(days=day_offset)
            
            # Skip weekends for main submissions (less traffic)
            if target_date.weekday() >= 5:  # Saturday, Sunday
                continue
            
            # Add time slots for this day
            for time_str in ["08:00", "14:00"]:
                hour, minute = map(int, time_str.split(":"))
                slot_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if slot_time > now:
                    optimal_slots.append({
                        "datetime": slot_time,
                        "reason": f"Peak activity time on {slot_time.strftime('%A')}",
                        "score": 90 if time_str == "08:00" else 85
                    })
        
        return {
            "next_optimal": optimal_slots[0] if optimal_slots else None,
            "all_slots": optimal_slots[:5],  # Next 5 opportunities
            "guidelines": self.guidelines.optimal_times
        }
    
    def analyze_competition(self, keywords: List[str]) -> Dict[str, Any]:
        """Analyze recent submissions with similar keywords."""
        # Simulate analysis of recent HN submissions
        # In real implementation, this would call HN API
        
        return {
            "recent_similar": 2,
            "last_similar_date": "2024-01-10",
            "recommendation": "Good timing - no recent similar submissions",
            "competing_keywords": keywords[:3]
        }
    
    def create_submission_package(self, context: Dict[str, Any]) -> HackerNewsPost:
        """Create complete HN submission package."""
        title = self.generate_hn_title(context)
        description = self.generate_hn_description(context)
        
        # Determine if it's a URL or text post
        github_url = context.get("github_url")
        demo_url = context.get("demo_url")
        
        if demo_url:
            # URL post with demo
            return HackerNewsPost(
                title=title,
                url=demo_url,
                post_type="story"
            )
        elif github_url:
            # URL post with GitHub
            return HackerNewsPost(
                title=title,
                url=github_url,
                post_type="story"
            )
        else:
            # Text post with description
            return HackerNewsPost(
                title=title,
                text=description,
                post_type="story"
            )
    
    def generate_follow_up_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategy for engaging with HN comments."""
        return {
            "response_guidelines": [
                "Respond quickly to initial comments (first 30 minutes critical)",
                "Be technical and specific in responses",
                "Thank people for feedback genuinely",
                "Address criticism constructively",
                "Share additional technical details when asked",
                "Don't be defensive about limitations",
                "Offer to help with setup questions"
            ],
            "preparation": [
                "Have technical details ready to share",
                "Prepare answers for common questions",
                "Set up notifications for comments",
                "Clear your calendar for 2-3 hours after posting",
                "Have additional resources/links ready"
            ],
            "engagement_tactics": [
                "Ask for specific feedback in comments",
                "Share interesting implementation challenges",
                "Mention future roadmap items",
                "Connect with other developers in comments"
            ]
        }

@click.group(name="hackernews")
@click.pass_context  
def hackernews(ctx):
    """Hacker News posting automation and optimization."""
    ctx.ensure_object(dict)

@hackernews.command()
@click.option("--app-name", default="AetherPost", help="Name of your app")
@click.option("--description", help="Brief description of your app")
@click.option("--github-url", help="GitHub repository URL")
@click.option("--demo-url", help="Demo/website URL")
@click.option("--open-source", is_flag=True, default=True, help="Is this open source?")
def generate(app_name, description, github_url, demo_url, open_source):
    """Generate optimized Hacker News submission."""
    manager = HackerNewsManager()
    
    context = {
        "app_name": app_name,
        "description": description or f"{app_name} automates social media for developers",
        "github_url": github_url,
        "demo_url": demo_url,
        "open_source": open_source
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Generating HN submission...", total=None)
        
        try:
            submission = manager.create_submission_package(context)
            progress.update(task, description="Submission generated!")
            
            # Validate submission
            if submission.text:
                validation = manager.validate_hn_submission(submission.title, submission.text)
            else:
                validation = manager.validate_hn_submission(submission.title, "", submission.url)
            
            # Display submission
            console.print(Panel(
                f"[bold green]Title:[/bold green]\n{submission.title}\n\n" +
                (f"[bold green]URL:[/bold green]\n{submission.url}\n\n" if submission.url else "") +
                (f"[bold green]Text:[/bold green]\n{submission.text[:500]}..." if submission.text else ""),
                title="Generated HN Submission"
            ))
            
            # Display validation results
            validation_color = "green" if validation["is_submittable"] else "red"
            console.print(Panel(
                f"[bold {validation_color}]Validation Score: {validation['score']}/100[/bold {validation_color}]\n\n" +
                (f"[bold red]Issues:[/bold red]\n" + "\n".join(f"• {issue}" for issue in validation['issues']) + "\n\n" if validation['issues'] else "") +
                (f"[bold yellow]Warnings:[/bold yellow]\n" + "\n".join(f"• {warning}" for warning in validation['warnings']) + "\n\n" if validation['warnings'] else "") +
                (f"[bold blue]Suggestions:[/bold blue]\n" + "\n".join(f"• {suggestion}" for suggestion in validation['suggestions']) if validation['suggestions'] else ""),
                title="Submission Validation"
            ))
            
        except Exception as e:
            print_error(f"Error generating submission: {e}")

@hackernews.command()
@click.option("--title", required=True, help="Submission title")
@click.option("--content", help="Submission content (for text posts)")
@click.option("--url", help="Submission URL (for link posts)")
def validate(title, content, url):
    """Validate submission against HN guidelines."""
    manager = HackerNewsManager()
    
    validation = manager.validate_hn_submission(title, content or "", url)
    
    validation_color = "green" if validation["is_submittable"] else "red"
    console.print(Panel(
        f"[bold {validation_color}]Validation Score: {validation['score']}/100[/bold {validation_color}]\n\n" +
        f"[bold]Title Length:[/bold] {len(title)}/{manager.guidelines.title_max_length}\n\n" +
        (f"[bold red]Issues:[/bold red]\n" + "\n".join(f"• {issue}" for issue in validation['issues']) + "\n\n" if validation['issues'] else "") +
        (f"[bold yellow]Warnings:[/bold yellow]\n" + "\n".join(f"• {warning}" for warning in validation['warnings']) + "\n\n" if validation['warnings'] else "") +
        (f"[bold blue]Suggestions:[/bold blue]\n" + "\n".join(f"• {suggestion}" for suggestion in validation['suggestions']) if validation['suggestions'] else ""),
        title="HN Submission Validation"
    ))

@hackernews.command()
def timing():
    """Get optimal timing suggestions for HN submission."""
    manager = HackerNewsManager()
    timing_data = manager.suggest_optimal_timing()
    
    if timing_data["next_optimal"]:
        next_time = timing_data["next_optimal"]["datetime"]
        console.print(Panel(
            f"[bold green]Next Optimal Time:[/bold green]\n"
            f"{next_time.strftime('%A, %B %d at %I:%M %p EST')}\n"
            f"({timing_data['next_optimal']['reason']})\n\n"
            f"[bold blue]Time until optimal:[/bold blue] "
            f"{next_time - datetime.now()}".split('.')[0],
            title="Optimal Posting Time"
        ))
    
    # Show upcoming opportunities
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Date/Time", style="cyan")
    table.add_column("Day")
    table.add_column("Reason")
    table.add_column("Score", justify="right")
    
    for slot in timing_data["all_slots"]:
        dt = slot["datetime"]
        table.add_row(
            dt.strftime("%m/%d %I:%M %p"),
            dt.strftime("%A"),
            slot["reason"],
            f"{slot['score']}/100"
        )
    
    console.print(table)

@hackernews.command()
def guidelines():
    """Show Hacker News submission guidelines."""
    manager = HackerNewsManager()
    guidelines = manager.guidelines
    
    console.print(Panel(
        f"[bold green]Title Guidelines:[/bold green]\n" +
        "\n".join(f"• {guideline}" for guideline in guidelines.title_guidelines) +
        f"\n\n[bold green]Content Guidelines:[/bold green]\n" +
        "\n".join(f"• {guideline}" for guideline in guidelines.content_guidelines) +
        f"\n\n[bold yellow]Avoid These Patterns:[/bold yellow]\n" +
        "\n".join(f"• {pattern}" for pattern in guidelines.avoid_patterns) +
        f"\n\n[bold blue]Success Patterns:[/bold blue]\n" +
        "\n".join(f"• {pattern}" for pattern in guidelines.success_patterns),
        title="HN Submission Guidelines"
    ))

@hackernews.command()
@click.option("--app-name", default="AetherPost", help="Name of your app")
def strategy(app_name):
    """Get complete engagement strategy for HN submission."""
    manager = HackerNewsManager()
    
    context = {"app_name": app_name}
    strategy_data = manager.generate_follow_up_strategy(context)
    
    console.print(Panel(
        f"[bold green]Response Guidelines:[/bold green]\n" +
        "\n".join(f"• {guideline}" for guideline in strategy_data['response_guidelines']) +
        f"\n\n[bold yellow]Preparation Checklist:[/bold yellow]\n" +
        "\n".join(f"• {item}" for item in strategy_data['preparation']) +
        f"\n\n[bold blue]Engagement Tactics:[/bold blue]\n" +
        "\n".join(f"• {tactic}" for tactic in strategy_data['engagement_tactics']),
        title="HN Engagement Strategy"
    ))

if __name__ == "__main__":
    hackernews()