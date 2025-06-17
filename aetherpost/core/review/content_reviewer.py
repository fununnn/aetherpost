"""Content review and approval system."""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.columns import Columns

from ..exceptions import AetherPostError, ErrorCode
from ..logging.logger import logger, audit
from ..content.strategy import PlatformContentStrategy, ContentType


class ReviewAction(Enum):
    """Available review actions."""
    APPROVE = "approve"
    REGENERATE_TEXT = "regenerate_text"
    REGENERATE_MEDIA = "regenerate_media"
    REJECT = "reject"


class ReviewStatus(Enum):
    """Review status for content."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REGENERATING = "regenerating"


@dataclass
class ContentReviewItem:
    """Individual content item for review."""
    platform: str
    content_type: str
    text: str
    hashtags: List[str]
    media_requirements: Dict[str, Any]
    metadata: Dict[str, Any]
    generated_at: str
    review_status: ReviewStatus = ReviewStatus.PENDING
    review_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ReviewSession:
    """Review session containing multiple content items."""
    session_id: str
    campaign_name: str
    created_at: str
    items: List[ContentReviewItem]
    auto_approve: bool = False
    reviewer_notes: str = ""
    
    def get_pending_items(self) -> List[ContentReviewItem]:
        """Get items that need review."""
        return [item for item in self.items if item.review_status == ReviewStatus.PENDING]
    
    def get_approved_items(self) -> List[ContentReviewItem]:
        """Get approved items."""
        return [item for item in self.items if item.review_status == ReviewStatus.APPROVED]


class ContentReviewer:
    """Content review and approval system."""
    
    def __init__(self):
        self.console = Console()
        self.strategy = PlatformContentStrategy()
        self.sessions_dir = Path("logs/review_sessions")
        self.sessions_dir.mkdir(exist_ok=True)
    
    async def create_review_session(
        self,
        campaign_name: str,
        content_requests: List[Dict[str, Any]],
        auto_approve: bool = False
    ) -> ReviewSession:
        """Create a new review session with generated content."""
        
        session_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate content for each request
        items = []
        
        self.console.print(f"🎨 Generating content for review session: {session_id}")
        
        for request in content_requests:
            platform = request.get("platform", "twitter")
            content_type = ContentType(request.get("content_type", "announcement"))
            context = request.get("context", {})
            
            try:
                # Generate content
                content_result = self.strategy.generate_content(content_type, platform, context)
                
                item = ContentReviewItem(
                    platform=platform,
                    content_type=content_type.value,
                    text=content_result["text"],
                    hashtags=content_result["hashtags"],
                    media_requirements=content_result["media_requirements"],
                    metadata={
                        "tone": content_result["tone"],
                        "optimal_time": content_result.get("optimal_time"),
                        "schedule_recommendation": content_result.get("schedule_recommendation"),
                        "context": context
                    },
                    generated_at=datetime.now().isoformat()
                )
                
                if auto_approve:
                    item.review_status = ReviewStatus.APPROVED
                    item.review_notes = "Auto-approved"
                
                items.append(item)
                
                logger.info(f"Generated content for {platform}", platform=platform, extra={
                    "content_type": content_type.value,
                    "session_id": session_id,
                    "auto_approve": auto_approve
                })
                
            except Exception as e:
                logger.error(f"Failed to generate content for {platform}: {e}")
                
                # Create error item
                error_item = ContentReviewItem(
                    platform=platform,
                    content_type=content_type.value,
                    text=f"[ERROR] Failed to generate content: {str(e)}",
                    hashtags=[],
                    media_requirements={"required": False},
                    metadata={"error": str(e), "context": context},
                    generated_at=datetime.now().isoformat(),
                    review_status=ReviewStatus.REJECTED,
                    review_notes=f"Generation failed: {str(e)}"
                )
                items.append(error_item)
        
        # Create session
        session = ReviewSession(
            session_id=session_id,
            campaign_name=campaign_name,
            created_at=datetime.now().isoformat(),
            items=items,
            auto_approve=auto_approve
        )
        
        # Save session
        self._save_session(session)
        
        # Log audit event
        audit("review_session_created", {
            "session_id": session_id,
            "campaign_name": campaign_name,
            "items_count": len(items),
            "auto_approve": auto_approve
        })
        
        return session
    
    async def review_session(self, session: ReviewSession, skip_review: bool = False) -> ReviewSession:
        """Conduct interactive review of content."""
        
        if skip_review or session.auto_approve:
            self.console.print("⚡ Skipping review (auto-approve enabled)")
            return session
        
        pending_items = session.get_pending_items()
        
        if not pending_items:
            self.console.print("✅ No items to review")
            return session
        
        self.console.print(Panel(
            f"[bold blue]📋 Content Review Session[/bold blue]\n\n"
            f"Campaign: {session.campaign_name}\n"
            f"Session ID: {session.session_id}\n"
            f"Items to review: {len(pending_items)}",
            title="🔍 Review Session",
            border_style="blue"
        ))
        
        for i, item in enumerate(pending_items, 1):
            self.console.print(f"\n{'='*60}")
            self.console.print(f"📝 Reviewing Item {i}/{len(pending_items)}")
            self.console.print(f"{'='*60}")
            
            # Display content for review
            action = await self._review_single_item(item, session)
            
            # Handle action
            if action == ReviewAction.APPROVE:
                item.review_status = ReviewStatus.APPROVED
                item.review_notes = "Approved by reviewer"
                self.console.print("✅ [green]Content approved![/green]")
                
            elif action == ReviewAction.REJECT:
                item.review_status = ReviewStatus.REJECTED
                reason = Prompt.ask("Rejection reason (optional)", default="")
                item.review_notes = f"Rejected: {reason}" if reason else "Rejected"
                self.console.print("❌ [red]Content rejected[/red]")
                
            elif action == ReviewAction.REGENERATE_TEXT:
                item.review_status = ReviewStatus.REGENERATING
                item.review_notes = "Text regeneration requested"
                self.console.print("🔄 [yellow]Regenerating text...[/yellow]")
                
                # Regenerate text
                new_item = await self._regenerate_content(item, regenerate_media=False)
                if new_item:
                    # Replace item in session
                    session.items[session.items.index(item)] = new_item
                    self.console.print("✨ [green]Text regenerated![/green]")
                else:
                    item.review_status = ReviewStatus.REJECTED
                    item.review_notes = "Failed to regenerate text"
                    self.console.print("❌ [red]Regeneration failed[/red]")
                    
            elif action == ReviewAction.REGENERATE_MEDIA:
                item.review_status = ReviewStatus.REGENERATING
                item.review_notes = "Media regeneration requested"
                self.console.print("🔄 [yellow]Regenerating media...[/yellow]")
                
                # Regenerate media
                new_item = await self._regenerate_content(item, regenerate_media=True)
                if new_item:
                    session.items[session.items.index(item)] = new_item
                    self.console.print("✨ [green]Media regenerated![/green]")
                else:
                    item.review_status = ReviewStatus.REJECTED
                    item.review_notes = "Failed to regenerate media"
                    self.console.print("❌ [red]Media regeneration failed[/red]")
        
        # Update session
        session.reviewer_notes = Prompt.ask("Session notes (optional)", default="")
        self._save_session(session)
        
        # Show final summary
        self._show_review_summary(session)
        
        # Log audit event
        approved_count = len(session.get_approved_items())
        audit("review_session_completed", {
            "session_id": session.session_id,
            "approved_items": approved_count,
            "total_items": len(session.items),
            "approval_rate": approved_count / len(session.items) if session.items else 0
        })
        
        return session
    
    async def _review_single_item(self, item: ContentReviewItem, session: ReviewSession) -> ReviewAction:
        """Review a single content item."""
        
        # Display platform and content type
        self.console.print(f"\n[bold cyan]📱 Platform:[/bold cyan] {item.platform.title()}")
        self.console.print(f"[bold cyan]📝 Type:[/bold cyan] {item.content_type.title()}")
        self.console.print(f"[bold cyan]🎨 Tone:[/bold cyan] {item.metadata.get('tone', 'Unknown')}")
        
        # Display content
        self.console.print(Panel(
            item.text,
            title=f"💬 {item.platform.title()} Content",
            border_style="green"
        ))
        
        # Display hashtags
        if item.hashtags:
            hashtag_text = " ".join(item.hashtags)
            self.console.print(f"\n[bold blue]🏷️  Hashtags:[/bold blue] {hashtag_text}")
        
        # Display media requirements
        if item.media_requirements.get("required"):
            media_type = item.media_requirements.get("type", "unknown")
            media_style = item.media_requirements.get("style", "generic")
            self.console.print(f"\n[bold purple]📸 Media Required:[/bold purple] {media_type} ({media_style})")
        
        # Display metadata
        if item.metadata.get("optimal_time"):
            self.console.print(f"[bold yellow]⏰ Optimal Time:[/bold yellow] {item.metadata['optimal_time']}")
        
        if item.metadata.get("schedule_recommendation"):
            self.console.print(f"[bold yellow]📅 Schedule:[/bold yellow] {item.metadata['schedule_recommendation']}")
        
        # Review options
        self.console.print("\n[bold]Review Options:[/bold]")
        self.console.print("1. ✅ Approve - Content is ready to post")
        self.console.print("2. 🔄 Regenerate Text - Create new text content")
        self.console.print("3. 🎨 Regenerate Media - Create new media requirements")
        self.console.print("4. ❌ Reject - Don't use this content")
        
        while True:
            choice = Prompt.ask(
                "Your choice",
                choices=["1", "2", "3", "4"],
                default="1"
            )
            
            action_map = {
                "1": ReviewAction.APPROVE,
                "2": ReviewAction.REGENERATE_TEXT,
                "3": ReviewAction.REGENERATE_MEDIA,
                "4": ReviewAction.REJECT
            }
            
            action = action_map[choice]
            
            # Confirm destructive actions
            if action == ReviewAction.REJECT:
                if Confirm.ask("Are you sure you want to reject this content?"):
                    return action
            elif action in [ReviewAction.REGENERATE_TEXT, ReviewAction.REGENERATE_MEDIA]:
                if Confirm.ask(f"Are you sure you want to regenerate {action.value.replace('regenerate_', '')}?"):
                    return action
            else:
                return action
    
    async def _regenerate_content(self, item: ContentReviewItem, regenerate_media: bool = False) -> Optional[ContentReviewItem]:
        """Regenerate content for an item."""
        
        try:
            content_type = ContentType(item.content_type)
            context = item.metadata.get("context", {})
            
            # Add variation instruction to context
            if regenerate_media:
                context["regeneration_request"] = "Create different media style and requirements"
            else:
                context["regeneration_request"] = "Create alternative text with different approach"
            
            # Generate new content
            content_result = self.strategy.generate_content(content_type, item.platform, context)
            
            # Create new item
            new_item = ContentReviewItem(
                platform=item.platform,
                content_type=item.content_type,
                text=content_result["text"] if not regenerate_media else item.text,
                hashtags=content_result["hashtags"],
                media_requirements=content_result["media_requirements"] if regenerate_media else item.media_requirements,
                metadata={
                    **item.metadata,
                    "regenerated_at": datetime.now().isoformat(),
                    "regeneration_type": "media" if regenerate_media else "text"
                },
                generated_at=item.generated_at,
                review_status=ReviewStatus.PENDING
            )
            
            logger.info(f"Regenerated content for {item.platform}", platform=item.platform, extra={
                "regeneration_type": "media" if regenerate_media else "text"
            })
            
            return new_item
            
        except Exception as e:
            logger.error(f"Failed to regenerate content: {e}")
            return None
    
    def _show_review_summary(self, session: ReviewSession):
        """Show review session summary."""
        
        approved_items = session.get_approved_items()
        rejected_items = [item for item in session.items if item.review_status == ReviewStatus.REJECTED]
        
        self.console.print(Panel(
            f"[bold green]📊 Review Session Summary[/bold green]\n\n"
            f"Campaign: {session.campaign_name}\n"
            f"Total Items: {len(session.items)}\n"
            f"✅ Approved: {len(approved_items)}\n"
            f"❌ Rejected: {len(rejected_items)}\n"
            f"📈 Approval Rate: {len(approved_items)/len(session.items)*100:.1f}%",
            title="📋 Summary",
            border_style="green"
        ))
        
        if approved_items:
            self.console.print("\n[bold green]✅ Approved Content:[/bold green]")
            
            approved_table = Table()
            approved_table.add_column("Platform", style="cyan")
            approved_table.add_column("Type", style="yellow")
            approved_table.add_column("Preview", style="white")
            approved_table.add_column("Media", style="purple")
            
            for item in approved_items:
                preview = item.text[:50] + "..." if len(item.text) > 50 else item.text
                media_req = "Yes" if item.media_requirements.get("required") else "No"
                
                approved_table.add_row(
                    item.platform.title(),
                    item.content_type.title(),
                    preview,
                    media_req
                )
            
            self.console.print(approved_table)
    
    def _save_session(self, session: ReviewSession):
        """Save review session to file."""
        try:
            session_file = self.sessions_dir / f"{session.session_id}.json"
            
            with open(session_file, 'w', encoding='utf-8') as f:
                # Convert session to dict and save
                session_data = {
                    "session_id": session.session_id,
                    "campaign_name": session.campaign_name,
                    "created_at": session.created_at,
                    "auto_approve": session.auto_approve,
                    "reviewer_notes": session.reviewer_notes,
                    "items": [
                        {
                            **item.to_dict(),
                            "review_status": item.review_status.value  # Convert enum to string
                        } for item in session.items
                    ]
                }
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved review session: {session.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to save review session: {e}")
    
    def load_session(self, session_id: str) -> Optional[ReviewSession]:
        """Load review session from file."""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Convert back to objects
            items = []
            for item_data in session_data.get("items", []):
                item = ContentReviewItem(
                    platform=item_data["platform"],
                    content_type=item_data["content_type"],
                    text=item_data["text"],
                    hashtags=item_data["hashtags"],
                    media_requirements=item_data["media_requirements"],
                    metadata=item_data["metadata"],
                    generated_at=item_data["generated_at"],
                    review_status=ReviewStatus(item_data["review_status"]),
                    review_notes=item_data.get("review_notes")
                )
                items.append(item)
            
            session = ReviewSession(
                session_id=session_data["session_id"],
                campaign_name=session_data["campaign_name"],
                created_at=session_data["created_at"],
                items=items,
                auto_approve=session_data.get("auto_approve", False),
                reviewer_notes=session_data.get("reviewer_notes", "")
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to load review session {session_id}: {e}")
            return None
    
    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent review sessions."""
        sessions = []
        
        try:
            session_files = sorted(
                self.sessions_dir.glob("review_*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for session_file in session_files[:limit]:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # Count statuses
                    items = session_data.get("items", [])
                    approved_count = sum(1 for item in items if item.get("review_status") == "approved")
                    
                    sessions.append({
                        "session_id": session_data["session_id"],
                        "campaign_name": session_data["campaign_name"],
                        "created_at": session_data["created_at"],
                        "total_items": len(items),
                        "approved_items": approved_count,
                        "auto_approve": session_data.get("auto_approve", False)
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to load session summary from {session_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
        
        return sessions


# Global reviewer instance
content_reviewer = ContentReviewer()