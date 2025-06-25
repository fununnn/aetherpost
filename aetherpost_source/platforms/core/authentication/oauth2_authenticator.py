"""OAuth2 authentication implementation."""

import asyncio
import aiohttp
import logging
import urllib.parse
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .base_authenticator import BaseAuthenticator, AuthenticationResult, AuthSession
from ..error_handling.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class OAuth2Authenticator(BaseAuthenticator):
    """OAuth2 authentication implementation."""
    
    def __init__(
        self,
        credentials: Dict[str, str],
        platform: str,
        base_url: str,
        auth_config: Dict[str, Any],
        session_storage: Optional[Any] = None
    ):
        super().__init__(credentials, platform, base_url, session_storage)
        self.auth_config = auth_config
        
        # OAuth2 endpoints
        self.authorization_endpoint = auth_config.get('authorization_endpoint')
        self.token_endpoint = auth_config.get('token_endpoint')
        self.refresh_endpoint = auth_config.get('refresh_endpoint', self.token_endpoint)
        self.revoke_endpoint = auth_config.get('revoke_endpoint')
        
        # OAuth2 configuration
        self.scopes = auth_config.get('scopes', [])
        self.redirect_uri = auth_config.get('redirect_uri', 'urn:ietf:wg:oauth:2.0:oob')
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
    
    @property
    def auth_type(self) -> str:
        return "oauth2"
    
    @property
    def required_credentials(self) -> List[str]:
        return ['client_id', 'client_secret']
    
    async def _perform_authentication(self) -> AuthenticationResult:
        """Perform OAuth2 authentication."""
        
        # Check if we have an authorization code
        auth_code = self.credentials.get('authorization_code')
        if auth_code:
            return await self._exchange_code_for_token(auth_code)
        
        # Check if we have existing tokens
        access_token = self.credentials.get('access_token')
        refresh_token = self.credentials.get('refresh_token')
        
        if access_token:
            # Create session from existing tokens
            session = AuthSession(
                platform=self.platform,
                auth_type=self.auth_type,
                access_token=access_token,
                refresh_token=refresh_token,
                scopes=self.scopes
            )
            
            # Verify token is still valid
            if await self._verify_token(session):
                return AuthenticationResult(success=True, session=session)
        
        # No valid tokens, need user authorization
        auth_url = self._get_authorization_url()
        return AuthenticationResult(
            success=False,
            error_message="User authorization required",
            error_code="authorization_required",
            requires_user_action=True,
            user_action_url=auth_url
        )
    
    def _get_authorization_url(self) -> str:
        """Generate OAuth2 authorization URL."""
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes) if self.scopes else '',
            'state': f"{self.platform}_{datetime.utcnow().timestamp()}"
        }
        
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.authorization_endpoint}?{query_string}"
    
    async def _exchange_code_for_token(self, authorization_code: str) -> AuthenticationResult:
        """Exchange authorization code for access token."""
        
        try:
            token_data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'redirect_uri': self.redirect_uri
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.token_endpoint,
                    data=token_data,
                    headers={'Accept': 'application/json'}
                ) as response:
                    
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return self._create_session_from_token_response(response_data)
                    else:
                        error_msg = response_data.get('error_description', 
                                                     response_data.get('error', 'Token exchange failed'))
                        return AuthenticationResult(
                            success=False,
                            error_message=error_msg,
                            error_code=response_data.get('error', 'token_exchange_failed')
                        )
                        
        except Exception as e:
            logger.error(f"OAuth2 token exchange failed for {self.platform}: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"Token exchange failed: {str(e)}",
                error_code="token_exchange_exception"
            )
    
    async def _refresh_session(self, session: AuthSession) -> AuthenticationResult:
        """Refresh OAuth2 access token."""
        
        if not session.refresh_token:
            return AuthenticationResult(
                success=False,
                error_message="No refresh token available",
                error_code="no_refresh_token"
            )
        
        try:
            refresh_data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': session.refresh_token
            }
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    self.refresh_endpoint,
                    data=refresh_data,
                    headers={'Accept': 'application/json'}
                ) as response:
                    
                    response_data = await response.json()
                    
                    if response.status == 200:
                        # Update existing session with new tokens
                        new_session = self._create_session_from_token_response(
                            response_data, 
                            existing_session=session
                        )
                        
                        logger.info(f"Successfully refreshed OAuth2 token for {self.platform}")
                        return new_session
                    else:
                        error_msg = response_data.get('error_description',
                                                     response_data.get('error', 'Token refresh failed'))
                        return AuthenticationResult(
                            success=False,
                            error_message=error_msg,
                            error_code=response_data.get('error', 'token_refresh_failed')
                        )
                        
        except Exception as e:
            logger.error(f"OAuth2 token refresh failed for {self.platform}: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"Token refresh failed: {str(e)}",
                error_code="token_refresh_exception"
            )
    
    def _create_session_from_token_response(
        self, 
        token_data: Dict[str, Any],
        existing_session: Optional[AuthSession] = None
    ) -> AuthenticationResult:
        """Create authentication session from token response."""
        
        access_token = token_data.get('access_token')
        if not access_token:
            return AuthenticationResult(
                success=False,
                error_message="No access token in response",
                error_code="missing_access_token"
            )
        
        # Calculate expiration time
        expires_in = token_data.get('expires_in')
        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
        
        # Get scopes (use existing if not provided in response)
        response_scopes = token_data.get('scope', '').split() if token_data.get('scope') else []
        scopes = response_scopes or (existing_session.scopes if existing_session else self.scopes)
        
        session = AuthSession(
            platform=self.platform,
            auth_type=self.auth_type,
            access_token=access_token,
            refresh_token=token_data.get('refresh_token', 
                                        existing_session.refresh_token if existing_session else None),
            token_type=token_data.get('token_type', 'Bearer'),
            expires_at=expires_at,
            scopes=scopes,
            user_info=existing_session.user_info if existing_session else {},
            extra_data={
                'raw_token_response': token_data,
                **(existing_session.extra_data if existing_session else {})
            }
        )
        
        return AuthenticationResult(success=True, session=session)
    
    async def _verify_token(self, session: AuthSession) -> bool:
        """Verify that the access token is still valid."""
        
        # If we have an introspection endpoint, use it
        introspect_endpoint = self.auth_config.get('introspect_endpoint')
        if introspect_endpoint:
            return await self._introspect_token(session, introspect_endpoint)
        
        # Otherwise, try a simple API call to verify
        verify_endpoint = self.auth_config.get('verify_endpoint')
        if verify_endpoint:
            return await self._verify_with_api_call(session, verify_endpoint)
        
        # If no verification method available, assume valid if not expired
        return not session.is_expired
    
    async def _introspect_token(self, session: AuthSession, introspect_endpoint: str) -> bool:
        """Use OAuth2 token introspection to verify token."""
        
        try:
            introspect_data = {
                'token': session.access_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    introspect_endpoint,
                    data=introspect_data
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data.get('active', False)
                    
                    return False
                    
        except Exception as e:
            logger.warning(f"Token introspection failed for {self.platform}: {e}")
            return False
    
    async def _verify_with_api_call(self, session: AuthSession, verify_endpoint: str) -> bool:
        """Verify token by making a test API call."""
        
        try:
            headers = self.get_auth_headers(session)
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(
                    verify_endpoint,
                    headers=headers
                ) as response:
                    
                    return response.status == 200
                    
        except Exception as e:
            logger.warning(f"Token verification failed for {self.platform}: {e}")
            return False
    
    async def _revoke_session_on_platform(self, session: AuthSession) -> bool:
        """Revoke OAuth2 tokens on the platform."""
        
        if not self.revoke_endpoint:
            return True  # No revocation endpoint, assume successful
        
        try:
            revoke_data = {
                'token': session.access_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    self.revoke_endpoint,
                    data=revoke_data
                ) as response:
                    
                    # Revocation typically returns 200 or 204
                    return response.status in [200, 204]
                    
        except Exception as e:
            logger.warning(f"Token revocation failed for {self.platform}: {e}")
            return False
    
    def get_authorization_flow_status(self) -> Dict[str, Any]:
        """Get current status of OAuth2 authorization flow."""
        
        has_client_credentials = bool(self.client_id and self.client_secret)
        has_auth_code = bool(self.credentials.get('authorization_code'))
        has_tokens = bool(self.credentials.get('access_token'))
        
        return {
            'platform': self.platform,
            'auth_type': self.auth_type,
            'has_client_credentials': has_client_credentials,
            'has_authorization_code': has_auth_code,
            'has_access_token': has_tokens,
            'authorization_url': self._get_authorization_url() if has_client_credentials else None,
            'scopes': self.scopes,
            'redirect_uri': self.redirect_uri
        }