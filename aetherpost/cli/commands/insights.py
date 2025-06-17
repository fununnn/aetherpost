"""Advanced insights and analytics commands."""

import typer
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.align import Align
import time

from ...core.edition import require_enterprise, is_feature_enabled, get_upgrade_message

console = Console()
insights_app = typer.Typer()


@insights_app.command()
def dashboard(
    days: int = typer.Option(30, "--days", help="Number of days to analyze"),
    export: bool = typer.Option(False, "--export", help="Export report to JSON"),
    platform: str = typer.Option(None, "--platform", help="Focus on specific platform")
):
    """Show comprehensive analytics dashboard."""
    
    # Check for advanced analytics feature
    if not is_feature_enabled('advanced_analytics'):
        console.print(Panel(
            get_upgrade_message('Advanced Analytics Dashboard'),
            border_style="yellow",
            title="🔒 Enterprise Feature"
        ))
        console.print("\n💡 [cyan]OSS users can still use:[/cyan]")
        console.print("  • [green]aetherpost stats[/green] - Basic campaign statistics")
        console.print("  • [green]aetherpost insights trends --basic[/green] - Basic trend analysis")
        return
    
    console.print(Panel(
        f"[bold blue]📊 Analytics Dashboard[/bold blue]\n\n"
        f"Analyzing last {days} days of campaign data...",
        border_style="blue"
    ))
    
    from ...core.analytics.dashboard import AnalyticsDashboard
    
    dashboard = AnalyticsDashboard()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Generating comprehensive report...", total=None)
        report = dashboard.generate_comprehensive_report(days)
        progress.update(task, completed=True)
    
    if "error" in report:
        console.print(f"❌ [red]{report['error']}[/red]")
        return
    
    # Display main dashboard
    display_dashboard_layout(report, platform)
    
    # Export if requested
    if export:
        export_filename = f"autopromo-analytics-{time.strftime('%Y%m%d-%H%M%S')}.json"
        with open(export_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        console.print(f"\n📄 [green]Report exported to: {export_filename}[/green]")


def display_dashboard_layout(report: dict, focus_platform: str = None):
    """Display dashboard with Rich layout."""
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="metrics", size=8),
        Layout(name="insights", ratio=1)
    )
    
    # Split metrics into columns
    layout["metrics"].split_row(
        Layout(name="overview"),
        Layout(name="platforms"),
        Layout(name="performance")
    )
    
    # Header
    layout["header"].update(
        Align.center(
            Panel(
                f"[bold green]📊 AetherPost Analytics Dashboard[/bold green]\n"
                f"Period: {report['period']} | Generated: {report['generated_at'][:19]}",
                border_style="green"
            )
        )
    )
    
    # Overview metrics
    overview_table = create_overview_table(report["overall_metrics"])
    layout["overview"].update(Panel(overview_table, title="Overview", border_style="blue"))
    
    # Platform insights
    platform_table = create_platform_table(report["platform_insights"], focus_platform)
    layout["platforms"].update(Panel(platform_table, title="Platform Performance", border_style="cyan"))
    
    # Performance insights
    performance_content = create_performance_content(report)
    layout["performance"].update(Panel(performance_content, title="Key Insights", border_style="yellow"))
    
    # Recommendations
    recommendations_content = create_recommendations_content(report["recommendations"])
    layout["insights"].update(Panel(recommendations_content, title="Recommendations", border_style="green"))
    
    console.print(layout)


def create_overview_table(metrics: dict) -> Table:
    """Create overview metrics table."""
    
    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold white")
    
    table.add_row("Total Posts", str(metrics.get("total_posts", 0)))
    table.add_row("Total Engagement", f"{metrics.get('total_engagement', 0):,.0f}")
    table.add_row("Avg Engagement/Post", f"{metrics.get('avg_engagement_per_post', 0):.1f}")
    table.add_row("Posting Frequency", f"{metrics.get('posting_frequency', 0):.1f}/day")
    
    return table


