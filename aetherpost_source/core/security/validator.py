"""Security validation utilities for AetherPost."""

import os
import socket
import ipaddress
import urllib.parse
from pathlib import Path
from typing import List, Set, Optional
from urllib.parse import urlparse


class SecurityValidator:
    """Security validation utilities."""
    
    def __init__(self):
        self.allowed_file_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
            '.mp4', '.mov', '.avi', '.mkv', '.webm',
            '.yaml', '.yml', '.json', '.txt', '.md'
        }
        
        self.blocked_schemes = {
            'file', 'ftp', 'gopher', 'ldap', 'ldaps',
            'dict', 'sftp', 'ssh', 'tftp'
        }
        
        self.private_ip_ranges = [
            ipaddress.IPv4Network('10.0.0.0/8'),
            ipaddress.IPv4Network('172.16.0.0/12'),
            ipaddress.IPv4Network('192.168.0.0/16'),
            ipaddress.IPv4Network('127.0.0.0/8'),
            ipaddress.IPv4Network('169.254.0.0/16'),
            ipaddress.IPv6Network('::1/128'),
            ipaddress.IPv6Network('fc00::/7'),
            ipaddress.IPv6Network('fe80::/10'),
        ]
    
    def validate_file_path(self, file_path: str, allowed_dirs: Optional[List[Path]] = None) -> bool:
        """
        Validate file path to prevent directory traversal attacks.
        
        Args:
            file_path: The file path to validate
            allowed_dirs: List of allowed parent directories
            
        Returns:
            bool: True if the path is safe, False otherwise
        """
        try:
            # Convert to Path object and resolve
            path = Path(file_path).resolve()
            
            # Check if file extension is allowed
            if path.suffix.lower() not in self.allowed_file_extensions:
                return False
            
            # Default allowed directories
            if allowed_dirs is None:
                allowed_dirs = [
                    Path.cwd(),
                    Path.home() / 'Downloads',
                    Path.home() / 'Documents',
                    Path('/tmp') if os.name != 'nt' else Path(os.environ.get('TEMP', ''))
                ]
            
            # Check if path is within allowed directories
            for allowed_dir in allowed_dirs:
                try:
                    if path.is_relative_to(allowed_dir.resolve()):
                        return True
                except (ValueError, OSError):
                    continue
            
            return False
            
        except (ValueError, OSError, RuntimeError):
            return False
    
    def validate_url(self, url: str, allow_private_ips: bool = False) -> bool:
        """
        Validate URL to prevent SSRF attacks.
        
        Args:
            url: The URL to validate
            allow_private_ips: Whether to allow private IP addresses
            
        Returns:
            bool: True if the URL is safe, False otherwise
        """
        try:
            parsed = urlparse(url)
            
            # Check protocol
            if parsed.scheme.lower() in self.blocked_schemes:
                return False
            
            if parsed.scheme.lower() not in ['http', 'https']:
                return False
            
            # Check hostname
            if not parsed.hostname:
                return False
            
            # Resolve hostname to IP
            try:
                ip_str = socket.gethostbyname(parsed.hostname)
                ip = ipaddress.ip_address(ip_str)
                
                # Check for private/loopback addresses
                if not allow_private_ips:
                    for private_range in self.private_ip_ranges:
                        if ip in private_range:
                            return False
                
            except (socket.gaierror, ValueError):
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                'localhost', '0.0.0.0', '[::]', 
                'metadata.google.internal',
                '169.254.169.254'  # AWS metadata service
            ]
            
            hostname_lower = parsed.hostname.lower()
            if any(pattern in hostname_lower for pattern in suspicious_patterns):
                return False
            
            return True
            
        except Exception:
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and special characters.
        
        Args:
            filename: The filename to sanitize
            
        Returns:
            str: Sanitized filename
        """
        # Remove path separators and other dangerous characters
        dangerous_chars = ['/', '\\', '..', '~', '$', '&', '|', ';', '`']
        
        sanitized = filename
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip(' .')
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = 'unnamed_file'
        
        return sanitized
    
    def validate_api_key(self, api_key: str, provider: str) -> bool:
        """
        Validate API key format for security.
        
        Args:
            api_key: The API key to validate
            provider: The provider name (openai, anthropic, etc.)
            
        Returns:
            bool: True if the API key format is valid
        """
        if not api_key or len(api_key) < 10:
            return False
        
        # Provider-specific validation
        provider_patterns = {
            'openai': lambda key: key.startswith('sk-') and len(key) > 40,
            'anthropic': lambda key: key.startswith('sk-ant-') and len(key) > 50,
            'twitter': lambda key: len(key) >= 25,  # Twitter API keys
        }
        
        validator = provider_patterns.get(provider.lower())
        if validator:
            return validator(api_key)
        
        # Generic validation for unknown providers
        return len(api_key) >= 20 and api_key.isalnum()
    
    def check_rate_limit_safety(self, requests_per_minute: int, requests_per_hour: int) -> bool:
        """
        Check if rate limits are within safe bounds.
        
        Args:
            requests_per_minute: Requests per minute
            requests_per_hour: Requests per hour
            
        Returns:
            bool: True if rates are safe
        """
        # Conservative limits to prevent abuse
        max_per_minute = 100
        max_per_hour = 1000
        
        return (requests_per_minute <= max_per_minute and 
                requests_per_hour <= max_per_hour)
    
    def is_safe_content(self, content: str) -> bool:
        """
        Check if content is safe for posting (basic checks).
        
        Args:
            content: Content to check
            
        Returns:
            bool: True if content appears safe
        """
        if not content or len(content) > 10000:  # Reasonable length limit
            return False
        
        # Check for potential injection patterns
        dangerous_patterns = [
            '<script', 'javascript:', 'data:text/html',
            'eval(', 'function(', 'alert(',
            'document.', 'window.', 'location.'
        ]
        
        content_lower = content.lower()
        return not any(pattern in content_lower for pattern in dangerous_patterns)


# Global validator instance
security_validator = SecurityValidator()


def validate_file_path(file_path: str, allowed_dirs: Optional[List[Path]] = None) -> bool:
    """Validate file path for security."""
    return security_validator.validate_file_path(file_path, allowed_dirs)


def validate_url(url: str, allow_private_ips: bool = False) -> bool:
    """Validate URL for security."""
    return security_validator.validate_url(url, allow_private_ips)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename."""
    return security_validator.sanitize_filename(filename)


def validate_api_key(api_key: str, provider: str) -> bool:
    """Validate API key format."""
    return security_validator.validate_api_key(api_key, provider)


def is_safe_content(content: str) -> bool:
    """Check if content is safe."""
    return security_validator.is_safe_content(content)