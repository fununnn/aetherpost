"""JWT (JSON Web Token) authentication implementation."""

import asyncio
import aiohttp
import logging
import json
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .base_authenticator import BaseAuthenticator, AuthenticationResult, AuthSession

logger = logging.getLogger(__name__)


class JWTAuthenticator(BaseAuthenticator):
    """JWT authentication implementation."""
    
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
        
        # JWT configuration
        self.login_endpoint = auth_config.get('login_endpoint', '/auth/login')
        self.refresh_endpoint = auth_config.get('refresh_endpoint', '/auth/refresh')
        self.verify_endpoint = auth_config.get('verify_endpoint', '/auth/verify')
        
        # Credentials
        self.username = credentials.get('username')
        self.password = credentials.get('password')
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
    
    @property
    def auth_type(self) -> str:
        return "jwt"
    
    @property
    def required_credentials(self) -> List[str]:
        return ['username', 'password']
    
    async def _perform_authentication(self) -> AuthenticationResult:
        """Perform JWT authentication."""
        
        try:
            login_data = {
                'username': self.username,
                'password': self.password
            }
            
            # Add client credentials if provided
            if self.client_id:
                login_data['client_id'] = self.client_id
            if self.client_secret:
                login_data['client_secret'] = self.client_secret
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}{self.login_endpoint}",
                    json=login_data,
                    headers={'Accept': 'application/json'}
                ) as response:
                    
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return self._create_session_from_jwt_response(response_data)
                    else:
                        error_msg = response_data.get('message', 
                                                     response_data.get('error', 'JWT authentication failed'))
                        return AuthenticationResult(
                            success=False,
                            error_message=error_msg,
                            error_code=response_data.get('code', 'jwt_auth_failed')
                        )
                        
        except Exception as e:
            logger.error(f"JWT authentication failed for {self.platform}: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"JWT authentication failed: {str(e)}",
                error_code="jwt_auth_exception"
            )
    
    def _create_session_from_jwt_response(self, response_data: Dict[str, Any]) -> AuthenticationResult:
        """Create session from JWT authentication response."""
        
        access_token = response_data.get('access_token') or response_data.get('token')
        if not access_token:
            return AuthenticationResult(
                success=False,
                error_message="No access token in JWT response",
                error_code="missing_jwt_token"
            )
        
        # Parse JWT to extract expiration
        expires_at = None
        try:
            jwt_payload = self._decode_jwt_payload(access_token)
            if jwt_payload and 'exp' in jwt_payload:
                expires_at = datetime.fromtimestamp(jwt_payload['exp'])
        except Exception as e:
            logger.warning(f"Failed to parse JWT expiration: {e}")
        
        # If no expiration in JWT, use response data
        if not expires_at and 'expires_in' in response_data:
            expires_in = int(response_data['expires_in'])
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        session = AuthSession(
            platform=self.platform,
            auth_type=self.auth_type,
            access_token=access_token,
            refresh_token=response_data.get('refresh_token'),
            token_type=response_data.get('token_type', 'Bearer'),
            expires_at=expires_at,
            user_info=response_data.get('user', {}),
            extra_data={
                'jwt_payload': self._decode_jwt_payload(access_token),
                'raw_response': response_data
            }
        )
        
        return AuthenticationResult(success=True, session=session)
    
    def _decode_jwt_payload(self, jwt_token: str) -> Optional[Dict[str, Any]]:
        """Decode JWT payload (without verification for info extraction)."""
        
        try:
            # JWT has 3 parts: header.payload.signature
            parts = jwt_token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload (second part)
            payload_b64 = parts[1]
            
            # Add padding if needed for base64 decoding
            padding = len(payload_b64) % 4
            if padding:
                payload_b64 += '=' * (4 - padding)
            
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes.decode('utf-8'))
            
            return payload
            
        except Exception as e:
            logger.warning(f"Failed to decode JWT payload: {e}")
            return None
    
    async def _refresh_session(self, session: AuthSession) -> AuthenticationResult:
        """Refresh JWT token using refresh token."""
        
        if not session.refresh_token:
            return AuthenticationResult(
                success=False,
                error_message="No refresh token available for JWT refresh",
                error_code="no_jwt_refresh_token"
            )
        
        try:
            refresh_data = {
                'refresh_token': session.refresh_token
            }
            
            # Add client credentials if configured
            if self.client_id:
                refresh_data['client_id'] = self.client_id
            if self.client_secret:
                refresh_data['client_secret'] = self.client_secret
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    f"{self.base_url}{self.refresh_endpoint}",
                    json=refresh_data,
                    headers={'Accept': 'application/json'}
                ) as response:
                    
                    response_data = await response.json()
                    
                    if response.status == 200:
                        logger.info(f"Successfully refreshed JWT token for {self.platform}")
                        return self._create_session_from_jwt_response(response_data)
                    else:
                        error_msg = response_data.get('message',
                                                     response_data.get('error', 'JWT token refresh failed'))
                        return AuthenticationResult(
                            success=False,
                            error_message=error_msg,
                            error_code=response_data.get('code', 'jwt_refresh_failed')
                        )
                        
        except Exception as e:
            logger.error(f"JWT token refresh failed for {self.platform}: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"JWT token refresh failed: {str(e)}",
                error_code="jwt_refresh_exception"
            )
    
    async def _verify_token(self, session: AuthSession) -> bool:
        """Verify JWT token is still valid."""
        
        try:
            headers = self.get_auth_headers(session)
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(
                    f"{self.base_url}{self.verify_endpoint}",
                    headers=headers
                ) as response:
                    
                    return response.status == 200
                    
        except Exception as e:
            logger.warning(f"JWT token verification failed for {self.platform}: {e}")
            return False
    
    def is_jwt_expired(self, jwt_token: str) -> bool:
        """Check if JWT token is expired based on 'exp' claim."""
        
        payload = self._decode_jwt_payload(jwt_token)
        if not payload or 'exp' not in payload:
            return False  # Cannot determine, assume valid
        
        exp_timestamp = payload['exp']
        return datetime.utcnow().timestamp() >= exp_timestamp
    
    def get_jwt_claims(self, session: Optional[AuthSession] = None) -> Optional[Dict[str, Any]]:
        """Get JWT claims from current session."""
        
        session = session or self._current_session
        if not session or not session.access_token:
            return None
        
        return session.extra_data.get('jwt_payload')


