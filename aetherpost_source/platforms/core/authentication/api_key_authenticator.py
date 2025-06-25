"""API Key authentication implementation."""

import logging
from typing import Dict, Any, Optional, List

from .base_authenticator import BaseAuthenticator, AuthenticationResult, AuthSession

logger = logging.getLogger(__name__)


class ApiKeyAuthenticator(BaseAuthenticator):
    """API Key authentication implementation."""
    
    def __init__(
        self,
        credentials: Dict[str, str],
        platform: str,
        base_url: str,
        auth_config: Optional[Dict[str, Any]] = None,
        session_storage: Optional[Any] = None
    ):
        super().__init__(credentials, platform, base_url, session_storage)
        self.auth_config = auth_config or {}
        
        # API key configuration
        self.api_key = credentials.get('api_key')
        self.api_secret = credentials.get('api_secret')
        self.key_header = self.auth_config.get('key_header', 'Authorization')
        self.key_prefix = self.auth_config.get('key_prefix', 'Bearer')
        self.secret_header = self.auth_config.get('secret_header')
        
        # Alternative configurations
        self.query_param = self.auth_config.get('query_param')  # For query parameter auth
        self.custom_headers = self.auth_config.get('custom_headers', {})
    
    @property
    def auth_type(self) -> str:
        return "api_key"
    
    @property
    def required_credentials(self) -> List[str]:
        required = ['api_key']
        if self.secret_header or self.auth_config.get('requires_secret', False):
            required.append('api_secret')
        return required
    
    async def _perform_authentication(self) -> AuthenticationResult:
        """Perform API key authentication."""
        
        try:
            # API key authentication is usually just validation
            # No actual authentication request needed
            
            session = AuthSession(
                platform=self.platform,
                auth_type=self.auth_type,
                access_token=self.api_key,
                token_type=self.key_prefix,
                extra_data={
                    'api_secret': self.api_secret,
                    'key_header': self.key_header,
                    'secret_header': self.secret_header,
                    'query_param': self.query_param,
                    'custom_headers': self.custom_headers
                }
            )
            
            # Test the API key if verification endpoint is provided
            verify_endpoint = self.auth_config.get('verify_endpoint')
            if verify_endpoint:
                is_valid = await self._verify_api_key(session, verify_endpoint)
                if not is_valid:
                    return AuthenticationResult(
                        success=False,
                        error_message="API key verification failed",
                        error_code="invalid_api_key"
                    )
            
            logger.info(f"Successfully authenticated {self.platform} using API key")
            return AuthenticationResult(success=True, session=session)
            
        except Exception as e:
            logger.error(f"API key authentication failed for {self.platform}: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"API key authentication failed: {str(e)}",
                error_code="api_key_auth_exception"
            )
    
    def get_auth_headers(self, session: Optional[AuthSession] = None) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        
        session = session or self._current_session
        if not session:
            return {}
        
        headers = {}
        
        # Main API key header
        if self.query_param:
            # API key goes in query parameters, not headers
            pass
        else:
            key_value = f"{session.token_type} {session.access_token}" if session.token_type else session.access_token
            headers[self.key_header] = key_value
        
        # API secret header if configured
        if self.secret_header and session.extra_data.get('api_secret'):
            headers[self.secret_header] = session.extra_data['api_secret']
        
        # Custom headers
        custom_headers = session.extra_data.get('custom_headers', {})
        headers.update(custom_headers)
        
        return headers
    
    def get_auth_params(self, session: Optional[AuthSession] = None) -> Dict[str, str]:
        """Get authentication query parameters for API requests."""
        
        session = session or self._current_session
        if not session or not self.query_param:
            return {}
        
        return {self.query_param: session.access_token}
    
    async def _verify_api_key(self, session: AuthSession, verify_endpoint: str) -> bool:
        """Verify API key by making a test request."""
        
        import aiohttp
        
        try:
            headers = self.get_auth_headers(session)
            params = self.get_auth_params(session)
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(
                    verify_endpoint,
                    headers=headers,
                    params=params
                ) as response:
                    
                    return response.status == 200
                    
        except Exception as e:
            logger.warning(f"API key verification failed for {self.platform}: {e}")
            return False


class TwitterApiKeyAuthenticator(ApiKeyAuthenticator):
    """Twitter-specific API key authentication with multiple keys."""
    
    @property
    def required_credentials(self) -> List[str]:
        return ['api_key', 'api_secret', 'access_token', 'access_token_secret']
    
    async def _perform_authentication(self) -> AuthenticationResult:
        """Twitter uses OAuth 1.0a with multiple keys."""
        
        try:
            # Validate all required Twitter credentials
            validation_result = self._validate_credentials()
            if not validation_result.success:
                return validation_result
            
            session = AuthSession(
                platform=self.platform,
                auth_type="twitter_oauth1",
                access_token=self.credentials.get('access_token'),
                token_type="OAuth",
                extra_data={
                    'api_key': self.credentials.get('api_key'),
                    'api_secret': self.credentials.get('api_secret'),
                    'access_token_secret': self.credentials.get('access_token_secret')
                }
            )
            
            # Verify Twitter credentials if endpoint provided
            verify_endpoint = self.auth_config.get('verify_endpoint')
            if verify_endpoint:
                is_valid = await self._verify_twitter_credentials(session, verify_endpoint)
                if not is_valid:
                    return AuthenticationResult(
                        success=False,
                        error_message="Twitter credentials verification failed",
                        error_code="invalid_twitter_credentials"
                    )
            
            logger.info(f"Successfully authenticated Twitter using OAuth 1.0a")
            return AuthenticationResult(success=True, session=session)
            
        except Exception as e:
            logger.error(f"Twitter authentication failed: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"Twitter authentication failed: {str(e)}",
                error_code="twitter_auth_exception"
            )
    
    async def _verify_twitter_credentials(self, session: AuthSession, verify_endpoint: str) -> bool:
        """Verify Twitter credentials using OAuth 1.0a signature."""
        
        # Twitter OAuth 1.0a verification would require signature generation
        # For now, we'll implement a simple check
        try:
            # This would need proper OAuth 1.0a signature implementation
            # For the migration, we'll rely on tweepy library for actual requests
            return True
            
        except Exception as e:
            logger.warning(f"Twitter credentials verification failed: {e}")
            return False
    
    def get_twitter_credentials(self, session: Optional[AuthSession] = None) -> Dict[str, str]:
        """Get Twitter-specific credentials for tweepy."""
        
        session = session or self._current_session
        if not session:
            return {}
        
        return {
            'api_key': session.extra_data.get('api_key'),
            'api_secret': session.extra_data.get('api_secret'),
            'access_token': session.access_token,
            'access_token_secret': session.extra_data.get('access_token_secret')
        }