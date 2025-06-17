"""Unified configuration management system for AetherPost."""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Type
from dataclasses import dataclass, field, asdict
from pathlib import Path
from abc import ABC, abstractmethod
import yaml

from .base_models import Platform, OperationResult
from .utils import load_config_file, save_config_file, merge_dictionaries

logger = logging.getLogger(__name__)


@dataclass
class PlatformCredentials:
    """Platform-specific credentials."""
    platform: Platform
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    access_token_secret: Optional[str] = None
    webhook_url: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if credentials are valid."""
        if self.platform == Platform.TWITTER:
            return bool(self.api_key and self.api_secret and self.access_token and self.access_token_secret)
        elif self.platform == Platform.INSTAGRAM:
            return bool(self.access_token)
        elif self.platform == Platform.LINKEDIN:
            return bool(self.access_token)
        elif self.platform == Platform.SLACK:
            return bool(self.webhook_url or self.access_token)
        elif self.platform == Platform.DISCORD:
            return bool(self.webhook_url)
        else:
            return bool(self.api_key or self.access_token or self.webhook_url)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                if key == "platform":
                    result[key] = value.value if hasattr(value, 'value') else value
                else:
                    result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlatformCredentials':
        """Create from dictionary."""
        platform = Platform(data["platform"]) if isinstance(data["platform"], str) else data["platform"]
        return cls(
            platform=platform,
            api_key=data.get("api_key"),
            api_secret=data.get("api_secret"),
            access_token=data.get("access_token"),
            access_token_secret=data.get("access_token_secret"),
            webhook_url=data.get("webhook_url"),
            additional_params=data.get("additional_params", {})
        )


@dataclass
class AIProviderConfig:
    """AI provider configuration."""
    provider: str  # openai, claude, gemini, etc.
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    additional_params: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if AI config is valid."""
        return bool(self.provider and self.api_key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIProviderConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class NotificationConfig:
    """Notification system configuration."""
    enabled: bool = True
    channels: List[Dict[str, Any]] = field(default_factory=list)
    default_channels: List[str] = field(default_factory=list)
    quiet_hours: Dict[str, str] = field(default_factory=dict)  # start_time, end_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AetherPostConfig:
    """Main AetherPost configuration."""
    app_name: str = "AetherPost"
    description: str = "Social media automation for developers"
    author: str = "AetherPost Team"
    website_url: Optional[str] = None
    github_url: Optional[str] = None
    contact_email: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    
    # Platform configurations
    platforms: Dict[str, PlatformCredentials] = field(default_factory=dict)
    
    # AI configuration
    ai: Optional[AIProviderConfig] = None
    
    # Notification configuration
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "auto_posting": True,
        "content_review": True,
        "analytics": True,
        "notifications": True,
        "ai_generation": True
    })
    
    # Default settings
    defaults: Dict[str, Any] = field(default_factory=lambda: {
        "posting_style": "friendly",
        "auto_hashtags": True,
        "optimal_timing": True,
        "content_validation": True
    })
    
    def get_platform_credentials(self, platform: Union[str, Platform]) -> Optional[PlatformCredentials]:
        """Get credentials for platform."""
        platform_str = platform.value if isinstance(platform, Platform) else platform
        return self.platforms.get(platform_str)
    
    def set_platform_credentials(self, credentials: PlatformCredentials) -> None:
        """Set credentials for platform."""
        self.platforms[credentials.platform.value] = credentials
    
    def get_configured_platforms(self) -> List[str]:
        """Get list of configured platforms."""
        return [platform for platform, creds in self.platforms.items() if creds.is_valid()]
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if feature is enabled."""
        return self.features.get(feature, False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {}
        
        # Basic info
        for field_name in ["app_name", "description", "author", "website_url", "github_url", 
                          "contact_email", "company", "location"]:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
        
        # Platform credentials
        result["platforms"] = {
            platform: creds.to_dict() 
            for platform, creds in self.platforms.items()
        }
        
        # AI configuration
        if self.ai:
            result["ai"] = self.ai.to_dict()
        
        # Notifications
        result["notifications"] = self.notifications.to_dict()
        
        # Features and defaults
        result["features"] = self.features
        result["defaults"] = self.defaults
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AetherPostConfig':
        """Create from dictionary."""
        # Extract platform credentials
        platforms = {}
        for platform_name, creds_data in data.get("platforms", {}).items():
            creds_data["platform"] = platform_name
            platforms[platform_name] = PlatformCredentials.from_dict(creds_data)
        
        # Extract AI config
        ai_config = None
        if "ai" in data:
            ai_config = AIProviderConfig.from_dict(data["ai"])
        
        # Extract notifications
        notifications = NotificationConfig.from_dict(data.get("notifications", {}))
        
        return cls(
            app_name=data.get("app_name", "AetherPost"),
            description=data.get("description", "Social media automation for developers"),
            author=data.get("author", "AetherPost Team"),
            website_url=data.get("website_url"),
            github_url=data.get("github_url"),
            contact_email=data.get("contact_email"),
            company=data.get("company"),
            location=data.get("location"),
            platforms=platforms,
            ai=ai_config,
            notifications=notifications,
            features=data.get("features", {}),
            defaults=data.get("defaults", {})
        )


class ConfigManager:
    """Unified configuration manager for AetherPost."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.yaml"
        self.credentials_file = self.config_dir / "credentials.yaml"
        
        self._config: Optional[AetherPostConfig] = None
        
        # Load existing configuration
        self.load_config()
    
    def _get_default_config_dir(self) -> Path:
        """Get default configuration directory."""
        if os.getenv("AUTOPROMO_CONFIG_DIR"):
            return Path(os.getenv("AUTOPROMO_CONFIG_DIR"))
        
        # Use user's home directory
        home_dir = Path.home()
        return home_dir / ".aetherpost"
    
    @property
    def config(self) -> AetherPostConfig:
        """Get current configuration."""
        if self._config is None:
            self._config = AetherPostConfig()
        return self._config
    
    def load_config(self) -> OperationResult:
        """Load configuration from files."""
        try:
            # Load main config
            config_data = {}
            if self.config_file.exists():
                config_data = load_config_file(self.config_file, {})
            
            # Load credentials separately
            credentials_data = {}
            if self.credentials_file.exists():
                credentials_data = load_config_file(self.credentials_file, {})
            
            # Merge configurations
            if credentials_data:
                config_data = merge_dictionaries(config_data, {"platforms": credentials_data})
            
            # Create config object
            if config_data:
                self._config = AetherPostConfig.from_dict(config_data)
            else:
                self._config = AetherPostConfig()
            
            logger.info(f"Configuration loaded from {self.config_dir}")
            return OperationResult.success_result("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config = AetherPostConfig()  # Fallback to default
            return OperationResult.error_result(f"Failed to load configuration: {e}")
    
    def save_config(self) -> OperationResult:
        """Save configuration to files."""
        try:
            if not self._config:
                return OperationResult.error_result("No configuration to save")
            
            config_dict = self._config.to_dict()
            
            # Separate credentials from main config
            credentials = config_dict.pop("platforms", {})
            
            # Save main config (without sensitive data)
            save_config_file(config_dict, self.config_file, "yaml")
            
            # Save credentials separately
            if credentials:
                save_config_file(credentials, self.credentials_file, "yaml")
                # Secure the credentials file
                os.chmod(self.credentials_file, 0o600)
            
            logger.info(f"Configuration saved to {self.config_dir}")
            return OperationResult.success_result("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return OperationResult.error_result(f"Failed to save configuration: {e}")
    
    def update_config(self, updates: Dict[str, Any]) -> OperationResult:
        """Update configuration with new values."""
        try:
            if not self._config:
                self._config = AetherPostConfig()
            
            # Update basic fields
            for key, value in updates.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
                elif key == "platforms":
                    # Handle platform updates
                    for platform_name, creds_data in value.items():
                        if isinstance(creds_data, dict):
                            creds_data["platform"] = platform_name
                            creds = PlatformCredentials.from_dict(creds_data)
                            self._config.set_platform_credentials(creds)
                elif key in ["features", "defaults"]:
                    # Merge dictionaries
                    current_dict = getattr(self._config, key, {})
                    current_dict.update(value)
                    setattr(self._config, key, current_dict)
            
            return OperationResult.success_result("Configuration updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return OperationResult.error_result(f"Failed to update configuration: {e}")
    
    def add_platform_credentials(self, platform: Union[str, Platform], 
                                credentials: Dict[str, Any]) -> OperationResult:
        """Add or update platform credentials."""
        try:
            platform_enum = Platform(platform) if isinstance(platform, str) else platform
            
            credentials["platform"] = platform_enum
            creds = PlatformCredentials.from_dict(credentials)
            
            self.config.set_platform_credentials(creds)
            
            return OperationResult.success_result(f"Credentials added for {platform_enum.value}")
            
        except Exception as e:
            logger.error(f"Failed to add platform credentials: {e}")
            return OperationResult.error_result(f"Failed to add credentials: {e}")
    
    def remove_platform_credentials(self, platform: Union[str, Platform]) -> OperationResult:
        """Remove platform credentials."""
        try:
            platform_str = platform.value if isinstance(platform, Platform) else platform
            
            if platform_str in self.config.platforms:
                del self.config.platforms[platform_str]
                return OperationResult.success_result(f"Credentials removed for {platform_str}")
            else:
                return OperationResult.error_result(f"No credentials found for {platform_str}")
                
        except Exception as e:
            logger.error(f"Failed to remove platform credentials: {e}")
            return OperationResult.error_result(f"Failed to remove credentials: {e}")
    
    def configure_ai_provider(self, provider: str, api_key: str, 
                            model: Optional[str] = None, **kwargs) -> OperationResult:
        """Configure AI provider."""
        try:
            ai_config = AIProviderConfig(
                provider=provider,
                api_key=api_key,
                model=model,
                **kwargs
            )
            
            self.config.ai = ai_config
            
            return OperationResult.success_result(f"AI provider {provider} configured")
            
        except Exception as e:
            logger.error(f"Failed to configure AI provider: {e}")
            return OperationResult.error_result(f"Failed to configure AI provider: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate current configuration and return issues."""
        issues = []
        
        if not self.config.app_name:
            issues.append("App name is required")
        
        if not self.config.description:
            issues.append("App description is required")
        
        # Check platform credentials
        configured_platforms = self.config.get_configured_platforms()
        if not configured_platforms:
            issues.append("No platform credentials configured")
        
        # Check AI configuration if enabled
        if self.config.is_feature_enabled("ai_generation"):
            if not self.config.ai or not self.config.ai.is_valid():
                issues.append("AI generation is enabled but no valid AI provider configured")
        
        # Check notification configuration
        if self.config.is_feature_enabled("notifications"):
            if not self.config.notifications.channels:
                issues.append("Notifications enabled but no channels configured")
        
        return issues
    
    def export_config(self, export_path: Path, include_credentials: bool = False) -> OperationResult:
        """Export configuration to file."""
        try:
            config_dict = self.config.to_dict()
            
            if not include_credentials:
                # Remove sensitive data
                if "platforms" in config_dict:
                    for platform_data in config_dict["platforms"].values():
                        for sensitive_key in ["api_key", "api_secret", "access_token", "access_token_secret"]:
                            platform_data.pop(sensitive_key, None)
                
                if "ai" in config_dict:
                    config_dict["ai"].pop("api_key", None)
            
            save_config_file(config_dict, export_path, "yaml")
            
            return OperationResult.success_result(f"Configuration exported to {export_path}")
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return OperationResult.error_result(f"Failed to export configuration: {e}")
    
    def import_config(self, import_path: Path) -> OperationResult:
        """Import configuration from file."""
        try:
            config_data = load_config_file(import_path)
            if not config_data:
                return OperationResult.error_result("No configuration data found in file")
            
            # Backup current config
            backup_config = self._config
            
            try:
                self._config = AetherPostConfig.from_dict(config_data)
                return OperationResult.success_result(f"Configuration imported from {import_path}")
            except Exception as e:
                # Restore backup on failure
                self._config = backup_config
                raise e
                
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return OperationResult.error_result(f"Failed to import configuration: {e}")
    
    def reset_config(self) -> OperationResult:
        """Reset configuration to defaults."""
        try:
            self._config = AetherPostConfig()
            return OperationResult.success_result("Configuration reset to defaults")
            
        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
            return OperationResult.error_result(f"Failed to reset configuration: {e}")


# Global configuration manager instance
config_manager = ConfigManager()