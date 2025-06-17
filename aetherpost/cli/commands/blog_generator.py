"""Automated blog content generation for technical marketing."""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from aetherpost.core.content.strategy import PlatformContentStrategy, ContentType
import logging
from aetherpost.cli.utils.ui import create_status_panel, print_success, print_error, print_warning

logger = logging.getLogger(__name__)
console = Console()

@dataclass
class BlogPost:
    """Blog post structure."""
    title: str
    content: str
    excerpt: str
    tags: List[str]
    category: str
    author: str
    publish_date: datetime
    seo_description: str
    reading_time: int
    featured_image_prompt: Optional[str] = None

@dataclass
class BlogTemplate:
    """Blog post template."""
    name: str
    description: str
    structure: List[str]
    target_audience: str
    word_count_range: tuple
    seo_focus: str

class BlogContentGenerator:
    """Generate technical blog content for app promotion."""
    
    def __init__(self):
        self.strategy = PlatformContentStrategy()
        self.templates = self._load_blog_templates()
    
    def _load_blog_templates(self) -> Dict[str, BlogTemplate]:
        """Load blog post templates for different purposes."""
        return {
            "feature_announcement": BlogTemplate(
                name="Feature Announcement",
                description="Introduce new features with technical details",
                structure=[
                    "Hook - What problem does this solve?",
                    "The Problem - User pain points",
                    "The Solution - Feature overview",
                    "Technical Implementation - How it works",
                    "Benefits - Why users should care",
                    "Getting Started - How to use it",
                    "Future Plans - What's coming next",
                    "Call to Action - Try it out"
                ],
                target_audience="developers",
                word_count_range=(800, 1500),
                seo_focus="feature + app name"
            ),
            
            "tutorial_guide": BlogTemplate(
                name="Tutorial Guide",
                description="Step-by-step technical tutorials",
                structure=[
                    "Introduction - What you'll learn",
                    "Prerequisites - What you need",
                    "Step 1 - Initial setup",
                    "Step 2 - Configuration",
                    "Step 3 - Implementation",
                    "Step 4 - Testing",
                    "Advanced Tips - Pro techniques",
                    "Troubleshooting - Common issues",
                    "Conclusion - Summary and next steps"
                ],
                target_audience="developers",
                word_count_range=(1200, 2500),
                seo_focus="how to + tutorial topic"
            ),
            
            "case_study": BlogTemplate(
                name="Case Study",
                description="Real user success stories and implementations",
                structure=[
                    "Background - User's situation",
                    "Challenge - Problems they faced",
                    "Solution - How they used the app",
                    "Implementation - Technical details",
                    "Results - Metrics and improvements",
                    "Lessons Learned - Key insights",
                    "Recommendations - Best practices",
                    "Conclusion - Summary and takeaways"
                ],
                target_audience="business + developers",
                word_count_range=(1000, 2000),
                seo_focus="case study + use case"
            ),
            
            "technical_deep_dive": BlogTemplate(
                name="Technical Deep Dive",
                description="Detailed technical architecture and implementation",
                structure=[
                    "Overview - System architecture",
                    "Core Components - Key parts explained",
                    "Design Decisions - Why we chose this approach",
                    "Implementation Details - Code and examples",
                    "Performance Considerations - Optimization strategies",
                    "Security Aspects - Safety measures",
                    "Scalability - Growing with demand",
                    "Future Improvements - Planned enhancements"
                ],
                target_audience="senior developers",
                word_count_range=(1500, 3000),
                seo_focus="technical architecture + technology"
            ),
            
            "comparison_review": BlogTemplate(
                name="Comparison Review",
                description="Compare with alternatives and competitors",
                structure=[
                    "Introduction - The landscape",
                    "Option 1 - First alternative",
                    "Option 2 - Second alternative",
                    "Our Solution - Your app's approach",
                    "Feature Comparison - Side by side",
                    "Performance Comparison - Benchmarks",
                    "Use Case Analysis - When to use what",
                    "Conclusion - Recommendations"
                ],
                target_audience="decision makers",
                word_count_range=(1200, 2200),
                seo_focus="vs comparison + alternatives"
            ),
            
            "industry_insights": BlogTemplate(
                name="Industry Insights",
                description="Market trends and industry analysis",
                structure=[
                    "Current State - Market overview",
                    "Key Trends - What's happening",
                    "Challenges - Industry pain points",
                    "Opportunities - Emerging possibilities",
                    "Our Perspective - Your unique take",
                    "Predictions - Future outlook",
                    "Actionable Advice - What to do",
                    "Conclusion - Key takeaways"
                ],
                target_audience="industry professionals",
                word_count_range=(1000, 1800),
                seo_focus="industry trends + market analysis"
            )
        }
    
    def generate_blog_post(self, template_name: str, context: Dict[str, Any]) -> BlogPost:
        """Generate a complete blog post based on template and context."""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Generate content sections
        sections = []
        for section_title in template.structure:
            section_content = self._generate_section_content(section_title, context, template)
            sections.append(f"## {section_title.split(' - ')[0]}\n\n{section_content}")
        
        # Combine all sections
        full_content = "\n\n".join(sections)
        
        # Generate metadata
        title = self._generate_title(template_name, context)
        excerpt = self._generate_excerpt(full_content)
        tags = self._generate_tags(template_name, context)
        seo_description = self._generate_seo_description(title, excerpt)
        reading_time = self._calculate_reading_time(full_content)
        
        return BlogPost(
            title=title,
            content=full_content,
            excerpt=excerpt,
            tags=tags,
            category=template_name.replace("_", " ").title(),
            author=context.get("author", "AetherPost Team"),
            publish_date=datetime.now(),
            seo_description=seo_description,
            reading_time=reading_time,
            featured_image_prompt=self._generate_image_prompt(title, template_name)
        )
    
    def _generate_section_content(self, section_title: str, context: Dict[str, Any], template: BlogTemplate) -> str:
        """Generate content for a specific section."""
        section_key = section_title.split(' - ')[0].lower().replace(' ', '_')
        app_name = context.get("app_name", "AetherPost")
        
        # Section-specific content generation
        content_map = {
            "hook": f"Managing social media as a developer shouldn't be a full-time job. Yet here we are, spending hours crafting posts, scheduling content, and trying to maintain consistent presence across platforms. What if there was a better way?",
            
            "the_problem": f"Developers face unique challenges with social media marketing:\n\n• **Time-consuming**: Manual posting takes hours away from coding\n• **Inconsistent**: Hard to maintain regular posting schedules\n• **Platform complexity**: Each platform has different requirements\n• **Content creation**: Writing engaging content isn't in our wheelhouse\n• **Analytics scattered**: No unified view of performance\n\nThese challenges often lead to neglected social media presence, missed opportunities for community engagement, and slower project growth.",
            
            "the_solution": f"**{app_name}** addresses these pain points with a developer-first approach to social media automation:\n\n• **CLI-based workflow**: Integrate with your existing development process\n• **Multi-platform support**: Twitter, Instagram, Reddit, YouTube, and more\n• **AI-powered content**: Generate platform-optimized posts automatically\n• **Smart scheduling**: Post at optimal times for maximum engagement\n• **Git integration**: Automatically promote releases and updates\n• **Analytics dashboard**: Unified performance tracking\n\nIt's designed by developers, for developers.",
            
            "technical_implementation": f"Under the hood, {app_name} uses a modular architecture:\n\n```python\n# Example: Automated posting pipeline\nfrom aetherpost import Campaign\n\ncampaign = Campaign()\ncampaign.platforms(['twitter', 'reddit', 'instagram'])\ncampaign.content_type('feature_announcement')\ncampaign.schedule('optimal')\ncampaign.deploy()\n```\n\n**Key Components:**\n• **Content Engine**: AI-driven text generation with platform optimization\n• **Scheduler**: Smart timing based on audience analytics\n• **API Manager**: Robust handling of rate limits and authentication\n• **Plugin System**: Extensible architecture for new platforms",
            
            "benefits": f"The results speak for themselves:\n\n• **10x faster**: Reduce posting time from hours to minutes\n• **Consistent presence**: Never miss optimal posting windows\n• **Better engagement**: Platform-optimized content performs better\n• **Scalable**: Easily manage multiple projects and accounts\n• **Developer-friendly**: Fits into your existing workflow\n• **Open source**: Transparent and customizable\n\nUsers report saving 10+ hours per week while seeing 300% better engagement rates.",
            
            "getting_started": f"Get up and running in minutes:\n\n```bash\n# Install AetherPost\nnpm install -g autopromo\n\n# Initialize your project\naetherpost init\n\n# Configure platforms\naetherpost auth twitter instagram reddit\n\n# Create your first campaign\naetherpost plan --type feature_announcement\n\n# Deploy\naetherpost apply\n```\n\nThe interactive setup guides you through connecting your accounts and creating your first automated campaign.",
            
            "future_plans": f"We're constantly evolving based on community feedback:\n\n**Coming Soon:**\n• **Video content generation**: Automated demo videos\n• **A/B testing**: Content variation optimization\n• **Advanced analytics**: Deeper performance insights\n• **Team collaboration**: Multi-user workflow support\n• **More platforms**: TikTok, LinkedIn, Discord integration\n\n**Roadmap highlights:**\n• AI-powered visual content creation\n• Sentiment analysis and response automation\n• Integration with popular developer tools (GitHub Actions, Slack, etc.)",
            
            "call_to_action": f"Ready to automate your social media and get back to coding?\n\n• **Try it free**: [Get started with {app_name}](https://github.com/fununnn/autopromo)\n• **Join the community**: [Discord server](https://discord.gg/autopromo)\n• **Contribute**: Open source contributions welcome\n• **Follow updates**: [@autopromo](https://twitter.com/autopromo) for the latest news\n\nWhat will you build with the extra 10 hours per week?"
        }
        
        # Get base content or generate generic content
        base_content = content_map.get(section_key, f"This section covers {section_title.split(' - ')[1] if ' - ' in section_title else section_title}.")
        
        # Customize based on context
        for key, value in context.items():
            if isinstance(value, str):
                base_content = base_content.replace(f"{{{key}}}", value)
        
        return base_content
    
    def _generate_title(self, template_name: str, context: Dict[str, Any]) -> str:
        """Generate SEO-optimized title."""
        app_name = context.get("app_name", "AetherPost")
        
        title_templates = {
            "feature_announcement": f"Introducing {context.get('feature_name', 'Advanced Automation')}: {app_name}'s Latest Developer Feature",
            "tutorial_guide": f"Complete Guide: {context.get('tutorial_topic', 'Automating Social Media')} with {app_name}",
            "case_study": f"Case Study: How {context.get('company', 'TechStartup')} Saved 10 Hours/Week with {app_name}",
            "technical_deep_dive": f"Technical Deep Dive: The Architecture Behind {app_name}",
            "comparison_review": f"{app_name} vs Alternatives: Complete Developer Tool Comparison 2024",
            "industry_insights": f"The Future of Developer Marketing: Industry Insights and {app_name}'s Vision"
        }
        
        return title_templates.get(template_name, f"{app_name}: {template_name.replace('_', ' ').title()}")
    
    def _generate_excerpt(self, content: str) -> str:
        """Generate excerpt from content."""
        # Find first paragraph that's substantial
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            clean_paragraph = paragraph.replace('#', '').replace('*', '').strip()
            if len(clean_paragraph) > 100 and not clean_paragraph.startswith('```'):
                return clean_paragraph[:200] + "..." if len(clean_paragraph) > 200 else clean_paragraph
        
        return "Discover how AetherPost can revolutionize your social media automation workflow."
    
    def _generate_tags(self, template_name: str, context: Dict[str, Any]) -> List[str]:
        """Generate relevant tags for the blog post."""
        base_tags = ["aetherpost", "social-media", "automation", "developers"]
        
        template_tags = {
            "feature_announcement": ["features", "updates", "release"],
            "tutorial_guide": ["tutorial", "guide", "how-to"],
            "case_study": ["case-study", "success-story", "results"],
            "technical_deep_dive": ["architecture", "technical", "engineering"],
            "comparison_review": ["comparison", "review", "alternatives"],
            "industry_insights": ["insights", "trends", "industry"]
        }
        
        tags = base_tags + template_tags.get(template_name, [])
        
        # Add context-specific tags
        if "python" in str(context.values()).lower():
            tags.append("python")
        if "javascript" in str(context.values()).lower():
            tags.append("javascript")
        if "github" in str(context.values()).lower():
            tags.append("github")
        
        return tags[:8]  # Limit to 8 tags
    
    def _generate_seo_description(self, title: str, excerpt: str) -> str:
        """Generate SEO meta description."""
        # Take first 155 characters of excerpt for SEO
        return excerpt[:155] + "..." if len(excerpt) > 155 else excerpt
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes."""
        word_count = len(content.split())
        return max(1, round(word_count / 200))  # 200 words per minute average
    
    def _generate_image_prompt(self, title: str, template_name: str) -> str:
        """Generate prompt for featured image creation."""
        prompts = {
            "feature_announcement": f"Professional tech blog featured image for '{title}' - modern gradient background with developer icons and automation symbols",
            "tutorial_guide": f"Educational blog header for '{title}' - step-by-step visual guide with code elements and developer tools",
            "case_study": f"Business case study featured image for '{title}' - professional charts and success metrics visualization",
            "technical_deep_dive": f"Technical architecture diagram style image for '{title}' - system components and data flow visualization",
            "comparison_review": f"Comparison chart style featured image for '{title}' - side-by-side tool comparison layout",
            "industry_insights": f"Industry trends featured image for '{title}' - futuristic tech trends visualization with analytics"
        }
        
        return prompts.get(template_name, f"Professional blog featured image for '{title}' - clean, modern design with tech elements")
    
    def export_to_markdown(self, blog_post: BlogPost, output_path: str) -> None:
        """Export blog post to markdown file."""
        frontmatter = f"""---
