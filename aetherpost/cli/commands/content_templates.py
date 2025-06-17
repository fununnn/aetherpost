"""Content templates for promotional activities."""

import typer
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
import json
from pathlib import Path
from datetime import datetime

from ...core.logging.logger import logger, audit
from ..utils.ui import ui, handle_cli_errors

templates_app = typer.Typer()
console = Console()

# Predefined templates for different industries and use cases
CONTENT_TEMPLATES = {
    "saas": {
        "name": "SaaS・技術系",
        "templates": {
            "feature_announcement": {
                "name": "新機能発表",
                "template": "🚀 新機能「{feature_name}」をリリースしました！\n\n✨ {benefit_1}\n📈 {benefit_2}\n⚡ {benefit_3}\n\n詳細はこちら👇\n{url}\n\n#SaaS #{hashtag_1} #{hashtag_2}",
                "variables": ["feature_name", "benefit_1", "benefit_2", "benefit_3", "url", "hashtag_1", "hashtag_2"],
                "tone": "excited"
            },
            "case_study": {
                "name": "導入事例",
                "template": "📊 {company_name}様での導入事例をご紹介\n\n課題：{problem}\n解決：{solution}\n結果：{result}\n\n{quote}\n- {person_name}様（{position}）\n\n同じような課題をお持ちの方、ぜひご相談ください💬\n{url}",
                "variables": ["company_name", "problem", "solution", "result", "quote", "person_name", "position", "url"],
                "tone": "professional"
            },
            "tips": {
                "name": "Tips・活用方法",
                "template": "💡 {tool_name}活用Tips\n\n「{tip_title}」\n\n{step_1}\n{step_2}\n{step_3}\n\n試してみて効果があったら、ぜひコメントで教えてください🙌\n\n#{hashtag_main} #Tips #効率化",
                "variables": ["tool_name", "tip_title", "step_1", "step_2", "step_3", "hashtag_main"],
                "tone": "helpful"
            }
        }
    },
    "ecommerce": {
        "name": "EC・小売",
        "templates": {
            "product_launch": {
                "name": "商品発売",
                "template": "🎉 新商品「{product_name}」登場！\n\n{product_description}\n\n特別価格：{price}（通常価格：{regular_price}）\n期間限定：{end_date}まで\n\n今すぐチェック👇\n{shop_url}\n\n#新商品 #{category} #限定価格",
                "variables": ["product_name", "product_description", "price", "regular_price", "end_date", "shop_url", "category"],
                "tone": "exciting"
            },
            "sale_announcement": {
                "name": "セール告知",
                "template": "🔥 {sale_name}開催中！\n\n{discount_rate}OFF\n対象商品：{target_products}\n期間：{start_date}〜{end_date}\n\n見逃し厳禁のお得なチャンス✨\n{shop_url}\n\n#セール #特価 #{category}",
                "variables": ["sale_name", "discount_rate", "target_products", "start_date", "end_date", "shop_url", "category"],
                "tone": "urgent"
            }
        }
    },
    "startup": {
        "name": "スタートアップ",
        "templates": {
            "funding_news": {
                "name": "資金調達発表",
                "template": "📰 資金調達のお知らせ\n\n{company_name}は、{investor_name}を引受先とする{amount}の資金調達を実施いたしました。\n\n今回の調達により：\n・{use_1}\n・{use_2}\n・{use_3}\n\n引き続きご支援のほど、よろしくお願いいたします🙏\n\n#資金調達 #スタートアップ #{industry}",
                "variables": ["company_name", "investor_name", "amount", "use_1", "use_2", "use_3", "industry"],
                "tone": "formal"
            },
            "team_update": {
                "name": "チーム紹介",
                "template": "👥 チームメンバー紹介\n\n{name}さんが{position}として参加されました！\n\n{background}\n\n{quote}\n\n{name}さんと一緒に{goal}を実現していきます💪\n\n#チーム #採用 #{company_hashtag}",
                "variables": ["name", "position", "background", "quote", "goal", "company_hashtag"],
                "tone": "welcoming"
            }
        }
    },
    "personal": {
        "name": "個人・クリエイター",
        "templates": {
            "daily_update": {
                "name": "日常アップデート",
                "template": "📅 今日の作業報告\n\n✅ {task_1}\n✅ {task_2}\n🔄 {task_3}（進行中）\n\n{reflection}\n\n明日は{tomorrow_plan}に取り組みます💪\n\n#{main_hashtag} #日報 #進捗",
                "variables": ["task_1", "task_2", "task_3", "reflection", "tomorrow_plan", "main_hashtag"],
                "tone": "casual"
            },
            "behind_scenes": {
                "name": "制作過程",
                "template": "🎨 制作の裏側をお見せします\n\n{project_name}の{process_stage}段階です\n\n今回のポイント：\n・{point_1}\n・{point_2}\n・{point_3}\n\n{current_feeling}\n\n完成まであと{timeline}予定です🔥\n\n#{project_hashtag} #制作過程 #クリエイター",
                "variables": ["project_name", "process_stage", "point_1", "point_2", "point_3", "current_feeling", "timeline", "project_hashtag"],
                "tone": "engaging"
            }
        }
    }
}

