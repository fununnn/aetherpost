"""Secure project file reader with security controls."""

import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import fnmatch
import yaml
from dataclasses import dataclass

from ..exceptions import AetherPostError, ErrorCode


@dataclass
class ProjectFile:
    """Represents a project file with metadata."""
    path: str
    relative_path: str
    content: str
    size: int
    hash: str
    last_modified: float


@dataclass
class ProjectContext:
    """Project context data structure."""
    files: List[ProjectFile]
    total_files: int
    total_size: int
    scan_time: float
    safe_files: int
    excluded_files: int
    oversized_files: int


class ProjectContextReader:
    """
    Secure project file reader with comprehensive security controls.
    
    Security Features:
    - Path traversal prevention
    - Sensitive information detection and filtering
    - File size limits (10KB per file)
    - Whitelist-based access control
    - Read-only operations
    """
    
    # Security configuration
    MAX_FILE_SIZE = 10 * 1024  # 10KB per file
    MAX_TOTAL_FILES = 100      # Maximum files to read
    MAX_TOTAL_SIZE = 1024 * 1024  # 1MB total content
    
    # Sensitive information patterns
    SENSITIVE_PATTERNS = [
        r'password\s*[=:]\s*["\']?[^"\'\s]+',
        r'secret\s*[=:]\s*["\']?[^"\'\s]+',
        r'key\s*[=:]\s*["\']?[^"\'\s]+',
        r'token\s*[=:]\s*["\']?[^"\'\s]+',
        r'api_key\s*[=:]\s*["\']?[^"\'\s]+',
        r'private_key\s*[=:]\s*["\']?[^"\'\s]+',
        r'access_token\s*[=:]\s*["\']?[^"\'\s]+',
        r'[A-Za-z0-9+/]{40,}={0,2}',  # Base64 patterns
        r'sk-[A-Za-z0-9]{32,}',       # OpenAI API keys
        r'xoxb-[A-Za-z0-9-]+',        # Slack tokens
    ]
    
    # File patterns to always exclude
    DEFAULT_EXCLUDES = [
        "*.secret",
        "*.key", 
        "*.pem",
        "*.p12",
        "*.pfx",
        ".env*",
        "node_modules",
        "__pycache__",
        "*.pyc",
        ".git",
        ".svn",
        ".hg",
        "*.log",
        "*.tmp",
        ".DS_Store",
        "Thumbs.db",
        "*.swp",
        "*.swo",
        ".vscode",
        ".idea",
        "*.exe",
        "*.dll",
        "*.so",
        "*.dylib",
        "credentials.json",
        "config.json",
        ".aws",
        ".ssh",
    ]
    
    def __init__(self):
        """Initialize the project reader."""
        self.project_root = Path.cwd()
        self.sensitive_regex = re.compile(
            '|'.join(self.SENSITIVE_PATTERNS), 
            re.IGNORECASE | re.MULTILINE
        )
    
    def load_context_config(self, campaign_file: str = "campaign.yaml") -> Dict:
        """
        Load context configuration from campaign.yaml.
        
        Args:
            campaign_file: Path to campaign configuration file
            
        Returns:
            Context configuration dictionary
            
        Raises:
            AetherPostError: If config cannot be loaded
        """
        try:
            campaign_path = self.project_root / campaign_file
            if not campaign_path.exists():
                return {"enabled": False}
            
            with open(campaign_path, 'r', encoding='utf-8') as f:
                campaign = yaml.safe_load(f)
            
            context_config = campaign.get('context', {})
            
            # Validate configuration
            if not isinstance(context_config, dict):
                raise AetherPostError("Context configuration must be a dictionary", ErrorCode.CONFIG_INVALID)
            
            # Set defaults
            context_config.setdefault('enabled', False)
            context_config.setdefault('watch', [])
            context_config.setdefault('exclude', [])
            
            return context_config
            
        except yaml.YAMLError as e:
            raise AetherPostError(f"Failed to parse campaign.yaml: {e}", ErrorCode.CONFIG_INVALID)
        except Exception as e:
            raise AetherPostError(f"Failed to load context config: {e}", ErrorCode.CONFIG_NOT_FOUND)
    
    def read_project_context(self, campaign_file: str = "campaign.yaml") -> Optional[ProjectContext]:
        """
        Read project context based on campaign configuration.
        
        Args:
            campaign_file: Path to campaign configuration file
            
        Returns:
            ProjectContext object or None if disabled
            
        Raises:
            AetherPostError: If reading fails
        """
        import time
        start_time = time.time()
        
        # Load configuration
        config = self.load_context_config(campaign_file)
        
        if not config.get('enabled', False):
            return None
        
        watch_paths = config.get('watch', [])
        exclude_patterns = config.get('exclude', [])
        
        if not watch_paths:
            return ProjectContext(
                files=[],
                total_files=0,
                total_size=0,
                scan_time=time.time() - start_time,
                safe_files=0,
                excluded_files=0,
                oversized_files=0
            )
        
        # Combine exclude patterns
        all_excludes = self.DEFAULT_EXCLUDES + exclude_patterns
        
        # Read files safely
        files = []
        excluded_count = 0
        oversized_count = 0
        total_size = 0
        
        for watch_path in watch_paths:
            path_files, path_excluded, path_oversized = self._read_path_safely(
                watch_path, all_excludes
            )
            files.extend(path_files)
            excluded_count += path_excluded
            oversized_count += path_oversized
            total_size += sum(f.size for f in path_files)
            
            # Check total size limit
            if total_size > self.MAX_TOTAL_SIZE:
                remaining_files = []
                current_size = 0
                for f in files:
                    if current_size + f.size <= self.MAX_TOTAL_SIZE:
                        remaining_files.append(f)
                        current_size += f.size
                    else:
                        oversized_count += 1
                files = remaining_files
                break
            
            # Check total file limit
            if len(files) >= self.MAX_TOTAL_FILES:
                files = files[:self.MAX_TOTAL_FILES]
                break
        
        return ProjectContext(
            files=files,
            total_files=len(files),
            total_size=sum(f.size for f in files),
            scan_time=time.time() - start_time,
            safe_files=len(files),
            excluded_files=excluded_count,
            oversized_files=oversized_count
        )
    
    def _read_path_safely(self, watch_path: str, exclude_patterns: List[str]) -> Tuple[List[ProjectFile], int, int]:
        """
        Safely read files from a watch path.
        
        Args:
            watch_path: Path to read (relative to project root)
            exclude_patterns: Patterns to exclude
            
        Returns:
            Tuple of (files, excluded_count, oversized_count)
        """
        files = []
        excluded_count = 0
        oversized_count = 0
        
        # Resolve and validate path
        try:
            abs_watch_path = self._resolve_safe_path(watch_path)
        except AetherPostError:
            # Invalid path, skip
            return files, excluded_count + 1, oversized_count
        
        # Handle single file
        if abs_watch_path.is_file():
            if self._should_exclude_file(abs_watch_path, exclude_patterns):
                excluded_count += 1
            else:
                file_obj = self._read_file_safely(abs_watch_path)
                if file_obj:
                    files.append(file_obj)
                else:
                    oversized_count += 1
            return files, excluded_count, oversized_count
        
        # Handle directory
        if not abs_watch_path.is_dir():
            return files, excluded_count + 1, oversized_count
        
        try:
            for file_path in abs_watch_path.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # Check exclusion patterns
                if self._should_exclude_file(file_path, exclude_patterns):
                    excluded_count += 1
                    continue
                
                # Read file safely
                file_obj = self._read_file_safely(file_path)
                if file_obj:
                    files.append(file_obj)
                else:
                    oversized_count += 1
                
                # Respect limits
                if len(files) >= self.MAX_TOTAL_FILES:
                    break
                    
        except (PermissionError, OSError):
            # Skip inaccessible directories
            excluded_count += 1
        
        return files, excluded_count, oversized_count
    
    def _resolve_safe_path(self, path: str) -> Path:
        """
        Resolve path safely, preventing path traversal.
        
        Args:
            path: Relative path to resolve
            
        Returns:
            Resolved absolute path
            
        Raises:
            AetherPostError: If path is unsafe
        """
        try:
            # Normalize the path
            normalized = os.path.normpath(path)
            
            # Prevent dangerous path traversal (but allow relative paths like ../file.txt)
            if normalized.startswith('/') or '/../' in normalized or normalized.startswith('../../../'):
                raise AetherPostError(f"Dangerous path detected: {path}", ErrorCode.PERMISSION_DENIED)
            
            # Resolve relative to project root
            resolved = (self.project_root / normalized).resolve()
            
            # Ensure the resolved path is within project root
            try:
                resolved.relative_to(self.project_root.resolve())
            except ValueError:
                raise AetherPostError(f"Path outside project root: {path}", ErrorCode.PERMISSION_DENIED)
            
            return resolved
            
        except AetherPostError:
            raise  # Re-raise AetherPostError as-is
        except Exception as e:
            raise AetherPostError(f"Invalid path: {path} - {e}", ErrorCode.FILE_NOT_FOUND)
    
    def _should_exclude_file(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """
        Check if file should be excluded based on patterns.
        
        Args:
            file_path: File path to check
            exclude_patterns: Exclusion patterns
            
        Returns:
            True if file should be excluded
        """
        relative_path = str(file_path.relative_to(self.project_root))
        file_name = file_path.name
        
        for pattern in exclude_patterns:
            # Check against full relative path
            if fnmatch.fnmatch(relative_path, pattern):
                return True
            # Check against filename only
            if fnmatch.fnmatch(file_name, pattern):
                return True
            # Check against directory names in path
            if pattern in relative_path.split(os.sep):
                return True
        
        return False
    
    def _read_file_safely(self, file_path: Path) -> Optional[ProjectFile]:
        """
        Read a single file safely with all security checks.
        
        Args:
            file_path: Path to file to read
            
        Returns:
            ProjectFile object or None if file cannot be read safely
        """
        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.MAX_FILE_SIZE:
                return None
            
            # Skip empty files
            if file_size == 0:
                return None
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                try:
                    with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                        content = f.read()
                except:
                    # Skip binary or unreadable files
                    return None
            
            # Check for sensitive information
            if self._contains_sensitive_info(content):
                return None
            
            # Calculate hash
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # Get relative path
            relative_path = str(file_path.relative_to(self.project_root))
            
            return ProjectFile(
                path=str(file_path),
                relative_path=relative_path,
                content=content,
                size=len(content.encode('utf-8')),
                hash=content_hash,
                last_modified=file_path.stat().st_mtime
            )
            
        except (PermissionError, OSError, IOError):
            # Skip inaccessible files
            return None
    
    def _contains_sensitive_info(self, content: str) -> bool:
        """
        Check if content contains sensitive information.
        
        Args:
            content: File content to check
            
        Returns:
            True if sensitive information detected
        """
        # Check for sensitive patterns
        if self.sensitive_regex.search(content):
            return True
        
        # Check for long base64-like strings (potential keys)
        base64_pattern = re.compile(r'[A-Za-z0-9+/]{50,}={0,2}')
        if base64_pattern.search(content):
            return True
        
        # Check for environment variable assignments with sensitive names
        env_pattern = re.compile(r'^(PASSWORD|SECRET|KEY|TOKEN|API_KEY)=', re.MULTILINE | re.IGNORECASE)
        if env_pattern.search(content):
            return True
        
        return False
    
    def get_file_summary(self, context: ProjectContext) -> Dict:
        """
        Generate a summary of the project context for AI consumption.
        
        Args:
            context: Project context to summarize
            
        Returns:
            Summary dictionary suitable for AI prompts
        """
        if not context or not context.files:
            return {"summary": "No project files accessible for context."}
        
        # Categorize files by type
        file_types = {}
        for file_obj in context.files:
            ext = Path(file_obj.relative_path).suffix.lower() or 'no_extension'
            if ext not in file_types:
                file_types[ext] = []
            file_types[ext].append(file_obj.relative_path)
        
        # Create summary
        summary = {
            "total_files": context.total_files,
            "total_size_kb": round(context.total_size / 1024, 2),
            "file_types": {ext: len(files) for ext, files in file_types.items()},
            "scan_time_ms": round(context.scan_time * 1000, 2),
            "security_stats": {
                "safe_files": context.safe_files,
                "excluded_files": context.excluded_files,
                "oversized_files": context.oversized_files
            }
        }
        
        # Add file contents for small projects
        if context.total_files <= 10 and context.total_size <= 50000:  # 50KB
            summary["file_contents"] = {}
            for file_obj in context.files:
                # Truncate very long files
                content = file_obj.content
                if len(content) > 2000:
                    content = content[:2000] + "\n... (truncated)"
                summary["file_contents"][file_obj.relative_path] = content
        else:
            # For larger projects, just include structure
            summary["file_structure"] = [f.relative_path for f in context.files]
        
        return summary