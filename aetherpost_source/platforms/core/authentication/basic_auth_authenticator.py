"""HTTP Basic Authentication implementation."""

import aiohttp
import logging
import base64
from typing import Dict, Any, Optional, List

from .base_authenticator import BaseAuthenticator, AuthenticationResult, AuthSession

logger = logging.getLogger(__name__)


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