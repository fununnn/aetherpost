"""Project difference detection system."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict

from .project_reader import ProjectContextReader, ProjectContext, ProjectFile
from ..exceptions import AetherPostError, ErrorCode


@dataclass
class FileChange:
    """Represents a file change."""
    path: str
    change_type: str  # 'added', 'modified', 'deleted'
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    size_change: int = 0


@dataclass 
class ProjectSnapshot:
    """Project state snapshot."""
    timestamp: float
    total_files: int
    total_size: int
    file_hashes: Dict[str, str]  # path -> hash
    file_sizes: Dict[str, int]   # path -> size
    last_scan_time: float


@dataclass
class ProjectDiff:
    """Project differences between snapshots."""
    old_snapshot: Optional[ProjectSnapshot]
    new_snapshot: ProjectSnapshot
    changes: List[FileChange]
    added_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]
    total_changes: int
    has_significant_changes: bool


class ProjectDiffDetector:
    """
    Detects and tracks changes in project files over time.
    
    Features:
    - Persistent snapshot storage in .aetherpost/project_snapshot.json
    - MD5 hash-based change detection
    - Change categorization (added/modified/deleted)
    - Significant change threshold detection
    """
    
    def __init__(self, aetherpost_dir: str = ".aetherpost"):
        """
        Initialize the diff detector.
        
        Args:
            aetherpost_dir: Directory to store snapshots
        """
        self.aetherpost_dir = Path(aetherpost_dir)
        self.snapshot_file = self.aetherpost_dir / "project_snapshot.json"
        self.reader = ProjectContextReader()
        
        # Ensure directory exists
        self.aetherpost_dir.mkdir(exist_ok=True)
    
    def create_snapshot(self, context: ProjectContext) -> ProjectSnapshot:
        """
        Create a snapshot from project context.
        
        Args:
            context: Project context to snapshot
            
        Returns:
            ProjectSnapshot object
        """
        file_hashes = {}
        file_sizes = {}
        
        for file_obj in context.files:
            file_hashes[file_obj.relative_path] = file_obj.hash
            file_sizes[file_obj.relative_path] = file_obj.size
        
        return ProjectSnapshot(
            timestamp=time.time(),
            total_files=context.total_files,
            total_size=context.total_size,
            file_hashes=file_hashes,
            file_sizes=file_sizes,
            last_scan_time=context.scan_time
        )
    
    def load_last_snapshot(self) -> Optional[ProjectSnapshot]:
        """
        Load the last saved snapshot.
        
        Returns:
            ProjectSnapshot object or None if no snapshot exists
        """
        if not self.snapshot_file.exists():
            return None
        
        try:
            with open(self.snapshot_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ProjectSnapshot(
                timestamp=data['timestamp'],
                total_files=data['total_files'],
                total_size=data['total_size'],
                file_hashes=data['file_hashes'],
                file_sizes=data['file_sizes'],
                last_scan_time=data.get('last_scan_time', 0.0)
            )
            
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            # Corrupted or missing snapshot
            return None
    
    def save_snapshot(self, snapshot: ProjectSnapshot) -> None:
        """
        Save snapshot to disk.
        
        Args:
            snapshot: Snapshot to save
            
        Raises:
            AetherPostError: If save fails
        """
        try:
            with open(self.snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(snapshot), f, indent=2)
        except Exception as e:
            raise AetherPostError(f"Failed to save snapshot: {e}", ErrorCode.FILE_NOT_FOUND)
    
    def detect_changes(self, campaign_file: str = "campaign.yaml") -> Optional[ProjectDiff]:
        """
        Detect changes since last snapshot.
        
        Args:
            campaign_file: Campaign configuration file
            
        Returns:
            ProjectDiff object or None if no context enabled
            
        Raises:
            AetherPostError: If detection fails
        """
        # Read current project context
        current_context = self.reader.read_project_context(campaign_file)
        
        if not current_context:
            # Context reading disabled
            return None
        
        # Create current snapshot
        new_snapshot = self.create_snapshot(current_context)
        
        # Load previous snapshot
        old_snapshot = self.load_last_snapshot()
        
        # Calculate differences
        changes = self._calculate_changes(old_snapshot, new_snapshot)
        
        # Categorize changes
        added_files = [c.path for c in changes if c.change_type == 'added']
        modified_files = [c.path for c in changes if c.change_type == 'modified']
        deleted_files = [c.path for c in changes if c.change_type == 'deleted']
        
        # Determine if changes are significant
        has_significant = self._has_significant_changes(changes, old_snapshot, new_snapshot)
        
        # Save new snapshot
        self.save_snapshot(new_snapshot)
        
        return ProjectDiff(
            old_snapshot=old_snapshot,
            new_snapshot=new_snapshot,
            changes=changes,
            added_files=added_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            total_changes=len(changes),
            has_significant_changes=has_significant
        )
    
    def _calculate_changes(self, old_snapshot: Optional[ProjectSnapshot], 
                          new_snapshot: ProjectSnapshot) -> List[FileChange]:
        """
        Calculate changes between snapshots.
        
        Args:
            old_snapshot: Previous snapshot (may be None for first run)
            new_snapshot: Current snapshot
            
        Returns:
            List of FileChange objects
        """
        changes = []
        
        if not old_snapshot:
            # First run - all files are "added"
            for path, hash_val in new_snapshot.file_hashes.items():
                changes.append(FileChange(
                    path=path,
                    change_type='added',
                    new_hash=hash_val,
                    size_change=new_snapshot.file_sizes.get(path, 0)
                ))
            return changes
        
        old_files = set(old_snapshot.file_hashes.keys())
        new_files = set(new_snapshot.file_hashes.keys())
        
        # Added files
        for path in new_files - old_files:
            changes.append(FileChange(
                path=path,
                change_type='added',
                new_hash=new_snapshot.file_hashes[path],
                size_change=new_snapshot.file_sizes.get(path, 0)
            ))
        
        # Deleted files
        for path in old_files - new_files:
            changes.append(FileChange(
                path=path,
                change_type='deleted',
                old_hash=old_snapshot.file_hashes[path],
                size_change=-old_snapshot.file_sizes.get(path, 0)
            ))
        
        # Modified files
        for path in old_files & new_files:
            old_hash = old_snapshot.file_hashes[path]
            new_hash = new_snapshot.file_hashes[path]
            
            if old_hash != new_hash:
                old_size = old_snapshot.file_sizes.get(path, 0)
                new_size = new_snapshot.file_sizes.get(path, 0)
                
                changes.append(FileChange(
                    path=path,
                    change_type='modified',
                    old_hash=old_hash,
                    new_hash=new_hash,
                    size_change=new_size - old_size
                ))
        
        return changes
    
    def _has_significant_changes(self, changes: List[FileChange], 
                                old_snapshot: Optional[ProjectSnapshot],
                                new_snapshot: ProjectSnapshot) -> bool:
        """
        Determine if changes are significant enough for content generation.
        
        Args:
            changes: List of file changes
            old_snapshot: Previous snapshot
            new_snapshot: Current snapshot
            
        Returns:
            True if changes are significant
        """
        if not changes:
            return False
        
        # First run is always significant
        if not old_snapshot:
            return True
        
        # Check for significant change types
        significant_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.txt', '.yaml', '.yml', '.json'}
        significant_files = {'README.md', 'CHANGELOG.md', 'package.json', 'pyproject.toml', 'requirements.txt'}
        
        for change in changes:
            file_path = Path(change.path)
            
            # Check if it's a significant file type
            if file_path.suffix.lower() in significant_extensions:
                return True
            
            # Check if it's a significant file name
            if file_path.name in significant_files:
                return True
            
            # Check if it's a documentation change
            if 'doc' in change.path.lower() or 'readme' in change.path.lower():
                return True
        
        # Check change volume
        total_size_change = sum(abs(c.size_change) for c in changes)
        if total_size_change > 1000:  # More than 1KB of changes
            return True
        
        # Check number of files changed
        if len(changes) >= 3:
            return True
        
        return False
    
    def get_changes_summary(self, diff: ProjectDiff) -> Dict:
        """
        Generate a summary of changes for AI consumption.
        
        Args:
            diff: Project differences
            
        Returns:
            Summary dictionary suitable for AI prompts
        """
        if not diff.has_significant_changes:
            return {"summary": "No significant changes detected."}
        
        summary = {
            "total_changes": diff.total_changes,
            "has_significant_changes": diff.has_significant_changes,
            "change_types": {
                "added": len(diff.added_files),
                "modified": len(diff.modified_files),
                "deleted": len(diff.deleted_files)
            }
        }
        
        # Add details for small change sets
        if diff.total_changes <= 10:
            summary["detailed_changes"] = []
            for change in diff.changes:
                detail = {
                    "file": change.path,
                    "type": change.change_type,
                    "size_change": change.size_change
                }
                summary["detailed_changes"].append(detail)
        else:
            # For large change sets, just list affected files
            summary["affected_files"] = {
                "added": diff.added_files[:5],  # Limit to first 5
                "modified": diff.modified_files[:5],
                "deleted": diff.deleted_files[:5]
            }
            if len(diff.added_files) > 5:
                summary["affected_files"]["added_truncated"] = f"... and {len(diff.added_files) - 5} more"
            if len(diff.modified_files) > 5:
                summary["affected_files"]["modified_truncated"] = f"... and {len(diff.modified_files) - 5} more"
            if len(diff.deleted_files) > 5:
                summary["affected_files"]["deleted_truncated"] = f"... and {len(diff.deleted_files) - 5} more"
        
        # Add timing information
        if diff.old_snapshot:
            time_since_last = diff.new_snapshot.timestamp - diff.old_snapshot.timestamp
            summary["time_since_last_scan"] = {
                "seconds": round(time_since_last, 2),
                "hours": round(time_since_last / 3600, 2),
                "days": round(time_since_last / 86400, 2)
            }
        else:
            summary["first_scan"] = True
        
        return summary
    
    def cleanup_old_snapshots(self, keep_count: int = 5) -> None:
        """
        Clean up old snapshot files (if we implement versioned snapshots in the future).
        
        Args:
            keep_count: Number of snapshots to keep
        """
        # Currently we only keep one snapshot, but this method is prepared
        # for future enhancement to keep multiple snapshots
        pass
    
    def reset_snapshots(self) -> None:
        """
        Reset all snapshots (useful for testing or manual reset).
        """
        if self.snapshot_file.exists():
            self.snapshot_file.unlink()
    
    def get_snapshot_info(self) -> Optional[Dict]:
        """
        Get information about the current snapshot.
        
        Returns:
            Snapshot information dictionary or None
        """
        snapshot = self.load_last_snapshot()
        if not snapshot:
            return None
        
        return {
            "timestamp": snapshot.timestamp,
            "total_files": snapshot.total_files,
            "total_size": snapshot.total_size,
            "last_scan_time_ms": round(snapshot.last_scan_time * 1000, 2),
            "age_hours": round((time.time() - snapshot.timestamp) / 3600, 2)
        }