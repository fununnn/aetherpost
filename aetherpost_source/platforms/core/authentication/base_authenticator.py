"""Base authentication system for all platforms."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class AuthSession:
    """Authentication session data."""
    
    platform: str
    auth_type: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    scopes: List[str] = field(default_factory=list)
    user_info: Dict[str, Any] = field(default_factory=dict)
    extra_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at
    
    @property
    def expires_in_seconds(self) -> Optional[int]:
        """Get seconds until expiration."""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'platform': self.platform,
            'auth_type': self.auth_type,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'scopes': self.scopes,
            'user_info': self.user_info,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthSession':
        """Create session from dictionary."""
        session = cls(
            platform=data['platform'],
            auth_type=data['auth_type'],
            access_token=data.get('access_token'),
            refresh_token=data.get('refresh_token'),
            token_type=data.get('token_type', 'Bearer'),
            scopes=data.get('scopes', []),
            user_info=data.get('user_info', {}),
            extra_data=data.get('extra_data', {})
        )
        
        if data.get('expires_at'):
            session.expires_at = datetime.fromisoformat(data['expires_at'])
        if data.get('created_at'):
            session.created_at = datetime.fromisoformat(data['created_at'])
            
        return session


@dataclass
class AuthenticationResult:
    """Result of authentication attempt."""
    
    success: bool
    session: Optional[AuthSession] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    requires_user_action: bool = False
    user_action_url: Optional[str] = None
    retry_after: Optional[int] = None
    
    @property
    def is_retryable(self) -> bool:
        """Check if authentication can be retried."""
        return not self.success and not self.requires_user_action


class BaseAuthenticator(ABC):
    """Base class for all authentication implementations."""
    
    def __init__(
        self,
        credentials: Dict[str, str],
        platform: str,
        base_url: str,
        session_storage: Optional[Any] = None
    ):
        self.credentials = credentials
        self.platform = platform
        self.base_url = base_url
        self.session_storage = session_storage
        self._current_session: Optional[AuthSession] = None
        self._authenticating = False
    
    @property
    @abstractmethod
    def auth_type(self) -> str:
        """Authentication type identifier."""
        pass
    
    @property
    @abstractmethod
    def required_credentials(self) -> List[str]:
        """List of required credential keys."""
        pass
    
    async def authenticate(self) -> AuthenticationResult:
        """Authenticate and return session."""
        
        # Prevent concurrent authentication attempts
        if self._authenticating:
            # Wait for current authentication to complete
            while self._authenticating:
                await asyncio.sleep(0.1)
            
            if self._current_session and not self._current_session.is_expired:
                return AuthenticationResult(success=True, session=self._current_session)
        
        self._authenticating = True
        
        try:
            # Check if we have a valid cached session
            if self._current_session and not self._current_session.is_expired:
                return AuthenticationResult(success=True, session=self._current_session)
            
            # Try to refresh if we have a refresh token
            if (self._current_session and 
                self._current_session.refresh_token and 
                self._current_session.is_expired):
                
                refresh_result = await self._refresh_session(self._current_session)
                if refresh_result.success:
                    self._current_session = refresh_result.session
                    await self._save_session(self._current_session)
                    return refresh_result
            
            # Validate credentials
            validation_result = self._validate_credentials()
            if not validation_result.success:
                return validation_result
            
            # Perform new authentication
            auth_result = await self._perform_authentication()
            
            if auth_result.success and auth_result.session:
                self._current_session = auth_result.session
                await self._save_session(self._current_session)
                
                logger.info(f"Successfully authenticated {self.platform} using {self.auth_type}")
            else:
                logger.error(
                    f"Authentication failed for {self.platform}: {auth_result.error_message}"
                )
            
            return auth_result
            
        except Exception as e:
            logger.error(f"Authentication error for {self.platform}: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"Authentication failed: {str(e)}",
                error_code="auth_exception"
            )
        finally:
            self._authenticating = False
    
    @abstractmethod
    async def _perform_authentication(self) -> AuthenticationResult:
        """Perform platform-specific authentication."""
        pass
    
    async def _refresh_session(self, session: AuthSession) -> AuthenticationResult:
        """Refresh an expired session if possible."""
        # Default implementation - subclasses should override if they support refresh
        return AuthenticationResult(
            success=False,
            error_message="Session refresh not supported",
            error_code="refresh_not_supported"
        )
    
    def _validate_credentials(self) -> AuthenticationResult:
        """Validate that all required credentials are present."""
        
        missing_creds = []
        for cred in self.required_credentials:
            if not self.credentials.get(cred):
                missing_creds.append(cred)
        
        if missing_creds:
            return AuthenticationResult(
                success=False,
                error_message=f"Missing required credentials: {', '.join(missing_creds)}",
                error_code="missing_credentials"
            )
        
        return AuthenticationResult(success=True)
    
    def get_auth_headers(self, session: Optional[AuthSession] = None) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        
        session = session or self._current_session
        if not session:
            return {}
        
        if session.access_token:
            return {
                'Authorization': f'{session.token_type} {session.access_token}'
            }
        
        return {}
    
    async def is_session_valid(self, session: Optional[AuthSession] = None) -> bool:
        """Check if current or provided session is valid."""
        
        session = session or self._current_session
        if not session:
            return False
        
        if session.is_expired:
            # Try to refresh if possible
            if session.refresh_token:
                refresh_result = await self._refresh_session(session)
                if refresh_result.success:
                    self._current_session = refresh_result.session
                    return True
            return False
        
        return True
    
    async def revoke_session(self) -> bool:
        """Revoke current authentication session."""
        
        if not self._current_session:
            return True
        
        try:
            # Perform platform-specific revocation if implemented
            revoke_result = await self._revoke_session_on_platform(self._current_session)
            
            # Clear local session regardless of platform response
            self._current_session = None
            if self.session_storage:
                await self._clear_saved_session()
            
            return revoke_result
            
        except Exception as e:
            logger.error(f"Error revoking session for {self.platform}: {e}")
            return False
    
    async def _revoke_session_on_platform(self, session: AuthSession) -> bool:
        """Revoke session on the platform (override in subclasses if supported)."""
        return True  # Default: assume successful revocation
    
    async def _save_session(self, session: AuthSession):
        """Save session to storage if available."""
        if self.session_storage:
            try:
                await self.session_storage.save_session(self.platform, session.to_dict())
            except Exception as e:
                logger.warning(f"Failed to save session for {self.platform}: {e}")
    
    async def _load_session(self) -> Optional[AuthSession]:
        """Load session from storage if available."""
        if self.session_storage:
            try:
                session_data = await self.session_storage.load_session(self.platform)
                if session_data:
                    return AuthSession.from_dict(session_data)
            except Exception as e:
                logger.warning(f"Failed to load session for {self.platform}: {e}")
        return None
    
    async def _clear_saved_session(self):
        """Clear saved session from storage."""
        if self.session_storage:
            try:
                await self.session_storage.clear_session(self.platform)
            except Exception as e:
                logger.warning(f"Failed to clear session for {self.platform}: {e}")
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current session information for debugging."""
        if not self._current_session:
            return None
        
        return {
            'platform': self._current_session.platform,
            'auth_type': self._current_session.auth_type,
            'has_access_token': bool(self._current_session.access_token),
            'has_refresh_token': bool(self._current_session.refresh_token),
            'expires_at': self._current_session.expires_at.isoformat() if self._current_session.expires_at else None,
            'is_expired': self._current_session.is_expired,
            'expires_in_seconds': self._current_session.expires_in_seconds,
            'scopes': self._current_session.scopes,
            'user_info': self._current_session.user_info
        }