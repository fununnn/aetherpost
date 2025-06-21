"""Unified exception handling system for AetherPost."""

from typing import Optional, Dict, Any
from enum import Enum
import logging


class ErrorCode(Enum):
    """Standardized error codes."""
    
    # Configuration Errors (1000-1099)
    CONFIG_NOT_FOUND = 1001
    CONFIG_INVALID = 1002
    CONFIG_MISSING_REQUIRED = 1003
    API_KEY_MISSING = 1004
    API_KEY_INVALID = 1005
    
    # Platform Errors (1100-1199)
    PLATFORM_NOT_SUPPORTED = 1101
    PLATFORM_AUTH_FAILED = 1102
    PLATFORM_API_ERROR = 1103
    PLATFORM_RATE_LIMITED = 1104
    PLATFORM_UNAVAILABLE = 1105
    
    # Content Errors (1200-1299)
    CONTENT_TOO_LONG = 1201
    CONTENT_INVALID_FORMAT = 1202
    CONTENT_GENERATION_FAILED = 1203
    MEDIA_GENERATION_FAILED = 1204
    CONTENT_VALIDATION_FAILED = 1205
    
    # System Errors (1300-1399)
    NETWORK_ERROR = 1301
    FILE_NOT_FOUND = 1302
    PERMISSION_DENIED = 1303
    DISK_SPACE_ERROR = 1304
    MEMORY_ERROR = 1305
    
    # Business Logic Errors (1400-1499)
    CAMPAIGN_NOT_FOUND = 1401
    CAMPAIGN_ALREADY_EXISTS = 1402
    INVALID_SCHEDULE = 1403
    QUOTA_EXCEEDED = 1404
    FEATURE_NOT_AVAILABLE = 1405


class AetherPostError(Exception):
    """Base exception class for AetherPost."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[list] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.suggestions = suggestions or []
        self.recoverable = recoverable
        
        # Log the error
        logger = logging.getLogger(__name__)
        logger.error(f"[{error_code.name}] {message}", extra={
            "error_code": error_code.value,
            "details": details,
            "recoverable": recoverable
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.error_code.value,
                "name": self.error_code.name,
                "message": self.message,
                "details": self.details,
                "suggestions": self.suggestions,
                "recoverable": self.recoverable
            }
        }
    
    def get_user_message(self) -> str:
        """Get user-friendly error message."""
        base_message = self.message
        
        if self.suggestions:
            suggestions_text = "\n".join(f"• {suggestion}" for suggestion in self.suggestions)
            return f"{base_message}\n\nSuggested actions:\n{suggestions_text}"
        
        return base_message


class ConfigurationError(AetherPostError):
    """Raised when there are configuration issues."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.CONFIG_INVALID, **kwargs):
        super().__init__(message, error_code, **kwargs)


class PlatformError(AetherPostError):
    """Raised when there are platform-specific issues."""
    
    def __init__(self, message: str, platform: str, error_code: ErrorCode = ErrorCode.PLATFORM_API_ERROR, **kwargs):
        details = kwargs.get('details', {})
        details['platform'] = platform
        kwargs['details'] = details
        super().__init__(message, error_code, **kwargs)


