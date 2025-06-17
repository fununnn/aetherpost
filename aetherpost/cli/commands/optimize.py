"""Content optimization and A/B testing commands."""

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
import asyncio
import json

console = Console()
optimize_app = typer.Typer()


@optimize_app.command()
def analyze():
    """Analyze content performance and get optimization insights."""
    
    console.print(Panel(
        "[bold blue]📊 Content Performance Analysis[/bold blue]",
        border_style="blue"
    ))
    
    from ...core.intelligence.content_optimizer import ContentOptimizer
    
    optimizer = ContentOptimizer()
    
    # Check if we have enough data
    state = optimizer.state_manager.load_state()
    if not state or not state.posts:
        console.print("❌ [red]No post data found for analysis[/red]")
        console.print("Run some campaigns first: [cyan]aetherpost apply[/cyan]")
        return
    
    if len(state.posts) < 3:
        console.print("⚠️ [yellow]Limited data available[/yellow]")
        console.print(f"Found {len(state.posts)} posts. Need at least 3 for meaningful analysis.")
    
    # Analyze each platform
    platforms = list(set(post.platform for post in state.posts))
    
    for platform in platforms:
        console.print(f"\n[bold cyan]Analysis for {platform.title()}:[/bold cyan]")
        
        insights = optimizer._analyze_performance_patterns(platform)
        
        if insights.get("confidence") == "low":
            console.print("  📉 Insufficient data for reliable insights")
            continue
        
        patterns = insights.get("patterns", {})
        
        # Display insights
        insights_table = Table(title=f"{platform.title()} Performance Insights")
        insights_table.add_column("Category", style="cyan")
        insights_table.add_column("Finding", style="white")
        insights_table.add_column("Recommendation", style="green")
        
        # Timing insights
        if "timing" in patterns and patterns["timing"]:
            timing = patterns["timing"]
            best_hour = timing.get("best_hour")
            if best_hour is not None:
                insights_table.add_row(
                    "Optimal Timing",
                    f"Best performance at {best_hour}:00",
                    f"Schedule posts around {best_hour}:00"
                )
        
        # Length insights
        if "length" in patterns and patterns["length"]:
            length = patterns["length"]
            best_length = length.get("best_length_category")
            if best_length:
                length_desc = {
                    "short": "under 100 characters",
                    "medium": "100-200 characters", 
                    "long": "over 200 characters"
                }
                insights_table.add_row(
                    "Content Length",
                    f"Best performance: {best_length} posts",
                    f"Target {length_desc.get(best_length, best_length)} length"
                )
        
        # Emoji insights
        if "emojis" in patterns and patterns["emojis"]:
            emoji = patterns["emojis"]
            recommendation = emoji.get("recommendation")
            if recommendation == "use_emojis":
                boost = emoji.get("emoji_boost", 1.0)
                insights_table.add_row(
                    "Emoji Usage",
                    f"{boost:.1f}x better engagement with emojis",
                    "Include strategic emojis in posts"
                )
            elif recommendation == "minimal_emojis":
                insights_table.add_row(
                    "Emoji Usage",
                    "Better performance with fewer emojis",
                    "Use emojis sparingly"
                )
        
        # Hashtag insights
        if "hashtags" in patterns and patterns["hashtags"]:
            hashtag = patterns["hashtags"]
            top_hashtags = hashtag.get("top_hashtags", [])
            if top_hashtags:
                top_3 = [tag for tag, _ in top_hashtags[:3]]
                insights_table.add_row(
                    "Top Hashtags",
                    f"Best performing: {', '.join(top_3)}",
                    "Use these hashtags in future posts"
                )
        
        # CTA insights
        if "call_to_action" in patterns and patterns["call_to_action"]:
            cta = patterns["call_to_action"]
            best_cta = cta.get("best_cta_type")
            if best_cta and best_cta != "none":
                insights_table.add_row(
                    "Call to Action",
                    f"Best CTA type: '{best_cta}'",
                    f"Use '{best_cta}'-style calls to action"
                )
        
        console.print(insights_table)
        
        # Confidence indicator
        confidence = insights.get("confidence", "low")
        sample_size = insights.get("sample_size", 0)
        
        confidence_color = {
            "high": "green",
            "medium": "yellow", 
            "low": "red"
        }
        
        console.print(f"\n📈 Confidence: [{confidence_color[confidence]}]{confidence.title()}[/{confidence_color[confidence]}] (based on {sample_size} posts)")