PLATFORM_ADAPTATIONS = {
    "twitter": {
        "max_length": 280,
        "hashtag_style": "moderate",  # 2-3 hashtags
        "tone_adjustment": "concise"
    },
    "instagram": {
        "max_length": 2200,
        "hashtag_style": "heavy",  # 10-15 hashtags
        "tone_adjustment": "visual"
    },
    "linkedin": {
        "max_length": 3000,
        "hashtag_style": "professional",  # 3-5 professional hashtags
        "tone_adjustment": "professional"
    },
    "facebook": {
        "max_length": 63206,
        "hashtag_style": "light",  # 1-2 hashtags
        "tone_adjustment": "conversational"
    }
}


def show_templates(
    industry: Optional[str] = typer.Option(None, "--industry", "-i", help="Filter by industry"),
):
    """List available content templates."""
    
    ui.header("📋 Content Templates", "Ready-to-use promotional templates", "list")
    
    if industry and industry in CONTENT_TEMPLATES:
        # Show templates for specific industry
        industry_data = CONTENT_TEMPLATES[industry]
        ui.console.print(f"\n[bold cyan]🏢 {industry_data['name']} Templates[/bold cyan]")
        
        for template_id, template_data in industry_data["templates"].items():
            ui.console.print(f"\n[bold]{template_data['name']}[/bold] ({template_id})")
            ui.console.print(f"Tone: {template_data['tone']}")
            ui.console.print(f"Variables: {len(template_data['variables'])} required")
            
            # Show preview
            preview = template_data["template"][:100] + "..." if len(template_data["template"]) > 100 else template_data["template"]
            ui.console.print(Panel(preview, title="Preview", border_style="dim"))
    else:
        # Show all industries
        industries_table = Table(title="📊 Available Templates by Industry")
        industries_table.add_column("Industry", style="cyan", width=20)
        industries_table.add_column("Templates", style="yellow", width=15)
        industries_table.add_column("Description", style="white", width=40)
        
        for industry_id, industry_data in CONTENT_TEMPLATES.items():
            template_count = len(industry_data["templates"])
            template_names = ", ".join(list(industry_data["templates"].keys())[:2])
            if len(industry_data["templates"]) > 2:
                template_names += f" (+{len(industry_data['templates'])-2} more)"
            
            industries_table.add_row(
                f"{industry_data['name']} ({industry_id})",
                str(template_count),
                template_names
            )
        
        ui.console.print(industries_table)
        
        ui.console.print("\n[bold]Usage:[/bold]")
        ui.console.print("• View industry templates: [cyan]aetherpost templates show --industry saas[/cyan]")
        ui.console.print("• Generate content: [cyan]aetherpost templates generate[/cyan]")
        ui.console.print("• Create custom template: [cyan]aetherpost templates create[/cyan]")


