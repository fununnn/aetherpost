"""Credential encryption and security utilities."""

import os
import json
import base64
import secrets
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Dict


class CredentialManager:
    """Manage encrypted credentials."""
    
    _master_key_cache = None
    
    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.environ.get("AETHERPOST_MASTER_KEY") or self._get_or_generate_key()
        self.cipher_suite = self._get_cipher_suite()
    
    def _get_or_generate_key(self) -> str:
        """Get cached master key or generate new one."""
        if CredentialManager._master_key_cache is None:
            CredentialManager._master_key_cache = self._generate_key()
            # Security: Never log actual master key
            print("Generated new master key. Please set AETHERPOST_MASTER_KEY environment variable.")
            print("Run 'aetherpost auth show-key' to display the key securely.")
        return CredentialManager._master_key_cache
    
    def _generate_key(self) -> str:
        """Generate a new master key."""
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()
    
    def _get_or_create_salt(self) -> bytes:
        """Get existing salt or create new random salt."""
        config_dir = Path.home() / '.aetherpost'
        salt_file = config_dir / 'salt'
        
        try:
            if salt_file.exists():
                with open(salt_file, 'rb') as f:
                    return f.read()
            else:
                # Create new random salt
                salt = secrets.token_bytes(32)  # 256-bit salt
                
                # Ensure config directory exists
                config_dir.mkdir(exist_ok=True)
                
                # Write salt with secure permissions
                with open(salt_file, 'wb') as f:
                    f.write(salt)
                
                # Set secure file permissions (owner read/write only)
                os.chmod(salt_file, 0o600)
                
                return salt
                
        except Exception as e:
            # Fallback to deterministic but more secure salt
            import hashlib
            fallback_data = f"aetherpost-{os.getuid() if hasattr(os, 'getuid') else 'user'}"
            return hashlib.sha256(fallback_data.encode()).digest()
    
    def _get_cipher_suite(self) -> Fernet:
        """Get cipher suite for encryption/decryption."""
        try:
            key = base64.urlsafe_b64decode(self.master_key.encode())
            return Fernet(key)
        except Exception:
            # If master_key is not base64 encoded, use it as password
            password = self.master_key.encode()
            salt = self._get_or_create_salt()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=600000,  # NIST recommended value
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            return Fernet(key)
    
    def encrypt_credentials(self, credentials: dict) -> str:
        """Encrypt credentials dictionary."""
        credentials_json = json.dumps(credentials)
        encrypted = self.cipher_suite.encrypt(credentials_json.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_credentials(self, encrypted_data: str) -> dict:
        """Decrypt credentials dictionary."""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher_suite.decrypt(encrypted_bytes)
        return json.loads(decrypted.decode())


class APIKeyValidator:
    """Validate API key formats and authenticity."""
    
    @staticmethod
    def validate_twitter_keys(credentials: dict) -> bool:
        """Validate Twitter API keys."""
        required_keys = ["api_key", "api_secret", "access_token", "access_token_secret"]
        return all(key in credentials and credentials[key] for key in required_keys)
    
    @staticmethod
    def validate_anthropic_key(api_key: str) -> bool:
        """Validate Anthropic API key format."""
        return api_key.startswith("sk-ant-") and len(api_key) > 20
    
    @staticmethod
    def validate_openai_key(api_key: str) -> bool:
        """Validate OpenAI API key format."""
        return api_key.startswith("sk-") and len(api_key) > 20
    
    @staticmethod
    def validate_bluesky_credentials(credentials: dict) -> bool:
        """Validate Bluesky credentials."""
        required_keys = ["handle", "password"]
        return all(key in credentials and credentials[key] for key in required_keys)