class BasicAuthAuthenticator(BaseAuthenticator):
    """HTTP Basic Authentication implementation."""
    
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
        
        self.username = credentials.get('username')
        self.password = credentials.get('password')
        self.verify_endpoint = self.auth_config.get('verify_endpoint')
    
    @property
    def auth_type(self) -> str:
        return "basic_auth"
    
    @property
    def required_credentials(self) -> List[str]:
        return ['username', 'password']
    
    async def _perform_authentication(self) -> AuthenticationResult:
        """Perform Basic Authentication."""
        
        try:
            # Create Basic Auth credentials
            credentials_str = f"{self.username}:{self.password}"
            credentials_b64 = base64.b64encode(credentials_str.encode()).decode()
            
            session = AuthSession(
                platform=self.platform,
                auth_type=self.auth_type,
                access_token=credentials_b64,
                token_type="Basic",
                user_info={'username': self.username}
            )
            
            # Verify credentials if endpoint provided
            if self.verify_endpoint:
                is_valid = await self._verify_basic_auth(session)
                if not is_valid:
                    return AuthenticationResult(
                        success=False,
                        error_message="Basic authentication verification failed",
                        error_code="invalid_basic_auth"
                    )
            
            logger.info(f"Successfully authenticated {self.platform} using Basic Auth")
            return AuthenticationResult(success=True, session=session)
            
        except Exception as e:
            logger.error(f"Basic authentication failed for {self.platform}: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"Basic authentication failed: {str(e)}",
                error_code="basic_auth_exception"
            )
    
    async def _verify_basic_auth(self, session: AuthSession) -> bool:
        """Verify Basic Auth credentials."""
        
        try:
            headers = self.get_auth_headers(session)
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(
                    f"{self.base_url}{self.verify_endpoint}",
                    headers=headers
                ) as response:
                    
                    return response.status == 200
                    
        except Exception as e:
            logger.warning(f"Basic auth verification failed for {self.platform}: {e}")
            return False