def create_platform_table(platform_insights: dict, focus_platform: str = None) -> Table:
    """Create platform performance table."""
    
    table = Table()
    table.add_column("Platform", style="cyan")
    table.add_column("Posts", justify="center")
    table.add_column("Engagement", justify="right")
    table.add_column("Avg/Post", justify="right")
    table.add_column("Growth", justify="center")
    
    platforms_to_show = [focus_platform] if focus_platform and focus_platform in platform_insights else platform_insights.keys()
    
    for platform in platforms_to_show:
        insights = platform_insights[platform]
        
        growth = insights.get("audience_growth", 0)
        growth_icon = "📈" if growth > 0 else "📉" if growth < 0 else "➡️"
        growth_color = "green" if growth > 0 else "red" if growth < 0 else "white"
        
        table.add_row(
            platform.title(),
            str(insights.get("total_posts", 0)),
            f"{insights.get('total_engagement', 0):,.0f}",
            f"{insights.get('avg_engagement_per_post', 0):.1f}",
            f"[{growth_color}]{growth_icon} {growth:+.1f}%[/{growth_color}]"
        )
    
    return table


def create_performance_content(report: dict) -> str:
    """Create performance insights content."""
    
    content_insights = report.get("content_insights", {})
    time_insights = report.get("time_insights", {})
    
    lines = []
    
    # Content insights
    if content_insights.get("best_style"):
        lines.append(f"🎨 Best Style: [cyan]{content_insights['best_style'].title()}[/cyan]")
    
    if content_insights.get("optimal_length"):
        lines.append(f"📏 Optimal Length: [cyan]{content_insights['optimal_length']} chars[/cyan]")
    
    if content_insights.get("best_cta_type"):
        lines.append(f"🎯 Best CTA: [cyan]{content_insights['best_cta_type'].title()}[/cyan]")
    
    # Time insights
    if time_insights.get("best_hours"):
        hours = time_insights["best_hours"][:2]
        hours_str = ", ".join(f"{h}:00" for h in hours)
        lines.append(f"⏰ Best Hours: [cyan]{hours_str}[/cyan]")
    
    if time_insights.get("best_days"):
        days = time_insights["best_days"][:2]
        days_str = ", ".join(days)
        lines.append(f"📅 Best Days: [cyan]{days_str}[/cyan]")
    
    # Emoji effectiveness
    emoji_eff = content_insights.get("emoji_effectiveness", 0)
    if emoji_eff != 0:
        emoji_icon = "😊" if emoji_eff > 0 else "😐"
        lines.append(f"{emoji_icon} Emoji Impact: [cyan]{emoji_eff:+.1f}%[/cyan]")
    
    return "\n".join(lines) if lines else "Insufficient data for insights"


def create_recommendations_content(recommendations: list) -> str:
    """Create recommendations content."""
    
    if not recommendations:
        return "No specific recommendations available"
    
    lines = []
    
    # Group by priority
    high_priority = [r for r in recommendations if r.get("priority") == "high"]
    medium_priority = [r for r in recommendations if r.get("priority") == "medium"]
    
    if high_priority:
        lines.append("[bold red]🔥 High Priority:[/bold red]")
        for rec in high_priority[:2]:  # Show top 2
            lines.append(f"• {rec.get('title', 'Unknown')}")
    
    if medium_priority:
        lines.append("\n[bold yellow]⚡ Medium Priority:[/bold yellow]")
        for rec in medium_priority[:2]:  # Show top 2
            lines.append(f"• {rec.get('title', 'Unknown')}")
    
    if len(recommendations) > 4:
        lines.append(f"\n[dim]... and {len(recommendations) - 4} more recommendations[/dim]")
    
    return "\n".join(lines)


@insights_app.command()
def trends(
    days: int = typer.Option(90, "--days", help="Number of days for trend analysis"),
    metric: str = typer.Option("engagement", "--metric", help="Metric to analyze trends for")
):
    """Analyze engagement and performance trends."""
    
    console.print(Panel(
        f"[bold purple]📈 Trend Analysis[/bold purple]\n\n"
        f"Analyzing {metric} trends over {days} days...",
        border_style="purple"
    ))
    
    from ...core.analytics.dashboard import AnalyticsDashboard
    
    dashboard = AnalyticsDashboard()
    report = dashboard.generate_comprehensive_report(days)
    
    if "error" in report:
        console.print(f"❌ [red]{report['error']}[/red]")
        return
    
    # Display trend analysis
    display_trend_analysis(report, metric)