@optimize_app.command()
def suggest():
    """Get optimization suggestions for next post."""
    
    console.print(Panel(
        "[bold green]💡 Optimization Suggestions[/bold green]",
        border_style="green"
    ))
    
    from ...core.intelligence.content_optimizer import ContentOptimizer
    from ...core.config.parser import ConfigLoader
    
    # Load current config
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_campaign_config()
    except Exception as e:
        console.print(f"❌ [red]Could not load configuration: {e}[/red]")
        return
    
    optimizer = ContentOptimizer()
    
    # Get suggestions for each platform
    for platform in config.platforms:
        console.print(f"\n[bold cyan]Suggestions for {platform.title()}:[/bold cyan]")
        
        insights = optimizer._analyze_performance_patterns(platform)
        
        if insights.get("confidence") == "low":
            console.print("  📊 Not enough data yet - keep posting to build insights!")
            continue
        
        # Generate optimized content preview
        try:
            optimized_content = asyncio.run(optimizer.optimize_content(config, platform))
            
            console.print(f"  📝 [bold]Optimized content preview:[/bold]")
            console.print(f"     {optimized_content.get('text', 'No content generated')}")
            
            # Show what optimizations were applied
            if hasattr(optimized_content, 'optimization_factors'):
                factors = optimized_content.get('optimization_factors', [])
                if factors:
                    console.print(f"  🔧 Applied optimizations: {', '.join(factors)}")
        
        except Exception as e:
            console.print(f"  ❌ Could not generate optimized content: {e}")


@optimize_app.command()
def experiment():
    """Set up A/B testing experiment."""
    
    console.print(Panel(
        "[bold purple]🧪 A/B Testing Setup[/bold purple]",
        border_style="purple"
    ))
    
    from ...core.intelligence.content_optimizer import ContentOptimizer
    from ...core.config.parser import ConfigLoader
    
    # Load current config
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_campaign_config()
    except Exception as e:
        console.print(f"❌ [red]Could not load configuration: {e}[/red]")
        return
    
    # Get experiment parameters
    console.print("\n[bold]Experiment Configuration:[/bold]")
    
    experiment_name = Prompt.ask("Experiment name", default=f"Test-{config.name}")
    duration_days = IntPrompt.ask("Duration (days)", default=7)
    
    # Select metric to optimize
    console.print("\nWhat metric do you want to optimize?")
    metrics = ["engagement_rate", "clicks", "likes", "shares", "replies"]
    for i, metric in enumerate(metrics, 1):
        console.print(f"{i}. {metric.replace('_', ' ').title()}")
    
    metric_choice = IntPrompt.ask("Select metric", default=1)
    selected_metric = metrics[metric_choice - 1] if 1 <= metric_choice <= len(metrics) else "engagement_rate"
    
    # Set up variants
    console.print("\n[bold]Variant Configuration:[/bold]")
    console.print("AetherPost will automatically generate optimized variants")
    
    variants = [
        {"id": "control", "name": "Control (current style)", "type": "base"},
        {"id": "optimized", "name": "Optimized (AI-enhanced)", "type": "optimized"}
    ]
    
    # Traffic split
    traffic_split = [50, 50]  # Default even split
    if Confirm.ask("Use custom traffic split?", default=False):
        control_percent = IntPrompt.ask("Control variant percentage", default=50)
        optimized_percent = 100 - control_percent
        traffic_split = [control_percent, optimized_percent]
        console.print(f"Traffic split: {control_percent}% control, {optimized_percent}% optimized")
    
    # Create experiment
    test_config = {
        "name": experiment_name,
        "duration_days": duration_days,
        "metric": selected_metric,
        "variants": variants,
        "traffic_split": traffic_split
    }
    
    optimizer = ContentOptimizer()
    experiment_id = asyncio.run(optimizer.setup_ab_test(config, test_config))
    
    console.print(f"\n✅ [green]Experiment created![/green]")
    console.print(f"   ID: {experiment_id}")
    console.print(f"   Duration: {duration_days} days")
    console.print(f"   Metric: {selected_metric}")
    
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"• Posts will automatically use A/B variants")
    console.print(f"• Check results: [cyan]aetherpost optimize results {experiment_id}[/cyan]")
    console.print(f"• View all experiments: [cyan]aetherpost optimize list[/cyan]")