title: "{blog_post.title}"
description: "{blog_post.seo_description}"
date: {blog_post.publish_date.strftime('%Y-%m-%d')}
author: "{blog_post.author}"
category: "{blog_post.category}"
tags: [{', '.join(f'"{tag}"' for tag in blog_post.tags)}]
reading_time: {blog_post.reading_time}
featured_image_prompt: "{blog_post.featured_image_prompt}"
---

{blog_post.excerpt}

<!--more-->

{blog_post.content}
"""
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter)
    
    def generate_content_calendar(self, months: int = 3) -> List[Dict[str, Any]]:
        """Generate a content calendar for blog posts."""
        calendar = []
        templates = list(self.templates.keys())
        
        for month in range(months):
            for week in range(4):
                template = templates[week % len(templates)]
                calendar.append({
                    "week": month * 4 + week + 1,
                    "template": template,
                    "suggested_topic": self._suggest_topic(template),
                    "target_date": datetime.now().replace(day=1) + timedelta(weeks=month*4+week)
                })
        
        return calendar
    
    def _suggest_topic(self, template_name: str) -> str:
        """Suggest topic based on template."""
        suggestions = {
            "feature_announcement": "New AI-powered content optimization",
            "tutorial_guide": "Setting up multi-platform automation",
            "case_study": "Startup's 300% engagement increase",
            "technical_deep_dive": "Rate limiting and API management",
            "comparison_review": "AetherPost vs manual posting",
            "industry_insights": "Future of developer marketing"
        }
        return suggestions.get(template_name, "General topic")

@click.group(name="blog")
@click.pass_context
def blog_generator(ctx):
    """Generate blog content for technical marketing."""
    ctx.ensure_object(dict)

@blog_generator.command()
@click.option("--template", "-t", type=click.Choice(['feature_announcement', 'tutorial_guide', 'case_study', 'technical_deep_dive', 'comparison_review', 'industry_insights']), 
              required=True, help="Blog post template")
@click.option("--app-name", default="AetherPost", help="Name of your app")
@click.option("--author", default="AetherPost Team", help="Author name")
@click.option("--feature-name", help="Feature name (for announcements)")
@click.option("--tutorial-topic", help="Tutorial topic (for guides)")
@click.option("--company", help="Company name (for case studies)")
@click.option("--output", "-o", help="Output file path")
@click.option("--preview", is_flag=True, help="Preview without saving")
def generate(template, app_name, author, feature_name, tutorial_topic, company, output, preview):
    """Generate a blog post from template."""
    generator = BlogContentGenerator()
    
    context = {
        "app_name": app_name,
        "author": author,
        "feature_name": feature_name,
        "tutorial_topic": tutorial_topic,
        "company": company
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Generating blog content...", total=None)
        
        try:
            blog_post = generator.generate_blog_post(template, context)
            progress.update(task, description="Blog post generated!")
            
            # Display preview
            console.print(Panel(
                f"[bold green]Title:[/bold green] {blog_post.title}\n\n"
                f"[bold green]Reading Time:[/bold green] {blog_post.reading_time} minutes\n"
                f"[bold green]Tags:[/bold green] {', '.join(blog_post.tags)}\n\n"
                f"[bold green]Excerpt:[/bold green]\n{blog_post.excerpt}\n\n"
                f"[bold green]Content Preview:[/bold green]\n{blog_post.content[:500]}...",
                title="Generated Blog Post"
            ))
            
            if not preview:
                # Save to file
                if not output:
                    filename = blog_post.title.lower().replace(' ', '-').replace(':', '') + '.md'
                    output = f"./blog/{filename}"
                
                generator.export_to_markdown(blog_post, output)
                print_success(f"Blog post saved to: {output}")
            
        except Exception as e:
            print_error(f"Error generating blog post: {e}")

@blog_generator.command()
def templates():
    """List available blog post templates."""
    generator = BlogContentGenerator()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Template", style="cyan")
    table.add_column("Description")
    table.add_column("Target Audience")
    table.add_column("Word Count")
    
    for name, template in generator.templates.items():
        word_range = f"{template.word_count_range[0]}-{template.word_count_range[1]}"
        table.add_row(
            name,
            template.description,
            template.target_audience,
            word_range
        )
    
    console.print(table)

@blog_generator.command()
@click.option("--months", "-m", default=3, help="Number of months for calendar")
def calendar(months):
    """Generate content calendar for blog posts."""
    generator = BlogContentGenerator()
    calendar_data = generator.generate_content_calendar(months)
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Week", justify="right")
    table.add_column("Template", style="cyan")
    table.add_column("Suggested Topic")
    table.add_column("Target Date")
    
    for item in calendar_data:
        table.add_row(
            str(item["week"]),
            item["template"].replace("_", " ").title(),
            item["suggested_topic"],
            item["target_date"].strftime("%Y-%m-%d")
        )
    
    console.print(table)
    console.print(f"\n[green]Generated {len(calendar_data)} blog post ideas for {months} months[/green]")

if __name__ == "__main__":
    blog_generator()