class ContentError(AetherPostError):
    """Raised when there are content-related issues."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.CONTENT_GENERATION_FAILED, **kwargs):
        super().__init__(message, error_code, **kwargs)


class RateLimitError(PlatformError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, platform: str, retry_after: Optional[int] = None, **kwargs):
        message = f"Rate limit exceeded for {platform}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        
        details = kwargs.get('details', {})
        details['retry_after'] = retry_after
        kwargs['details'] = details
        
        suggestions = kwargs.get('suggestions', [])
        suggestions.extend([
            f"Wait {retry_after} seconds before retrying" if retry_after else "Wait before retrying",
            "Consider upgrading your API plan",
            "Use the scheduler to spread out posts"
        ])
        kwargs['suggestions'] = suggestions
        
        super().__init__(message, platform, ErrorCode.PLATFORM_RATE_LIMITED, **kwargs)


class ValidationError(AetherPostError):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        kwargs['details'] = details
        
        super().__init__(message, ErrorCode.CONTENT_VALIDATION_FAILED, **kwargs)


# Error message templates for better UX
ERROR_MESSAGES = {
    ErrorCode.API_KEY_MISSING: {
        "message": "API key is missing for {platform}",
        "suggestions": [
            "Add your API key to .env.aetherpost",
            "Run 'aetherpost auth setup {platform}' to configure",
            "Check the setup guide: https://aether-post.com/getting-started.html"
        ]
    },
    ErrorCode.CONTENT_TOO_LONG: {
        "message": "Content exceeds {platform} character limit ({current}/{max})",
        "suggestions": [
            "Shorten your message",
            "Use 'aetherpost content optimize' to auto-shorten",
            "Split into multiple posts"
        ]
    },
    ErrorCode.PLATFORM_RATE_LIMITED: {
        "message": "Rate limit reached for {platform}",
        "suggestions": [
            "Wait before retrying",
            "Use scheduler to spread posts",
            "Consider upgrading API plan"
        ]
    }
}


def create_user_friendly_error(
    error_code: ErrorCode,
    **format_kwargs
) -> AetherPostError:
    """Create a user-friendly error with standardized messaging."""
    
    template = ERROR_MESSAGES.get(error_code, {
        "message": "An error occurred",
        "suggestions": ["Please try again or contact support"]
    })
    
    message = template["message"].format(**format_kwargs)
    suggestions = template["suggestions"]
    
    return AetherPostError(
        message=message,
        error_code=error_code,
        suggestions=suggestions,
        details=format_kwargs
    )


class ErrorHandler:
    """Centralized error handling."""
    
    @staticmethod
    def handle_platform_error(e: Exception, platform: str) -> AetherPostError:
        """Convert platform-specific exceptions to AetherPostError."""
        
        if "rate limit" in str(e).lower():
            return RateLimitError(platform=platform)
        elif "unauthorized" in str(e).lower() or "authentication" in str(e).lower():
            return create_user_friendly_error(
                ErrorCode.API_KEY_INVALID,
                platform=platform
            )
        elif "not found" in str(e).lower():
            return PlatformError(
                f"Resource not found on {platform}",
                platform=platform,
                error_code=ErrorCode.PLATFORM_API_ERROR
            )
        else:
            return PlatformError(
                f"Platform error: {str(e)}",
                platform=platform,
                error_code=ErrorCode.PLATFORM_API_ERROR
            )
    
    @staticmethod
    def handle_config_error(e: Exception) -> AetherPostError:
        """Convert configuration exceptions to AetherPostError."""
        
        if "not found" in str(e).lower():
            return create_user_friendly_error(ErrorCode.CONFIG_NOT_FOUND)
        elif "invalid" in str(e).lower():
            return create_user_friendly_error(ErrorCode.CONFIG_INVALID)
        else:
            return ConfigurationError(f"Configuration error: {str(e)}")
    
    @staticmethod
    def handle_content_error(e: Exception) -> AetherPostError:
        """Convert content exceptions to AetherPostError."""
        
        if "too long" in str(e).lower() or "character limit" in str(e).lower():
            return create_user_friendly_error(ErrorCode.CONTENT_TOO_LONG)
        else:
            return ContentError(f"Content error: {str(e)}")


# Decorator for automatic error handling
def handle_errors(func):
    """Decorator to automatically handle and convert exceptions."""
    
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AetherPostError:
            # Re-raise AetherPost errors as-is
            raise
        except Exception as e:
            # Convert other exceptions to AetherPostError
            logger = logging.getLogger(__name__)
            logger.exception(f"Unhandled exception in {func.__name__}")
            
            raise AetherPostError(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                error_code=ErrorCode.SYSTEM_ERROR,
                details={"function": func.__name__, "original_error": str(e)},
                recoverable=False
            )
    
    return wrapper


# Add missing error code
ErrorCode.SYSTEM_ERROR = 1399