@optimize_app.command()
def list():
    """List all A/B testing experiments."""
    
    console.print(Panel(
        "[bold blue]🧪 A/B Testing Experiments[/bold blue]",
        border_style="blue"
    ))
    
    from ...core.intelligence.content_optimizer import ContentOptimizer
    
    optimizer = ContentOptimizer()
    experiments = optimizer.optimization_history.get("experiments", [])
    
    if not experiments:
        console.print("No experiments found.")
        console.print("Create one with: [cyan]aetherpost optimize experiment[/cyan]")
        return
    
    experiments_table = Table(title="A/B Testing Experiments")
    experiments_table.add_column("ID", style="cyan")
    experiments_table.add_column("Name", style="white")
    experiments_table.add_column("Status", style="green")
    experiments_table.add_column("Metric", style="yellow")
    experiments_table.add_column("Duration", style="blue")
    
    for exp in experiments:
        status = exp.get("status", "unknown")
        status_icon = {"active": "🟢", "completed": "🔵", "stopped": "🔴"}.get(status, "⚪")
        
        experiments_table.add_row(
            exp.get("id", "Unknown"),
            exp.get("name", "Unnamed"),
            f"{status_icon} {status.title()}",
            exp.get("metric", "Unknown"),
            f"{exp.get('duration_days', 'Unknown')} days"
        )
    
    console.print(experiments_table)


@optimize_app.command()
def results(
    experiment_id: str = typer.Argument(..., help="Experiment ID to analyze")
):
    """Analyze A/B test results."""
    
    console.print(Panel(
        f"[bold green]📈 Experiment Results: {experiment_id}[/bold green]",
        border_style="green"
    ))
    
    from ...core.intelligence.content_optimizer import ContentOptimizer
    
    optimizer = ContentOptimizer()
    results = optimizer.analyze_ab_test_results(experiment_id)
    
    if "error" in results:
        console.print(f"❌ [red]{results['error']}[/red]")
        return
    
    # Display results
    console.print(f"[bold]Experiment ID:[/bold] {results['experiment_id']}")
    console.print(f"[bold]Metric:[/bold] {results['metric'].replace('_', ' ').title()}")
    
    # Winner information
    winner = results["winner"]
    console.print(f"\n🏆 [bold green]Winner: Variant {winner['variant_id']}[/bold green]")
    console.print(f"   Performance: {winner['performance']['average']:.2f}")
    console.print(f"   Sample size: {winner['performance']['count']} posts")
    
    # All variants performance
    console.print(f"\n[bold]All Variants Performance:[/bold]")
    
    variants_table = Table()
    variants_table.add_column("Variant", style="cyan")
    variants_table.add_column("Average", style="white")
    variants_table.add_column("Count", style="green")
    variants_table.add_column("Total", style="yellow")
    
    for variant_id, performance in results["all_variants"].items():
        is_winner = variant_id == winner["variant_id"]
        variant_display = f"🏆 {variant_id}" if is_winner else variant_id
        
        variants_table.add_row(
            variant_display,
            f"{performance['average']:.2f}",
            str(performance['count']),
            f"{performance['total']:.2f}"
        )
    
    console.print(variants_table)
    
    # Confidence and recommendation
    confidence = results["confidence"]
    confidence_color = {"high": "green", "medium": "yellow", "low": "red"}
    
    console.print(f"\n📊 [bold]Confidence:[/bold] [{confidence_color[confidence]}]{confidence.title()}[/{confidence_color[confidence]}]")
    console.print(f"💡 [bold]Recommendation:[/bold] {results['recommendation']}")
    
    if confidence == "low":
        console.print("\n⚠️ [yellow]Low confidence - consider running the test longer[/yellow]")
    elif confidence == "high":
        console.print(f"\n✅ [green]High confidence - safe to use winning variant[/green]")


