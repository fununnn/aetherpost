"""Unified platform exception hierarchy."""

from typing import Dict, Any, Optional, List
from datetime import datetime


class PlatformError(Exception):
    """Base exception for all platform-related errors."""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.platform = platform
        self.error_code = error_code
        self.details = details or {}
        self.original_error = original_error
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'platform': self.platform,
            'error_code': self.error_code,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'original_error': str(self.original_error) if self.original_error else None
        }


class AuthenticationError(PlatformError):
    """Authentication and authorization related errors."""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        auth_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, platform, **kwargs)
        self.auth_type = auth_type


class PostingError(PlatformError):
    """Content posting and publishing related errors."""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        content_type: Optional[str] = None,
        post_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, platform, **kwargs)
        self.content_type = content_type
        self.post_id = post_id


class RateLimitError(PlatformError):
    """Rate limiting and API quota related errors."""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, platform, **kwargs)
        self.retry_after = retry_after
        self.limit_type = limit_type


class ContentValidationError(PlatformError):
    """Content validation and format related errors."""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
        content_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, platform, **kwargs)
        self.validation_errors = validation_errors or []
        self.content_type = content_type


class NetworkError(PlatformError):
    """Network connectivity and API communication errors."""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, platform, **kwargs)
        self.status_code = status_code
        self.endpoint = endpoint


class ConfigurationError(PlatformError):
    """Platform configuration and setup related errors."""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        config_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, platform, **kwargs)
        self.config_key = config_key


class MediaUploadError(PlatformError):
    """Media file upload and processing related errors."""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, platform, **kwargs)
        self.file_path = file_path
        self.file_type = file_type
        self.file_size = file_size


class ProfileUpdateError(PlatformError):
    """Profile management and update related errors."""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        field_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, platform, **kwargs)
        self.field_name = field_name


class AnalyticsError(PlatformError):
    """Analytics and metrics collection related errors."""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        metric_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, platform, **kwargs)
        self.metric_type = metric_type