"""Stop command for pausing all promotional activities."""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from datetime import datetime

from ...core.logging.logger import logger, audit
from ...core.state.manager import StateManager
from ..utils.ui import ui, handle_cli_errors

stop_app = typer.Typer()
console = Console()


@stop_app.command()
@handle_cli_errors
def main(
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Reason for stopping promotions"),
    all_campaigns: bool = typer.Option(False, "--all", help="Stop all campaigns (not just current)"),
    duration: Optional[str] = typer.Option(None, "--duration", "-d", help="Stop duration (e.g., '24h', '7d')"),
    emergency: bool = typer.Option(False, "--emergency", "-e", help="Emergency stop (immediate halt)"),
    show_ads: bool = typer.Option(True, "--show-ads/--no-ads", help="Show advertising options"),
):
    """Stop all promotional activities."""
    
    # Header
    if emergency:
        ui.header("🚨 Emergency Stop", "Halting all promotional activities", "alert")
    else:
        ui.header("⏸️  AetherPost Stop", "Pausing promotional activities", "pause")
    
    # Get current state
    state_manager = StateManager()
    current_state = state_manager.load_state()
    
    # Show current status
    if current_state:
        ui.info(f"Current campaign: {current_state.campaign_name}")
        ui.info(f"Active posts: {len([p for p in current_state.posts if p.status == 'published'])}")
    
    # Confirm stop
    if not emergency:
        stop_details = []
        if reason:
            stop_details.append(f"Reason: {reason}")
        if duration:
            stop_details.append(f"Duration: {duration}")
        if all_campaigns:
            stop_details.append("Scope: All campaigns")
        else:
            stop_details.append("Scope: Current campaign only")
        
        ui.console.print(Panel(
            "\n".join(stop_details) if stop_details else "Standard promotion pause",
            title="Stop Details",
            border_style="yellow"
        ))
        
        if not Confirm.ask("\n? Confirm stopping promotions?"):
            ui.info("Stop cancelled")
            return
    
    # Execute stop
    try:
        # Create stop record
        stop_record = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason or "User requested stop",
            "duration": duration,
            "all_campaigns": all_campaigns,
            "emergency": emergency,
            "active_posts_stopped": 0
        }
        
        # Stop scheduled posts
        if current_state:
            scheduled_posts = [p for p in current_state.posts if p.status == "scheduled"]
            for post in scheduled_posts:
                post.status = "stopped"
                stop_record["active_posts_stopped"] += 1
            
            # Update timestamp
            current_state.updated_at = datetime.now()
            
            # Save updated state
            state_manager.state = current_state
            state_manager.save_state()
        
        # Log audit event
        audit("promotions_stopped", {
            "reason": reason,
            "emergency": emergency,
            "all_campaigns": all_campaigns,
            "duration": duration,
            "posts_stopped": stop_record["active_posts_stopped"]
        })
        
        # Show success message
        if emergency:
            ui.success("🚨 Emergency stop completed - All promotions halted immediately")
        else:
            ui.success("✅ Promotions stopped successfully")
        
        if stop_record["active_posts_stopped"] > 0:
            ui.info(f"Cancelled {stop_record['active_posts_stopped']} scheduled posts")
        
        # Show advertising options if enabled
        if show_ads:
            show_advertising_options()
        
        # Show restart instructions
        ui.console.print("\n[bold]To restart promotions:[/bold]")
        ui.console.print("• Resume current campaign: [cyan]aetherpost resume[/cyan]")
        ui.console.print("• Start new campaign: [cyan]aetherpost apply --config campaign.yaml[/cyan]")
        
    except Exception as e:
        logger.error(f"Failed to stop promotions: {e}")
        raise