@optimize_app.command()
def stop(
    experiment_id: str = typer.Argument(..., help="Experiment ID to stop")
):
    """Stop a running A/B test experiment."""
    
    from ...core.intelligence.content_optimizer import ContentOptimizer
    
    optimizer = ContentOptimizer()
    experiments = optimizer.optimization_history.get("experiments", [])
    
    # Find experiment
    experiment = next(
        (exp for exp in experiments if exp["id"] == experiment_id),
        None
    )
    
    if not experiment:
        console.print(f"❌ [red]Experiment {experiment_id} not found[/red]")
        return
    
    if experiment.get("status") != "active":
        console.print(f"⚠️ [yellow]Experiment {experiment_id} is not active[/yellow]")
        return
    
    # Confirm stopping
    if not Confirm.ask(f"Stop experiment '{experiment.get('name', experiment_id)}'?"):
        console.print("Operation cancelled.")
        return
    
    # Stop experiment
    experiment["status"] = "stopped"
    optimizer._save_optimization_history()
    
    console.print(f"✅ [green]Experiment {experiment_id} stopped[/green]")
    
    # Show current results
    console.print("\nCurrent results:")
    results = optimizer.analyze_ab_test_results(experiment_id)
    if "winner" in results:
        winner = results["winner"]
        console.print(f"Leading variant: {winner['variant_id']} ({winner['performance']['average']:.2f})")


@optimize_app.command()
def history():
    """Show optimization history and insights."""
    
    console.print(Panel(
        "[bold cyan]📚 Optimization History[/bold cyan]",
        border_style="cyan"
    ))
    
    from ...core.intelligence.content_optimizer import ContentOptimizer
    
    optimizer = ContentOptimizer()
    history = optimizer.optimization_history
    
    # Recent optimization decisions
    insights = history.get("insights", [])
    if insights:
        console.print("\n[bold]Recent Optimization Decisions:[/bold]")
        
        recent_table = Table()
        recent_table.add_column("Date", style="cyan")
        recent_table.add_column("Platform", style="white")
        recent_table.add_column("Selected Variant", style="green")
        recent_table.add_column("Optimizations", style="yellow")
        
        for insight in insights[-10:]:  # Last 10 decisions
            date = insight.get("timestamp", "Unknown")[:10]  # Just the date part
            platform = insight.get("platform", "Unknown")
            variant = insight.get("selected_variant", "Unknown")
            factors = ", ".join(insight.get("optimization_factors", []))
            
            recent_table.add_row(date, platform, variant, factors or "None")
        
        console.print(recent_table)
    
    # Experiments summary
    experiments = history.get("experiments", [])
    if experiments:
        console.print(f"\n[bold]Experiments Summary:[/bold]")
        
        active_count = len([e for e in experiments if e.get("status") == "active"])
        completed_count = len([e for e in experiments if e.get("status") == "completed"])
        stopped_count = len([e for e in experiments if e.get("status") == "stopped"])
        
        console.print(f"• Active: {active_count}")
        console.print(f"• Completed: {completed_count}")
        console.print(f"• Stopped: {stopped_count}")
        console.print(f"• Total: {len(experiments)}")
    
    if not insights and not experiments:
        console.print("No optimization history found.")
        console.print("Start optimizing with: [cyan]aetherpost optimize analyze[/cyan]")


@optimize_app.command()
def clear():
    """Clear optimization history."""
    
    if not Confirm.ask("⚠️ Clear all optimization history and experiments?"):
        console.print("Operation cancelled.")
        return
    
    from ...core.intelligence.content_optimizer import ContentOptimizer
    
    optimizer = ContentOptimizer()
    optimizer.optimization_history = {"experiments": [], "insights": [], "performance_data": {}}
    optimizer._save_optimization_history()
    
    console.print("✅ [green]Optimization history cleared[/green]")