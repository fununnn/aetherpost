"""Unified error handling and logging system for AetherPost."""

import logging
import traceback
import functools
from typing import Dict, List, Any, Optional, Callable, Type, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import sys
import os

from .base_models import OperationResult


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization."""
    AUTHENTICATION = "authentication"
    API_LIMIT = "api_limit"
    NETWORK = "network"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    PLATFORM = "platform"
    CONTENT = "content"
    TEMPLATE = "template"
    FILE_SYSTEM = "file_system"
    PERMISSION = "permission"
    UNKNOWN = "unknown"


@dataclass
class AetherPostError:
    """Structured error information."""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    suggestions: List[str] = None
    context: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.suggestions is None:
            self.suggestions = []
        if self.context is None:
            self.context = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_id": self.error_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


class AetherPostException(Exception):
    """Base exception class for AetherPost."""
    
    def __init__(self, error: AetherPostError, original_exception: Optional[Exception] = None):
        self.error = error
        self.original_exception = original_exception
        super().__init__(error.message)


class AuthenticationError(AetherPostException):
    """Authentication-related errors."""
    
    def __init__(self, message: str, platform: str = None, **kwargs):
        error = AetherPostError(
            error_id="AUTH_ERROR",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            message=message,
            context={"platform": platform} if platform else {},
            suggestions=[
                "Check your API credentials",
                "Verify platform-specific authentication requirements",
                "Run 'aetherpost auth' to reconfigure credentials"
            ],
            **kwargs
        )
        super().__init__(error)


class APILimitError(AetherPostException):
    """API rate limit errors."""
    
    def __init__(self, message: str, platform: str = None, retry_after: int = None, **kwargs):
        context = {"platform": platform} if platform else {}
        if retry_after:
            context["retry_after"] = retry_after
        
        suggestions = [
            "Wait for rate limit to reset",
            "Consider reducing posting frequency",
            "Check platform API documentation for limits"
        ]
        
        if retry_after:
            suggestions.insert(0, f"Retry after {retry_after} seconds")
        
        error = AetherPostError(
            error_id="API_LIMIT_ERROR",
            category=ErrorCategory.API_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            message=message,
            context=context,
            suggestions=suggestions,
            **kwargs
        )
        super().__init__(error)


class ValidationError(AetherPostException):
    """Content validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        context = {}
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)
        
        error = AetherPostError(
            error_id="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            message=message,
            context=context,
            suggestions=[
                "Check content format and requirements",
                "Validate against platform constraints",
                "Use 'aetherpost validate' command"
            ],
            **kwargs
        )
        super().__init__(error)


class ConfigurationError(AetherPostException):
    """Configuration-related errors."""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        context = {"config_key": config_key} if config_key else {}
        
        error = AetherPostError(
            error_id="CONFIG_ERROR",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            message=message,
            context=context,
            suggestions=[
                "Check configuration file syntax",
                "Run 'aetherpost setup' to reconfigure",
                "Verify all required settings are present"
            ],
            **kwargs
        )
        super().__init__(error)


class PlatformError(AetherPostException):
    """Platform-specific errors."""
    
    def __init__(self, message: str, platform: str, error_code: str = None, **kwargs):
        context = {"platform": platform}
        if error_code:
            context["error_code"] = error_code
        
        error = AetherPostError(
            error_id="PLATFORM_ERROR",
            category=ErrorCategory.PLATFORM,
            severity=ErrorSeverity.MEDIUM,
            message=message,
            context=context,
            suggestions=[
                f"Check {platform} platform status",
                "Verify platform-specific requirements",
                "Consult platform documentation"
            ],
            **kwargs
        )
        super().__init__(error)


