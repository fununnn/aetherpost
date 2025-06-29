"""Background scheduler for continuous posting."""

import asyncio
import signal
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from .scheduler import PostingScheduler
from .models import ScheduledPost, ScheduleStatus
from ..exceptions import AetherPostError, ErrorCode

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Background scheduler that runs continuously."""
    
    def __init__(self, 
                 campaign_file: str = "campaign.yaml",
                 check_interval_seconds: int = 60,
                 aetherpost_dir: str = ".aetherpost"):
        """Initialize background scheduler."""
        self.campaign_file = campaign_file
        self.check_interval = check_interval_seconds
        self.scheduler = PostingScheduler(aetherpost_dir)
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
        # Track statistics
        self.stats = {
            "started_at": None,
            "last_check": None,
            "posts_executed": 0,
            "posts_failed": 0,
            "errors": []
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    async def start(self):
        """Start the background scheduler."""
        if self.running:
            logger.warning("Background scheduler is already running")
            return
        
        self.running = True
        self.stats["started_at"] = datetime.utcnow()
        
        logger.info(f"Starting background scheduler for {self.campaign_file}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        
        # Start the main loop
        self.task = asyncio.create_task(self._run_loop())
        
        try:
            await self.task
        except asyncio.CancelledError:
            logger.info("Background scheduler stopped")
        except Exception as e:
            logger.error(f"Background scheduler error: {e}")
            self.stats["errors"].append({
                "time": datetime.utcnow().isoformat(),
                "error": str(e)
            })
            raise
    
    def stop(self):
        """Stop the background scheduler."""
        if not self.running:
            return
        
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()
        
        logger.info("Background scheduler stopped")
    
    async def _run_loop(self):
        """Main scheduler loop."""
        logger.info("Background scheduler loop started")
        
        while self.running:
            try:
                await self._check_and_execute_posts()
                self.stats["last_check"] = datetime.utcnow()
                
                # Sleep for the check interval
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                self.stats["errors"].append({
                    "time": datetime.utcnow().isoformat(),
                    "error": str(e)
                })
                
                # Wait a bit before retrying to avoid rapid error loops
                await asyncio.sleep(min(self.check_interval, 300))  # Max 5 minutes
    
    async def _check_and_execute_posts(self):
        """Check for and execute pending posts."""
        try:
            # Get pending posts
            pending_posts = self.scheduler.get_pending_posts()
            
            if not pending_posts:
                return
            
            logger.info(f"Found {len(pending_posts)} pending posts")
            
            # Execute each pending post
            for post in pending_posts:
                try:
                    logger.info(f"Executing post {post.id} scheduled for {post.scheduled_time}")
                    
                    success = await self.scheduler.execute_scheduled_post(post)
                    
                    if success:
                        self.stats["posts_executed"] += 1
                        logger.info(f"Successfully executed post {post.id}")
                    else:
                        self.stats["posts_failed"] += 1
                        logger.error(f"Failed to execute post {post.id}")
                    
                    # Small delay between posts to avoid rate limits
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error executing post {post.id}: {e}")
                    self.stats["posts_failed"] += 1
                    self.stats["errors"].append({
                        "time": datetime.utcnow().isoformat(),
                        "post_id": post.id,
                        "error": str(e)
                    })
            
        except Exception as e:
            logger.error(f"Error checking for pending posts: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        schedule_stats = self.scheduler.get_schedule_stats()
        
        status = {
            "running": self.running,
            "campaign_file": self.campaign_file,
            "check_interval_seconds": self.check_interval,
            "stats": self.stats.copy(),
            "schedule": schedule_stats
        }
        
        if self.stats["started_at"]:
            uptime = datetime.utcnow() - self.stats["started_at"]
            status["uptime_seconds"] = uptime.total_seconds()
        
        return status
    
    async def run_once(self):
        """Run one check cycle (useful for testing)."""
        logger.info("Running one scheduler check cycle")
        await self._check_and_execute_posts()
    
    def cleanup_old_posts(self, days_old: int = 30):
        """Clean up old posts."""
        self.scheduler.cleanup_old_posts(days_old)
    
    def pause_schedule(self):
        """Pause all scheduled posts."""
        self.scheduler.pause_schedule()
        logger.info("Schedule paused")
    
    def resume_schedule(self):
        """Resume all scheduled posts."""
        self.scheduler.resume_schedule()
        logger.info("Schedule resumed")


async def run_background_scheduler(
    campaign_file: str = "campaign.yaml",
    check_interval: int = 60,
    daemon: bool = False
):
    """Run the background scheduler."""
    
    scheduler = BackgroundScheduler(
        campaign_file=campaign_file,
        check_interval_seconds=check_interval
    )
    
    if daemon:
        # Run in background daemon mode
        import os
        import atexit
        
        # Fork to background
        pid = os.fork()
        if pid > 0:
            # Parent process - exit
            print(f"Background scheduler started with PID: {pid}")
            sys.exit(0)
        
        # Child process continues
        os.setsid()  # Create new session
        
        # Register cleanup on exit
        atexit.register(scheduler.stop)
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, stopping scheduler")
        scheduler.stop()
    except Exception as e:
        logger.error(f"Background scheduler error: {e}")
        scheduler.stop()
        raise


def create_scheduler_daemon(
    campaign_file: str = "campaign.yaml",
    check_interval: int = 60,
    pid_file: Optional[str] = None
):
    """Create a scheduler daemon process."""
    
    if pid_file is None:
        pid_file = ".aetherpost/scheduler.pid"
    
    pid_path = Path(pid_file)
    
    # Check if already running
    if pid_path.exists():
        try:
            with open(pid_path, 'r') as f:
                existing_pid = int(f.read().strip())
            
            # Check if process is still running
            import os
            try:
                os.kill(existing_pid, 0)  # Check if process exists
                logger.error(f"Scheduler already running with PID {existing_pid}")
                return False
            except OSError:
                # Process doesn't exist, remove stale PID file
                pid_path.unlink()
        except (ValueError, FileNotFoundError):
            # Invalid or missing PID file
            if pid_path.exists():
                pid_path.unlink()
    
    # Fork to create daemon
    import os
    
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process
            print(f"Background scheduler daemon started with PID: {pid}")
            
            # Write PID file
            pid_path.parent.mkdir(exist_ok=True)
            with open(pid_path, 'w') as f:
                f.write(str(pid))
            
            return True
    except OSError as e:
        logger.error(f"Failed to fork daemon: {e}")
        return False
    
    # Child process - become daemon
    try:
        os.setsid()  # Create new session
        
        # Fork again to ensure we're not session leader
        pid = os.fork()
        if pid > 0:
            os._exit(0)
        
        # Redirect standard streams
        import os
        os.chdir("/")
        os.umask(0)
        
        # Redirect stdin, stdout, stderr
        with open(os.devnull, 'r') as devnull:
            os.dup2(devnull.fileno(), sys.stdin.fileno())
        
        # Log to file instead of stdout/stderr
        log_file = pid_path.parent / "scheduler.log"
        with open(log_file, 'a') as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
            os.dup2(f.fileno(), sys.stderr.fileno())
        
        # Setup logging to file
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
            ]
        )
        
        # Remove PID file on exit
        import atexit
        def cleanup():
            if pid_path.exists():
                pid_path.unlink()
        atexit.register(cleanup)
        
        # Run the scheduler
        asyncio.run(run_background_scheduler(
            campaign_file=campaign_file,
            check_interval=check_interval
        ))
        
    except Exception as e:
        logger.error(f"Daemon error: {e}")
        os._exit(1)


def stop_scheduler_daemon(pid_file: str = ".aetherpost/scheduler.pid"):
    """Stop the scheduler daemon."""
    
    pid_path = Path(pid_file)
    
    if not pid_path.exists():
        logger.info("No scheduler daemon running")
        return False
    
    try:
        with open(pid_path, 'r') as f:
            pid = int(f.read().strip())
        
        import os
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to exit
        import time
        for _ in range(10):  # Wait up to 10 seconds
            try:
                os.kill(pid, 0)
                time.sleep(1)
            except OSError:
                # Process has exited
                break
        else:
            # Force kill if still running
            logger.warning(f"Force killing scheduler daemon PID {pid}")
            os.kill(pid, signal.SIGKILL)
        
        # Remove PID file
        pid_path.unlink()
        logger.info(f"Stopped scheduler daemon PID {pid}")
        return True
        
    except (ValueError, FileNotFoundError, ProcessLookupError) as e:
        logger.error(f"Error stopping daemon: {e}")
        if pid_path.exists():
            pid_path.unlink()
        return False