def show_advertising_options():
    """Show advertising and sponsorship opportunities when promotions are stopped."""
    
    ui.console.print("\n")
    ui.console.print(Panel(
        "[bold yellow]🎯 広告でリーチを拡大しませんか？[/bold yellow]\n\n"
        "オーガニック投稿を停止中に、こんな広告オプションはいかがでしょうか：\n\n"
        "[bold]1. SNS広告代行[/bold]\n"
        "   • Twitter、Instagram、LinkedInでの広告運用\n"
        "   • ターゲティング設定と予算最適化\n"
        "   • 月額 ¥50,000～\n\n"
        "[bold]2. インフルエンサーマーケティング[/bold]\n"
        "   • 業界インフルエンサーとのタイアップ\n"
        "   • フォロワー数に応じた課金制\n"
        "   • 1投稿 ¥10,000～\n\n"
        "[bold]3. コンテンツ制作代行[/bold]\n"
        "   • プロによるクリエイティブ制作\n"
        "   • 動画、画像、コピーライティング\n"
        "   • 制作費 ¥30,000～\n\n"
        "[bold]4. マーケティング戦略コンサル[/bold]\n"
        "   • 包括的なマーケティング戦略立案\n"
        "   • 競合分析と市場調査込み\n"
        "   • 月額 ¥200,000～\n\n"
        "[bold cyan]お問い合わせ：[/bold cyan]\n"
        "• メール: [blue]ads@autopromo.dev[/blue]\n"
        "• 電話: [blue]03-1234-5678[/blue]\n"
        "• 無料相談: [cyan]平日 10:00-18:00[/cyan]",
        title="💰 広告・マーケティングサービス",
        border_style="yellow"
    ))




@stop_app.command("status")
def stop_status():
    """Check if promotions are currently stopped."""
    
    state_manager = StateManager()
    current_state = state_manager.load_state()
    
    if not current_state:
        ui.info("No active campaign found")
        return
    
    # Check if any posts are in "stopped" status
    stopped_posts = [p for p in current_state.posts if p.status == "stopped"]
    is_stopped = len(stopped_posts) > 0
    
    if is_stopped:
        
        ui.header("⏸️  Promotions Currently Stopped", icon="pause")
        
        status_info = {
            "Status": "STOPPED",
            "Stopped Posts": str(len(stopped_posts)),
            "Total Posts": str(len(current_state.posts)),
            "Campaign ID": current_state.campaign_id,
            "Created": current_state.created_at.strftime("%Y-%m-%d %H:%M")
        }
        
        ui.status_table("Stop Details", status_info)
        
        ui.console.print("\n[bold]To resume:[/bold] [cyan]aetherpost resume[/cyan]")
    else:
        ui.success("✅ Promotions are currently active")
        
        # Show campaign stats
        active_posts = len([p for p in current_state.posts if p.status == "published"])
        scheduled_posts = len([p for p in current_state.posts if p.status == "scheduled"])
        
        ui.info(f"Active posts: {active_posts}")
        ui.info(f"Scheduled posts: {scheduled_posts}")


@stop_app.command()
def resume(
    force: bool = typer.Option(False, "--force", "-f", help="Force resume without confirmation"),
):
    """Resume stopped promotional activities."""
    
    ui.header("▶️  Resume Promotions", icon="play")
    
    state_manager = StateManager()
    current_state = state_manager.load_state()
    
    if not current_state:
        ui.warning("No campaign found to resume")
        return
    
    # Check if any posts are in "stopped" status
    stopped_posts = [p for p in current_state.posts if p.status == "stopped"]
    
    if not stopped_posts:
        ui.info("No stopped posts found to resume")
        return
    
    # Show stop details
    ui.info(f"Found {len(stopped_posts)} stopped posts to resume")
    
    # Confirm resume
    if not force:
        if not Confirm.ask("\n? Resume promotional activities?"):
            ui.info("Resume cancelled")
            return
    
    # Resume promotions
    try:
        # Reactivate stopped posts
        reactivated = 0
        for post in current_state.posts:
            if post.status == "stopped":
                post.status = "scheduled"
                reactivated += 1
        
        # Update timestamp
        current_state.updated_at = datetime.now()
        
        # Save state
        state_manager.state = current_state
        state_manager.save_state()
        
        # Log audit event
        audit("promotions_resumed", {
            "posts_reactivated": reactivated,
            "campaign_id": current_state.campaign_id
        })
        
        ui.success("✅ Promotions resumed successfully")
        
        if reactivated > 0:
            ui.info(f"Reactivated {reactivated} scheduled posts")
        
        ui.console.print("\n[bold]Next steps:[/bold]")
        ui.console.print("• Check status: [cyan]aetherpost status[/cyan]")
        ui.console.print("• View scheduled posts: [cyan]aetherpost state show[/cyan]")
        
    except Exception as e:
        logger.error(f"Failed to resume promotions: {e}")
        ui.error(f"Failed to resume: {e}")