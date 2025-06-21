"""Security audit logging for AetherPost."""

import json
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_type: str
    timestamp: str
    user_id: Optional[str]
    source_ip: Optional[str]
    user_agent: Optional[str]
    resource: Optional[str]
    action: str
    result: str  # success, failure, blocked
    details: Dict[str, Any]
    risk_level: str  # low, medium, high, critical


class SecurityAuditLogger:
    """Security audit logger with structured logging."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.session_id = self._generate_session_id()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup security audit logger."""
        logger = logging.getLogger('aetherpost.security.audit')
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create logs directory
        log_dir = Path.home() / '.aetherpost' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler for audit log
        audit_file = log_dir / 'audit.log'
        file_handler = logging.FileHandler(audit_file)
        file_handler.setLevel(logging.INFO)
        
        # JSON formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        # Set secure file permissions
        audit_file.chmod(0o600)
        
        return logger
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import time
        import os
        session_data = f"{time.time()}-{os.getpid()}"
        return hashlib.sha256(session_data.encode()).hexdigest()[:16]
    
    def _get_current_user(self) -> str:
        """Get current user identifier (anonymized)."""
        import os
        try:
            # Create anonymized user ID
            username = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
            user_hash = hashlib.sha256(username.encode()).hexdigest()[:12]
            return f"user_{user_hash}"
        except Exception:
            return "user_unknown"
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize details to remove sensitive information."""
        sanitized = {}
        
        for key, value in details.items():
            key_lower = key.lower()
            
            # Mask sensitive keys
            if any(sensitive in key_lower for sensitive in [
                'password', 'secret', 'token', 'key', 'auth', 'credential'
            ]):
                sanitized[key] = self._mask_value(str(value))
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, str) and len(value) > 100:
                # Truncate long strings
                sanitized[key] = value[:100] + "... (truncated)"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _mask_value(self, value: str) -> str:
        """Mask sensitive values."""
        if len(value) <= 4:
            return "*" * len(value)
        else:
            return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
    
    def log_authentication_attempt(self, 
                                 platform: str, 
                                 success: bool, 
                                 details: Optional[Dict[str, Any]] = None):
        """Log authentication attempt."""
        event = SecurityEvent(
            event_type="authentication",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=self._get_current_user(),
            source_ip=None,  # CLI application
            user_agent=f"AetherPost-CLI/{self.session_id}",
            resource=platform,
            action="authenticate",
            result="success" if success else "failure",
            details=self._sanitize_details(details or {}),
            risk_level="medium" if not success else "low"
        )
        
        self.logger.info(json.dumps(asdict(event)))
    
    def log_api_request(self, 
                       provider: str, 
                       operation: str, 
                       success: bool,
                       details: Optional[Dict[str, Any]] = None):
        """Log API request."""
        event = SecurityEvent(
            event_type="api_request",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=self._get_current_user(),
            source_ip=None,
            user_agent=f"AetherPost-CLI/{self.session_id}",
            resource=f"{provider}/{operation}",
            action="api_call",
            result="success" if success else "failure",
            details=self._sanitize_details(details or {}),
            risk_level="low" if success else "medium"
        )
        
        self.logger.info(json.dumps(asdict(event)))
    
    def log_file_access(self, 
                       file_path: str, 
                       operation: str, 
                       success: bool,
                       details: Optional[Dict[str, Any]] = None):
        """Log file access attempt."""
        # Anonymize file path
        anonymized_path = self._anonymize_path(file_path)
        
        event = SecurityEvent(
            event_type="file_access",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=self._get_current_user(),
            source_ip=None,
            user_agent=f"AetherPost-CLI/{self.session_id}",
            resource=anonymized_path,
            action=operation,
            result="success" if success else "failure",
            details=self._sanitize_details(details or {}),
            risk_level="medium" if not success else "low"
        )
        
        self.logger.info(json.dumps(asdict(event)))
    
    def log_security_violation(self, 
                             violation_type: str, 
                             details: Dict[str, Any]):
        """Log security violation."""
        event = SecurityEvent(
            event_type="security_violation",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=self._get_current_user(),
            source_ip=None,
            user_agent=f"AetherPost-CLI/{self.session_id}",
            resource=violation_type,
            action="blocked",
            result="blocked",
            details=self._sanitize_details(details),
            risk_level="high"
        )
        
        self.logger.warning(json.dumps(asdict(event)))
    
    def log_configuration_change(self, 
                                setting: str, 
                                old_value: Any, 
                                new_value: Any):
        """Log configuration changes."""
        details = {
            "setting": setting,
            "old_value": self._mask_value(str(old_value)) if 'secret' in setting.lower() else str(old_value),
            "new_value": self._mask_value(str(new_value)) if 'secret' in setting.lower() else str(new_value)
        }
        
        event = SecurityEvent(
            event_type="configuration_change",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=self._get_current_user(),
            source_ip=None,
            user_agent=f"AetherPost-CLI/{self.session_id}",
            resource="configuration",
            action="modify",
            result="success",
            details=details,
            risk_level="medium"
        )
        
        self.logger.info(json.dumps(asdict(event)))
    
    def _anonymize_path(self, file_path: str) -> str:
        """Anonymize file path for logging."""
        path = Path(file_path)
        
        # Replace home directory with placeholder
        try:
            relative_to_home = path.relative_to(Path.home())
            return f"~/{relative_to_home}"
        except ValueError:
            # Not under home directory, just return filename
            return path.name


# Global audit logger instance
audit_logger = SecurityAuditLogger()


def log_authentication_attempt(platform: str, success: bool, details: Optional[Dict[str, Any]] = None):
    """Log authentication attempt."""
    audit_logger.log_authentication_attempt(platform, success, details)


def log_api_request(provider: str, operation: str, success: bool, details: Optional[Dict[str, Any]] = None):
    """Log API request."""
    audit_logger.log_api_request(provider, operation, success, details)


def log_file_access(file_path: str, operation: str, success: bool, details: Optional[Dict[str, Any]] = None):
    """Log file access."""
    audit_logger.log_file_access(file_path, operation, success, details)


def log_security_violation(violation_type: str, details: Dict[str, Any]):
    """Log security violation."""
    audit_logger.log_security_violation(violation_type, details)


def log_configuration_change(setting: str, old_value: Any, new_value: Any):
    """Log configuration change."""
    audit_logger.log_configuration_change(setting, old_value, new_value)