class ErrorHandler:
    """Centralized error handling and logging."""
    
    def __init__(self, logger_name: str = "aetherpost"):
        self.logger = logging.getLogger(logger_name)
        self.error_history: List[AetherPostError] = []
        self.error_mapping = self._setup_error_mapping()
    
    def _setup_error_mapping(self) -> Dict[Type[Exception], Callable]:
        """Setup mapping from standard exceptions to AetherPost errors."""
        return {
            ConnectionError: self._handle_network_error,
            TimeoutError: self._handle_network_error,
            FileNotFoundError: self._handle_file_error,
            PermissionError: self._handle_permission_error,
            ValueError: self._handle_validation_error,
            KeyError: self._handle_configuration_error,
            ImportError: self._handle_dependency_error,
        }
    
    def handle_exception(self, exception: Exception, 
                        context: Dict[str, Any] = None) -> AetherPostError:
        """Handle any exception and convert to structured error."""
        
        # If it's already an AetherPost exception, return the error
        if isinstance(exception, AetherPostException):
            error = exception.error
        else:
            # Map standard exceptions to AetherPost errors
            handler = self.error_mapping.get(type(exception), self._handle_unknown_error)
            error = handler(exception, context or {})
        
        # Log the error
        self._log_error(error, exception)
        
        # Store in history
        self.error_history.append(error)
        
        return error
    
    def _handle_network_error(self, exception: Exception, context: Dict[str, Any]) -> AetherPostError:
        """Handle network-related errors."""
        return AetherPostError(
            error_id="NETWORK_ERROR",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message=f"Network error: {str(exception)}",
            details=str(exception),
            context=context,
            suggestions=[
                "Check internet connection",
                "Verify API endpoints are accessible",
                "Check for firewall or proxy issues"
            ]
        )
    
    def _handle_file_error(self, exception: Exception, context: Dict[str, Any]) -> AetherPostError:
        """Handle file system errors."""
        return AetherPostError(
            error_id="FILE_ERROR",
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            message=f"File system error: {str(exception)}",
            details=str(exception),
            context=context,
            suggestions=[
                "Check file permissions",
                "Verify file paths exist",
                "Ensure sufficient disk space"
            ]
        )
    
    def _handle_permission_error(self, exception: Exception, context: Dict[str, Any]) -> AetherPostError:
        """Handle permission errors."""
        return AetherPostError(
            error_id="PERMISSION_ERROR",
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.HIGH,
            message=f"Permission denied: {str(exception)}",
            details=str(exception),
            context=context,
            suggestions=[
                "Check file/directory permissions",
                "Run with appropriate user privileges",
                "Verify access rights"
            ]
        )
    
    def _handle_validation_error(self, exception: Exception, context: Dict[str, Any]) -> AetherPostError:
        """Handle validation errors."""
        return AetherPostError(
            error_id="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            message=f"Validation error: {str(exception)}",
            details=str(exception),
            context=context,
            suggestions=[
                "Check input data format",
                "Verify required fields are present",
                "Validate data types and constraints"
            ]
        )
    
    def _handle_configuration_error(self, exception: Exception, context: Dict[str, Any]) -> AetherPostError:
        """Handle configuration errors."""
        return AetherPostError(
            error_id="CONFIG_ERROR",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            message=f"Configuration error: {str(exception)}",
            details=str(exception),
            context=context,
            suggestions=[
                "Check configuration file format",
                "Verify all required settings",
                "Run setup wizard to reconfigure"
            ]
        )
    
    def _handle_dependency_error(self, exception: Exception, context: Dict[str, Any]) -> AetherPostError:
        """Handle dependency/import errors."""
        return AetherPostError(
            error_id="DEPENDENCY_ERROR",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.HIGH,
            message=f"Dependency error: {str(exception)}",
            details=str(exception),
            context=context,
            suggestions=[
                "Install missing dependencies",
                "Check Python environment",
                "Verify package versions"
            ]
        )
    
    def _handle_unknown_error(self, exception: Exception, context: Dict[str, Any]) -> AetherPostError:
        """Handle unknown errors."""
        return AetherPostError(
            error_id="UNKNOWN_ERROR",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            message=f"Unexpected error: {str(exception)}",
            details=str(exception),
            context=context,
            suggestions=[
                "Check logs for more details",
                "Report issue if problem persists",
                "Try alternative approach"
            ]
        )
    
    def _log_error(self, error: AetherPostError, exception: Exception = None) -> None:
        """Log error with appropriate level."""
        
        # Determine log level based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            log_level = logging.CRITICAL
        elif error.severity == ErrorSeverity.HIGH:
            log_level = logging.ERROR
        elif error.severity == ErrorSeverity.MEDIUM:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # Create log message
        log_message = f"[{error.error_id}] {error.message}"
        if error.context:
            log_message += f" | Context: {error.context}"
        
        # Log with stack trace for high severity errors
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and exception:
            self.logger.log(log_level, log_message, exc_info=True)
        else:
            self.logger.log(log_level, log_message)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        if not self.error_history:
            return {"total_errors": 0, "by_category": {}, "by_severity": {}}
        
        # Count by category
        by_category = {}
        by_severity = {}
        
        for error in self.error_history:
            # Count by category
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1
            
            # Count by severity
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": [error.to_dict() for error in self.error_history[-5:]]
        }
    
    def clear_error_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()


# Global error handler instance
error_handler = ErrorHandler()


def handle_errors(func: Callable = None, *, 
                 return_result: bool = True,
                 log_errors: bool = True,
                 reraise: bool = False):
    """Decorator for unified error handling."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                if return_result and not isinstance(result, OperationResult):
                    return OperationResult.success_result(
                        "Operation completed successfully",
                        data=result
                    )
                return result
                
            except Exception as e:
                error = error_handler.handle_exception(e, {
                    "function": func.__name__,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                })
                
                if reraise:
                    raise AetherPostException(error, e) from e
                
                if return_result:
                    return OperationResult.error_result(
                        error.message,
                        errors=[error.message],
                        metadata={"error_id": error.error_id, "category": error.category.value}
                    )
                else:
                    return None
        
        return wrapper
    
    # Support both @handle_errors and @handle_errors()
    if func is None:
        return decorator
    else:
        return decorator(func)


def safe_execute(func: Callable, *args, default=None, **kwargs) -> Any:
    """Safely execute function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_exception(e, {
            "function": func.__name__ if hasattr(func, '__name__') else str(func),
            "args": str(args)[:100],
            "kwargs": str(kwargs)[:100]
        })
        return default


def validate_and_raise(condition: bool, error_class: Type[AetherPostException], 
                      message: str, **kwargs) -> None:
    """Validate condition and raise specific error if false."""
    if not condition:
        raise error_class(message, **kwargs)


# Setup logging configuration
def setup_logging(level: Union[str, int] = logging.INFO,
                 log_file: Optional[str] = None,
                 format_string: Optional[str] = None) -> None:
    """Setup logging configuration for AetherPost."""
    
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[]
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    
    # File handler if specified
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # Apply to AetherPost logger
    autopromo_logger = logging.getLogger("aetherpost")
    autopromo_logger.handlers.clear()
    for handler in handlers:
        autopromo_logger.addHandler(handler)
    autopromo_logger.setLevel(level)
    autopromo_logger.propagate = False