def display_trend_analysis(report: dict, metric: str):
    """Display trend analysis."""
    
    console.print(f"\n[bold]📊 {metric.title()} Trend Analysis[/bold]")
    
    platform_insights = report.get("platform_insights", {})
    
    # Create trend table
    trend_table = Table(title=f"{metric.title()} Trends by Platform")
    trend_table.add_column("Platform", style="cyan")
    trend_table.add_column("Current Avg", justify="right")
    trend_table.add_column("Trend Direction", justify="center")
    trend_table.add_column("Growth Rate", justify="right")
    trend_table.add_column("Optimal Times", style="green")
    
    for platform, insights in platform_insights.items():
        avg_engagement = insights.get("avg_engagement_per_post", 0)
        growth = insights.get("audience_growth", 0)
        optimal_times = insights.get("optimal_posting_times", [])
        
        # Trend direction
        if growth > 5:
            trend_icon = "📈 Rising"
            trend_color = "green"
        elif growth < -5:
            trend_icon = "📉 Declining"
            trend_color = "red"
        else:
            trend_icon = "➡️ Stable"
            trend_color = "yellow"
        
        optimal_times_str = ", ".join(f"{t}:00" for t in optimal_times[:3])
        
        trend_table.add_row(
            platform.title(),
            f"{avg_engagement:.1f}",
            f"[{trend_color}]{trend_icon}[/{trend_color}]",
            f"{growth:+.1f}%",
            optimal_times_str
        )
    
    console.print(trend_table)
    
    # Show seasonal trends if available
    time_insights = report.get("time_insights", {})
    seasonal_trends = time_insights.get("seasonal_trends", {})
    
    if seasonal_trends:
        console.print(f"\n[bold]🌱 Seasonal Performance[/bold]")
        
        seasonal_table = Table()
        seasonal_table.add_column("Season", style="cyan")
        seasonal_table.add_column("Avg Engagement", justify="right")
        seasonal_table.add_column("Performance", justify="center")
        
        # Sort by performance
        sorted_seasons = sorted(seasonal_trends.items(), key=lambda x: x[1], reverse=True)
        
        for i, (season, performance) in enumerate(sorted_seasons):
            if i == 0:
                performance_icon = "🥇 Best"
            elif i == len(sorted_seasons) - 1:
                performance_icon = "🥉 Lowest"
            else:
                performance_icon = "🥈 Good"
            
            seasonal_table.add_row(
                season.title(),
                f"{performance:.1f}",
                performance_icon
            )
        
        console.print(seasonal_table)


@insights_app.command()
def compare(
    period1: int = typer.Option(30, "--period1", help="First period (days)"),
    period2: int = typer.Option(60, "--period2", help="Second period (days)"),
    metric: str = typer.Option("engagement", "--metric", help="Metric to compare")
):
    """Compare performance between two time periods."""
    
    console.print(Panel(
        f"[bold orange]⚖️ Period Comparison[/bold orange]\n\n"
        f"Comparing last {period1} days vs previous {period2-period1} days...",
        border_style="orange"
    ))
    
    from ...core.analytics.dashboard import AnalyticsDashboard
    
    dashboard = AnalyticsDashboard()
    
    # Generate reports for both periods
    recent_report = dashboard.generate_comprehensive_report(period1)
    extended_report = dashboard.generate_comprehensive_report(period2)
    
    if "error" in recent_report or "error" in extended_report:
        console.print("❌ [red]Insufficient data for comparison[/red]")
        return
    
    # Display comparison
    display_period_comparison(recent_report, extended_report, period1, period2-period1)