def generate_content(
    industry: str = typer.Option(..., "--industry", "-i", help="Industry type"),
    template: str = typer.Option(..., "--template", "-t", help="Template ID"),
    platform: str = typer.Option("all", "--platform", "-p", help="Target platform"),
    interactive: bool = typer.Option(True, "--interactive/--batch", help="Interactive mode"),
):
    """Generate content from template."""
    
    # Validate industry and template
    if industry not in CONTENT_TEMPLATES:
        ui.error(f"Industry '{industry}' not found. Available: {', '.join(CONTENT_TEMPLATES.keys())}")
        return
    
    if template not in CONTENT_TEMPLATES[industry]["templates"]:
        available = ', '.join(CONTENT_TEMPLATES[industry]["templates"].keys())
        ui.error(f"Template '{template}' not found in {industry}. Available: {available}")
        return
    
    template_data = CONTENT_TEMPLATES[industry]["templates"][template]
    
    ui.header(f"🎨 Generate: {template_data['name']}", f"Industry: {CONTENT_TEMPLATES[industry]['name']}", "edit")
    
    # Show template info
    ui.console.print(Panel(
        f"[bold]Template:[/bold] {template_data['name']}\n"
        f"[bold]Tone:[/bold] {template_data['tone']}\n"
        f"[bold]Variables:[/bold] {len(template_data['variables'])} required",
        title="Template Info",
        border_style="blue"
    ))
    
    # Collect variables
    variables = {}
    
    if interactive:
        ui.console.print("\n[bold]📝 Fill in the template variables:[/bold]")
        for var in template_data["variables"]:
            value = Prompt.ask(f"  {var.replace('_', ' ').title()}")
            variables[var] = value
    else:
        ui.console.print("\n[yellow]Batch mode: Using placeholder values[/yellow]")
        for var in template_data["variables"]:
            variables[var] = f"[{var.upper()}]"
    
    # Generate content
    generated_content = template_data["template"].format(**variables)
    
    # Platform adaptations
    if platform == "all":
        platforms = ["twitter", "instagram", "linkedin", "facebook"]
    else:
        platforms = [platform]
    
    ui.console.print("\n[bold green]✨ Generated Content[/bold green]")
    
    for plt in platforms:
        if plt in PLATFORM_ADAPTATIONS:
            adapted_content = adapt_for_platform(generated_content, plt, template_data["tone"])
            
            ui.console.print(f"\n[bold cyan]📱 {plt.title()}[/bold cyan]")
            ui.console.print(Panel(
                adapted_content,
                border_style="green"
            ))
            
            # Show platform stats
            char_count = len(adapted_content)
            max_chars = PLATFORM_ADAPTATIONS[plt]["max_length"]
            status = "✅" if char_count <= max_chars else "⚠️"
            ui.console.print(f"  {status} Length: {char_count}/{max_chars} characters")
    
    # Save option
    if Confirm.ask("\n? Save generated content for later use?"):
        save_generated_content(industry, template, variables, generated_content, platforms)
    
    # Direct posting option
    if Confirm.ask("\n? Post this content now?"):
        post_generated_content(generated_content, platforms)


def adapt_for_platform(content: str, platform: str, tone: str) -> str:
    """Adapt content for specific platform."""
    adaptation = PLATFORM_ADAPTATIONS.get(platform, {})
    
    # Length adjustment
    max_length = adaptation.get("max_length", 1000)
    if len(content) > max_length:
        # Truncate smartly (preserve hashtags if possible)
        lines = content.split('\n')
        hashtag_lines = [line for line in lines if line.strip().startswith('#')]
        content_lines = [line for line in lines if not line.strip().startswith('#')]
        
        # Truncate content lines
        available_length = max_length - sum(len(line) + 1 for line in hashtag_lines) - 10  # buffer
        
        truncated_content = ""
        for line in content_lines:
            if len(truncated_content + line + "\n") <= available_length:
                truncated_content += line + "\n"
            else:
                # Add truncation indicator
                truncated_content += "...\n"
                break
        
        # Re-add hashtags
        content = truncated_content + "\n".join(hashtag_lines)
    
    # Platform-specific adjustments
    if platform == "linkedin":
        # Add professional elements
        if not content.startswith("📊") and not content.startswith("💼"):
            content = "💼 " + content
    elif platform == "twitter":
        # Make more concise
        content = content.replace("皆様", "皆さん")
        content = content.replace("いたします", "します")
    elif platform == "instagram":
        # Add more emojis and hashtags
        if "✨" not in content:
            content = content.replace("!", "!✨")
    
    return content.strip()


