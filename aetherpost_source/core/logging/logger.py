"""Enhanced logging system for AetherPost."""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

from ..exceptions import AetherPostError


class LogLevel(Enum):
    """Log levels with numeric values."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """Log output formats."""
    SIMPLE = "simple"
    DETAILED = "detailed" 
    JSON = "json"
    STRUCTURED = "structured"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    level: str
    logger: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    platform: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    error_code: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class AetherPostFormatter(logging.Formatter):
    """Custom formatter for AetherPost logs."""
    
    def __init__(self, format_type: LogFormat = LogFormat.DETAILED, include_color: bool = True):
        self.format_type = format_type
        self.include_color = include_color
        
        # Color codes
        self.colors = {
            'DEBUG': '\033[36m',     # Cyan
            'INFO': '\033[32m',      # Green
            'WARNING': '\033[33m',   # Yellow
            'ERROR': '\033[31m',     # Red
            'CRITICAL': '\033[35m',  # Magenta
            'RESET': '\033[0m'       # Reset
        }
        
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record."""
        
        if self.format_type == LogFormat.JSON:
            return self._format_json(record)
        elif self.format_type == LogFormat.STRUCTURED:
            return self._format_structured(record)
        elif self.format_type == LogFormat.SIMPLE:
            return self._format_simple(record)
        else:
            return self._format_detailed(record)
    
    def _format_json(self, record: logging.LogRecord) -> str:
        """Format as JSON."""
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            module=getattr(record, 'module', None),
            function=getattr(record, 'funcName', None),
            line=getattr(record, 'lineno', None),
            platform=getattr(record, 'platform', None),
            user_id=getattr(record, 'user_id', None),
            session_id=getattr(record, 'session_id', None),
            error_code=getattr(record, 'error_code', None),
            extra=getattr(record, 'extra', None)
        )
        
        return json.dumps(log_entry.to_dict(), ensure_ascii=False)
    
    def _format_structured(self, record: logging.LogRecord) -> str:
        """Format as structured text."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        logger = record.name
        message = record.getMessage()
        
        # Add color if enabled
        if self.include_color:
            color = self.colors.get(level, '')
            reset = self.colors['RESET']
            level = f"{color}{level}{reset}"
        
        base = f"[{timestamp}] {level:<8} {logger:<20} | {message}"
        
        # Add extra context
        extras = []
        if hasattr(record, 'platform'):
            extras.append(f"platform={record.platform}")
        if hasattr(record, 'error_code'):
            extras.append(f"error_code={record.error_code}")
        if hasattr(record, 'user_id'):
            extras.append(f"user_id={record.user_id}")
        
        if extras:
            base += f" [{', '.join(extras)}]"
        
        return base
    
    def _format_simple(self, record: logging.LogRecord) -> str:
        """Format as simple text."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        level = record.levelname[0]  # First letter only
        message = record.getMessage()
        
        return f"{timestamp} {level} {message}"
    
    def _format_detailed(self, record: logging.LogRecord) -> str:
        """Format with full details."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level = record.levelname
        logger = record.name
        location = f"{record.filename}:{record.lineno}"
        message = record.getMessage()
        
        # Add color if enabled
        if self.include_color:
            color = self.colors.get(level, '')
            reset = self.colors['RESET']
            level = f"{color}{level}{reset}"
        
        base = f"[{timestamp}] {level:<8} {logger:<25} {location:<20} | {message}"
        
        # Add exception info if present
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        
        return base


class AetherPostLogger:
    """Enhanced logging system for AetherPost."""
    
    def __init__(self, name: str = "aetherpost"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.log_dir = Path("logs")
        self.session_id = self._generate_session_id()
        
        # Ensure logs directory exists
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging if not already configured
        if not self.logger.handlers:
            self._setup_logging()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _setup_logging(self):
        """Setup logging configuration."""
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set base level
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler with color
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = AetherPostFormatter(
            LogFormat.STRUCTURED, 
            include_color=True
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for detailed logs
        log_file = self.log_dir / "autopromo.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = AetherPostFormatter(LogFormat.DETAILED, include_color=False)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # JSON handler for structured logs
        json_file = self.log_dir / "autopromo.json"
        json_handler = logging.handlers.RotatingFileHandler(
            json_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3
        )
        json_handler.setLevel(logging.INFO)
        json_formatter = AetherPostFormatter(LogFormat.JSON)
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)
        
        # Error-only handler
        error_file = self.log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = AetherPostFormatter(LogFormat.DETAILED, include_color=False)
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
        
        # Audit log handler (for sensitive operations)
        audit_file = self.log_dir / "audit.log"
        self.audit_handler = logging.handlers.RotatingFileHandler(
            audit_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10  # Keep more audit logs
        )
        audit_formatter = AetherPostFormatter(LogFormat.JSON)
        self.audit_handler.setFormatter(audit_formatter)
        
        # Create audit logger
        self.audit_logger = logging.getLogger(f"{self.name}.audit")
        self.audit_logger.addHandler(self.audit_handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method."""
        # Add session ID to all logs
        kwargs['session_id'] = self.session_id
        
        # Extract platform if provided
        platform = kwargs.pop('platform', None)
        if platform:
            kwargs['platform'] = platform
        
        # Extract user ID if provided
        user_id = kwargs.pop('user_id', None)
        if user_id:
            kwargs['user_id'] = user_id
        
        # Extract error code if provided
        error_code = kwargs.pop('error_code', None)
        if error_code:
            kwargs['error_code'] = error_code
        
        # Store extra data
        extra_data = kwargs.pop('extra', {})
        if extra_data:
            kwargs['extra'] = extra_data
        
        self.logger.log(level, message, extra=kwargs)
    
    def log_error(self, error: AetherPostError, **kwargs):
        """Log AetherPost error with full context."""
        self._log(
            logging.ERROR,
            error.message,
            error_code=error.error_code.value,
            extra={
                'error_details': error.details,
                'suggestions': error.suggestions,
                'recoverable': error.recoverable
            },
            **kwargs
        )
    
    def audit(self, action: str, details: Dict[str, Any], **kwargs):
        """Log audit event."""
        audit_data = {
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'details': details,
            **kwargs
        }
        
        self.audit_logger.info(
            f"AUDIT: {action}",
            extra=audit_data
        )
    
    def platform_event(self, platform: str, event: str, details: Dict[str, Any]):
        """Log platform-specific event."""
        self.info(
            f"Platform event: {event}",
            platform=platform,
            extra=details
        )
    
    def performance_metric(self, metric_name: str, value: float, unit: str = "ms"):
        """Log performance metric."""
        self.info(
            f"Performance: {metric_name}",
            extra={
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                'type': 'performance'
            }
        )
    
    def user_action(self, action: str, user_id: Optional[str] = None, **kwargs):
        """Log user action."""
        self.info(
            f"User action: {action}",
            user_id=user_id,
            extra={'action_type': 'user_action', **kwargs}
        )
    
    def api_request(self, platform: str, endpoint: str, method: str, 
                   status_code: Optional[int] = None, duration: Optional[float] = None):
        """Log API request."""
        details = {
            'platform': platform,
            'endpoint': endpoint,
            'method': method,
            'type': 'api_request'
        }
        
        if status_code:
            details['status_code'] = status_code
        if duration:
            details['duration_ms'] = duration
        
        level = logging.ERROR if status_code and status_code >= 400 else logging.INFO
        self._log(
            level,
            f"API {method} {endpoint} -> {status_code or 'pending'}",
            platform=platform,
            extra=details
        )
    
    def set_level(self, level: LogLevel):
        """Set logging level."""
        self.logger.setLevel(level.value)
        
        # Update console handler level
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                handler.setLevel(level.value)
                break
    
    def add_file_handler(self, filename: str, level: LogLevel = LogLevel.INFO, 
                        format_type: LogFormat = LogFormat.DETAILED):
        """Add additional file handler."""
        file_path = self.log_dir / filename
        handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        handler.setLevel(level.value)
        
        formatter = AetherPostFormatter(format_type, include_color=False)
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        return handler
    
    def get_recent_logs(self, count: int = 100, level: Optional[LogLevel] = None) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        logs = []
        
        json_file = self.log_dir / "autopromo.json"
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    for line in f.readlines()[-count:]:
                        try:
                            log_entry = json.loads(line.strip())
                            if level is None or log_entry.get('level') == level.name:
                                logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                self.error(f"Failed to read recent logs: {e}")
        
        return logs
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up log files older than specified days."""
        import time
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        for log_file in self.log_dir.glob("*.log*"):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.info(f"Cleaned up old log file: {log_file}")
            except Exception as e:
                self.warning(f"Failed to clean up {log_file}: {e}")


# Global logger instance
logger = AetherPostLogger()


# Convenience functions
def debug(message: str, **kwargs):
    """Log debug message."""
    logger.debug(message, **kwargs)


def info(message: str, **kwargs):
    """Log info message."""
    logger.info(message, **kwargs)


def warning(message: str, **kwargs):
    """Log warning message."""
    logger.warning(message, **kwargs)


def error(message: str, **kwargs):
    """Log error message."""
    logger.error(message, **kwargs)


def critical(message: str, **kwargs):
    """Log critical message."""
    logger.critical(message, **kwargs)


def exception(message: str, **kwargs):
    """Log exception with traceback."""
    logger.exception(message, **kwargs)


def audit(action: str, details: Dict[str, Any], **kwargs):
    """Log audit event."""
    logger.audit(action, details, **kwargs)


def record_performance(operation: str, duration_ms: float, platform: Optional[str] = None, success: bool = True):
    """Record performance metrics."""
    logger.performance_metric(operation, duration_ms, "ms")


# Decorator for automatic function logging
def log_function_call(func):
    """Decorator to automatically log function calls."""
    
    def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Log function entry
        debug(f"Entering {func_name}", extra={
            'function': func_name,
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys())
        })
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # Log successful completion
            duration = (time.time() - start_time) * 1000
            debug(f"Completed {func_name}", extra={
                'function': func_name,
                'duration_ms': duration,
                'success': True
            })
            
            return result
            
        except Exception as e:
            # Log exception
            duration = (time.time() - start_time) * 1000
            error(f"Exception in {func_name}: {str(e)}", extra={
                'function': func_name,
                'duration_ms': duration,
                'success': False,
                'exception_type': type(e).__name__
            })
            raise
    
    return wrapper