def display_period_comparison(recent_report: dict, extended_report: dict, recent_days: int, previous_days: int):
    """Display period comparison."""
    
    console.print(f"\n[bold]📊 Performance Comparison[/bold]")
    
    # Extract metrics for comparison
    recent_metrics = recent_report.get("overall_metrics", {})
    extended_metrics = extended_report.get("overall_metrics", {})
    
    # Calculate previous period metrics (rough estimation)
    recent_total_engagement = recent_metrics.get("total_engagement", 0)
    extended_total_engagement = extended_metrics.get("total_engagement", 0)
    previous_total_engagement = extended_total_engagement - recent_total_engagement
    
    recent_posts = recent_metrics.get("total_posts", 0)
    extended_posts = extended_metrics.get("total_posts", 0)
    previous_posts = extended_posts - recent_posts
    
    # Calculate averages
    recent_avg = recent_total_engagement / recent_posts if recent_posts > 0 else 0
    previous_avg = previous_total_engagement / previous_posts if previous_posts > 0 else 0
    
    # Create comparison table
    comparison_table = Table(title="Period Comparison")
    comparison_table.add_column("Metric", style="cyan")
    comparison_table.add_column(f"Recent ({recent_days}d)", justify="right")
    comparison_table.add_column(f"Previous ({previous_days}d)", justify="right")
    comparison_table.add_column("Change", justify="center")
    
    # Calculate changes
    def calculate_change(recent, previous):
        if previous == 0:
            return "∞" if recent > 0 else "0%"
        change = ((recent - previous) / previous) * 100
        return f"{change:+.1f}%"
    
    def format_change(change_str):
        if change_str.startswith('+'):
            return f"[green]📈 {change_str}[/green]"
        elif change_str.startswith('-'):
            return f"[red]📉 {change_str}[/red]"
        else:
            return f"[yellow]➡️ {change_str}[/yellow]"
    
    # Add comparison rows
    comparison_table.add_row(
        "Total Posts",
        str(recent_posts),
        str(previous_posts),
        format_change(calculate_change(recent_posts, previous_posts))
    )
    
    comparison_table.add_row(
        "Total Engagement",
        f"{recent_total_engagement:,.0f}",
        f"{previous_total_engagement:,.0f}",
        format_change(calculate_change(recent_total_engagement, previous_total_engagement))
    )
    
    comparison_table.add_row(
        "Avg Engagement/Post",
        f"{recent_avg:.1f}",
        f"{previous_avg:.1f}",
        format_change(calculate_change(recent_avg, previous_avg))
    )
    
    console.print(comparison_table)
    
    # Platform-specific comparison
    recent_platforms = recent_report.get("platform_insights", {})
    extended_platforms = extended_report.get("platform_insights", {})
    
    if recent_platforms:
        console.print(f"\n[bold]📱 Platform Performance Changes[/bold]")
        
        platform_comparison_table = Table()
        platform_comparison_table.add_column("Platform", style="cyan")
        platform_comparison_table.add_column("Engagement Change", justify="center")
        platform_comparison_table.add_column("Posts Change", justify="center")
        
        for platform in recent_platforms.keys():
            recent_platform = recent_platforms[platform]
            extended_platform = extended_platforms.get(platform, {})
            
            recent_eng = recent_platform.get("avg_engagement_per_post", 0)
            extended_eng = extended_platform.get("avg_engagement_per_post", 0)
            previous_eng = extended_eng  # Simplified calculation
            
            recent_posts_count = recent_platform.get("total_posts", 0)
            extended_posts_count = extended_platform.get("total_posts", 0)
            previous_posts_count = extended_posts_count - recent_posts_count
            
            eng_change = calculate_change(recent_eng, previous_eng)
            posts_change = calculate_change(recent_posts_count, previous_posts_count)
            
            platform_comparison_table.add_row(
                platform.title(),
                format_change(eng_change),
                format_change(posts_change)
            )
        
        console.print(platform_comparison_table)