def save_generated_content(industry: str, template: str, variables: dict, content: str, platforms: list):
    """Save generated content to file."""
    
    generated_dir = Path("generated_content")
    generated_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{industry}_{template}_{timestamp}.json"
    
    data = {
        "industry": industry,
        "template": template,
        "variables": variables,
        "content": content,
        "platforms": platforms,
        "generated_at": datetime.now().isoformat(),
        "status": "draft"
    }
    
    with open(generated_dir / filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    ui.success(f"Content saved to: generated_content/{filename}")


def post_generated_content(content: str, platforms: list):
    """Post generated content using existing AetherPost commands."""
    ui.console.print("\n[yellow]Posting feature integration coming soon![/yellow]")
    ui.console.print("For now, you can copy the content and use:")
    ui.console.print(f"[cyan]aetherpost promote \"{content[:50]}...\" --platforms {','.join(platforms)}[/cyan]")


def create_template(
    name: str = typer.Option(..., "--name", "-n", help="Template name"),
    industry: str = typer.Option(..., "--industry", "-i", help="Industry category"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Load template from file"),
):
    """Create a custom content template."""
    
    ui.header("🔧 Create Custom Template", "Build your own content template", "plus")
    
    if file:
        # Load from file
        try:
            with open(file, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except FileNotFoundError:
            ui.error(f"File not found: {file}")
            return
    else:
        # Interactive creation
        ui.console.print("[bold]Enter your template content:[/bold]")
        ui.console.print("Use {variable_name} for placeholders")
        ui.console.print("Example: Hello {name}, check out our new {feature}!")
        
        template_content = Prompt.ask("\nTemplate content", multiline=True)
    
    # Extract variables from template
    import re
    variables = re.findall(r'\{(\w+)\}', template_content)
    
    if not variables:
        ui.warning("No variables found in template. Add {variable_name} placeholders.")
        return
    
    # Get additional info
    tone = Prompt.ask("Template tone", choices=["professional", "casual", "excited", "helpful", "urgent"], default="professional")
    
    # Show preview
    ui.console.print("\n[bold]Template Preview:[/bold]")
    ui.console.print(Panel(template_content, border_style="green"))
    ui.console.print(f"Variables found: {', '.join(variables)}")
    ui.console.print(f"Tone: {tone}")
    
    if Confirm.ask("\n? Save this template?"):
        save_custom_template(name, industry, template_content, variables, tone)


def save_custom_template(name: str, industry: str, content: str, variables: list, tone: str):
    """Save custom template to file."""
    custom_dir = Path("custom_templates")
    custom_dir.mkdir(exist_ok=True)
    
    template_data = {
        "name": name,
        "template": content,
        "variables": variables,
        "tone": tone,
        "created_at": datetime.now().isoformat(),
        "industry": industry
    }
    
    filename = f"{industry}_{name.lower().replace(' ', '_')}.json"
    
    with open(custom_dir / filename, 'w', encoding='utf-8') as f:
        json.dump(template_data, f, indent=2, ensure_ascii=False)
    
    ui.success(f"Custom template saved: custom_templates/{filename}")
    
    # Log audit event
    audit("custom_template_created", {
        "template_name": name,
        "industry": industry,
        "variables_count": len(variables)
    })


def show_drafts():
    """Show saved content drafts."""
    
    generated_dir = Path("generated_content")
    
    if not generated_dir.exists():
        ui.info("No drafts found. Generate content with 'aetherpost templates generate'")
        return
    
    draft_files = list(generated_dir.glob("*.json"))
    
    if not draft_files:
        ui.info("No drafts found")
        return
    
    ui.header("📄 Content Drafts", f"Found {len(draft_files)} drafts", "file")
    
    drafts_table = Table(title="Saved Drafts")
    drafts_table.add_column("File", style="cyan", width=25)
    drafts_table.add_column("Industry", style="yellow", width=15)
    drafts_table.add_column("Template", style="green", width=20)
    drafts_table.add_column("Created", style="white", width=15)
    drafts_table.add_column("Preview", style="dim", width=30)
    
    for draft_file in sorted(draft_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
        try:
            with open(draft_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            preview = data["content"][:50] + "..." if len(data["content"]) > 50 else data["content"]
            created = data.get("generated_at", "Unknown")[:10]  # Just date part
            
            drafts_table.add_row(
                draft_file.name,
                data.get("industry", "Unknown"),
                data.get("template", "Unknown"),
                created,
                preview.replace('\n', ' ')
            )
        except Exception:
            continue
    
    ui.console.print(drafts_table)
    
    ui.console.print("\n[bold]Actions:[/bold]")
    ui.console.print("• View draft: [cyan]cat generated_content/filename.json[/cyan]")
    ui.console.print("• Clean up: [cyan]rm generated_content/*.json[/cyan]")


# Register commands
templates_app.command("show", help="List available content templates")(handle_cli_errors(show_templates))
templates_app.command("generate", help="Generate content from template")(handle_cli_errors(generate_content))
templates_app.command("create", help="Create a custom content template")(handle_cli_errors(create_template))
templates_app.command("drafts", help="Show saved content drafts")(handle_cli_errors(show_drafts))