@insights_app.command()
def export(
    format: str = typer.Option("json", "--format", help="Export format (json, csv, html)"),
    output: str = typer.Option(None, "--output", help="Output file path"),
    days: int = typer.Option(30, "--days", help="Number of days to include")
):
    """Export detailed analytics report."""
    
    console.print(Panel(
        f"[bold green]📤 Exporting Analytics Report[/bold green]\n\n"
        f"Format: {format.upper()} | Period: {days} days",
        border_style="green"
    ))
    
    from ...core.analytics.dashboard import AnalyticsDashboard
    
    dashboard = AnalyticsDashboard()
    report = dashboard.generate_comprehensive_report(days)
    
    if "error" in report:
        console.print(f"❌ [red]{report['error']}[/red]")
        return
    
    # Generate filename if not provided
    if not output:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output = f"autopromo-analytics-{timestamp}.{format}"
    
    try:
        if format.lower() == "json":
            export_json(report, output)
        elif format.lower() == "csv":
            export_csv(report, output)
        elif format.lower() == "html":
            export_html(report, output)
        else:
            console.print(f"❌ [red]Unsupported format: {format}[/red]")
            return
        
        console.print(f"✅ [green]Report exported to: {output}[/green]")
        console.print(f"📊 File size: {Path(output).stat().st_size / 1024:.1f} KB")
        
    except Exception as e:
        console.print(f"❌ [red]Export failed: {e}[/red]")


def export_json(report: dict, output: str):
    """Export report as JSON."""
    with open(output, 'w') as f:
        json.dump(report, f, indent=2, default=str)


def export_csv(report: dict, output: str):
    """Export report as CSV."""
    import csv
    
    with open(output, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write overall metrics
        writer.writerow(["Overall Metrics"])
        overall = report.get("overall_metrics", {})
        for key, value in overall.items():
            writer.writerow([key, value])
        
        writer.writerow([])  # Empty row
        
        # Write platform insights
        writer.writerow(["Platform Insights"])
        writer.writerow(["Platform", "Total Posts", "Total Engagement", "Avg Engagement/Post"])
        
        platforms = report.get("platform_insights", {})
        for platform, insights in platforms.items():
            writer.writerow([
                platform,
                insights.get("total_posts", 0),
                insights.get("total_engagement", 0),
                insights.get("avg_engagement_per_post", 0)
            ])


def export_html(report: dict, output: str):
    """Export report as HTML."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AetherPost Analytics Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f9ff; padding: 20px; border-radius: 8px; }}
        .metric {{ background: #fff; border: 1px solid #e5e7eb; padding: 15px; margin: 10px 0; border-radius: 6px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f9fafb; }}
        .recommendation {{ background: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 AetherPost Analytics Report</h1>
        <p>Generated: {report.get('generated_at', 'Unknown')}</p>
        <p>Period: {report.get('period', 'Unknown')}</p>
    </div>
    
    <h2>Overall Metrics</h2>
    """
    
    # Add overall metrics
    overall = report.get("overall_metrics", {})
    for key, value in overall.items():
        html_content += f'<div class="metric"><strong>{key.replace("_", " ").title()}:</strong> {value}</div>'
    
    # Add platform insights table
    html_content += """
    <h2>Platform Performance</h2>
    <table>
        <tr>
            <th>Platform</th>
            <th>Total Posts</th>
            <th>Total Engagement</th>
            <th>Avg Engagement/Post</th>
        </tr>
    """
    
    platforms = report.get("platform_insights", {})
    for platform, insights in platforms.items():
        html_content += f"""
        <tr>
            <td>{platform.title()}</td>
            <td>{insights.get('total_posts', 0)}</td>
            <td>{insights.get('total_engagement', 0):,}</td>
            <td>{insights.get('avg_engagement_per_post', 0):.1f}</td>
        </tr>
        """
    
    html_content += "</table>"
    
    # Add recommendations
    recommendations = report.get("recommendations", [])
    if recommendations:
        html_content += "<h2>Recommendations</h2>"
        for rec in recommendations:
            html_content += f'''
            <div class="recommendation">
                <strong>{rec.get('title', 'Unknown')}</strong><br>
                {rec.get('description', '')}
            </div>
            '''
    
    html_content += "</body></html>"
    
    with open(output, 'w') as f:
        f.write(html_content)