"""Unified configuration system for AetherPost."""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from ..exceptions import ConfigurationError, ErrorCode, create_user_friendly_error


class ConfigSource(Enum):
    """Configuration source types."""
    FILE = "file"
    ENVIRONMENT = "environment"
    DEFAULT = "default"
    RUNTIME = "runtime"


@dataclass
class PlatformCredentials:
    """Platform-specific credentials."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    access_token_secret: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if credentials are valid for basic operations."""
        # At minimum, we need an API key or access token
        return bool(self.api_key or self.access_token)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AIProviderConfig:
    """AI provider configuration."""
    provider: str = "openai"  # openai, anthropic, both
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def is_valid(self) -> bool:
        """Check if AI config is valid."""
        return bool(self.api_key and self.provider)


@dataclass
class AutomationSettings:
    """Automation and scheduling settings."""
    auto_post: bool = False
    schedule_enabled: bool = False
    timezone: str = "UTC"
    default_frequency: str = "daily"
    quiet_hours_start: str = "23:00"
    quiet_hours_end: str = "07:00"
    weekend_posting: bool = True


@dataclass
class SecuritySettings:
    """Security and privacy settings."""
    encrypt_credentials: bool = True
    audit_log_enabled: bool = True
    rate_limit_strategy: str = "conservative"  # aggressive, conservative, adaptive
    backup_enabled: bool = True
    backup_retention_days: int = 30


@dataclass
class UnifiedConfig:
    """Unified configuration for AetherPost."""
    
    # Project metadata
    project_name: str = "autopromo-project"
    version: str = "1.0.0"
    description: str = ""
    
    # Platform credentials
    platforms: Dict[str, PlatformCredentials] = None
    
    # AI configuration
    ai: AIProviderConfig = None
    
    # Automation settings
    automation: AutomationSettings = None
    
    # Security settings
    security: SecuritySettings = None
    
    # Runtime settings
    debug: bool = False
    verbose: bool = False
    dry_run: bool = False
    
    def __post_init__(self):
        """Initialize default values."""
        if self.platforms is None:
            self.platforms = {}
        if self.ai is None:
            self.ai = AIProviderConfig()
        if self.automation is None:
            self.automation = AutomationSettings()
        if self.security is None:
            self.security = SecuritySettings()
    
    def get_platform_credentials(self, platform: str) -> Optional[PlatformCredentials]:
        """Get credentials for a specific platform."""
        return self.platforms.get(platform.lower())
    
    def set_platform_credentials(self, platform: str, credentials: PlatformCredentials):
        """Set credentials for a platform."""
        self.platforms[platform.lower()] = credentials
    
    def get_configured_platforms(self) -> List[str]:
        """Get list of configured platforms with valid credentials."""
        return [
            platform for platform, creds in self.platforms.items()
            if creds and creds.is_valid()
        ]
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check if at least one platform is configured
        if not self.get_configured_platforms():
            issues.append("No platforms configured with valid credentials")
        
        # Check AI configuration
        if not self.ai.is_valid():
            issues.append("AI provider not properly configured")
        
        # Check project name
        if not self.project_name or not self.project_name.strip():
            issues.append("Project name is required")
        
        return issues


class ConfigManager:
    """Manages unified configuration with multiple sources."""
    
    CONFIG_DIRS = [
        ".aetherpost",
        os.path.expanduser("~/.aetherpost"),
        "/etc/autopromo"
    ]
    
    CONFIG_FILES = [
        "config.yaml",
        "config.yml", 
        "config.json",
        ".env.aetherpost"
    ]
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else self._find_config_dir()
        self.config_file = self._find_config_file()
        self.env_file = self.config_dir / ".env.aetherpost"
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self._config = self._load_config()
    
    def _find_config_dir(self) -> Path:
        """Find the configuration directory."""
        # Try current directory first
        for dir_name in self.CONFIG_DIRS:
            config_dir = Path(dir_name)
            if config_dir.exists():
                return config_dir
        
        # Create default directory
        default_dir = Path(".aetherpost")
        default_dir.mkdir(exist_ok=True)
        return default_dir
    
    def _find_config_file(self) -> Optional[Path]:
        """Find the main configuration file."""
        for filename in self.CONFIG_FILES:
            config_file = self.config_dir / filename
            if config_file.exists():
                return config_file
        return None
    
    def _load_config(self) -> UnifiedConfig:
        """Load configuration from all sources."""
        config_data = {}
        
        # 1. Load defaults
        config_data.update(self._load_defaults())
        
        # 2. Load from file
        if self.config_file:
            config_data.update(self._load_from_file(self.config_file))
        
        # 3. Load from environment file
        if self.env_file.exists():
            config_data.update(self._load_from_env_file(self.env_file))
        
        # 4. Load from environment variables
        config_data.update(self._load_from_environment())
        
        # Convert to UnifiedConfig
        return self._dict_to_config(config_data)
    
    def _load_defaults(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            "project_name": "autopromo-project",
            "version": "1.0.0",
            "ai": {
                "provider": "openai",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "automation": {
                "auto_post": False,
                "timezone": "UTC",
                "default_frequency": "daily"
            },
            "security": {
                "encrypt_credentials": True,
                "audit_log_enabled": True,
                "rate_limit_strategy": "conservative"
            }
        }
    
    def _load_from_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif file_path.suffix == '.json':
                    return json.load(f)
                else:
                    return {}
        except Exception as e:
            self.logger.warning(f"Failed to load config from {file_path}: {e}")
            return {}
    
    def _load_from_env_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from .env file."""
        config_data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        # Parse platform credentials
                        if key.startswith('AUTOPROMO_'):
                            self._parse_env_var(config_data, key, value)
        
        except Exception as e:
            self.logger.warning(f"Failed to load env file {file_path}: {e}")
        
        return config_data
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config_data = {}
        
        for key, value in os.environ.items():
            if key.startswith('AUTOPROMO_'):
                self._parse_env_var(config_data, key, value)
        
        return config_data
    
    def _parse_env_var(self, config_data: Dict[str, Any], key: str, value: str):
        """Parse environment variable into config structure."""
        # Remove AUTOPROMO_ prefix
        key = key[10:]  # len('AUTOPROMO_') = 10
        
        # Platform credentials
        if key.startswith('TWITTER_'):
            platform_key = key[8:]  # Remove 'TWITTER_'
            self._set_nested_value(config_data, f"platforms.twitter.{platform_key.lower()}", value)
        elif key.startswith('INSTAGRAM_'):
            platform_key = key[10:]  # Remove 'INSTAGRAM_'
            self._set_nested_value(config_data, f"platforms.instagram.{platform_key.lower()}", value)
        elif key.startswith('YOUTUBE_'):
            platform_key = key[8:]  # Remove 'YOUTUBE_'
            self._set_nested_value(config_data, f"platforms.youtube.{platform_key.lower()}", value)
        elif key.startswith('AI_'):
            ai_key = key[3:]  # Remove 'AI_'
            self._set_nested_value(config_data, f"ai.{ai_key.lower()}", value)
        else:
            # General configuration
            self._set_nested_value(config_data, key.lower(), value)
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: str):
        """Set nested dictionary value using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert value to appropriate type
        final_key = keys[-1]
        if value.lower() in ('true', 'false'):
            current[final_key] = value.lower() == 'true'
        elif value.isdigit():
            current[final_key] = int(value)
        elif value.replace('.', '').isdigit():
            current[final_key] = float(value)
        else:
            current[final_key] = value
    
    def _dict_to_config(self, data: Dict[str, Any]) -> UnifiedConfig:
        """Convert dictionary to UnifiedConfig object."""
        
        # Extract platforms
        platforms = {}
        platforms_data = data.get('platforms', {})
        for platform_name, platform_data in platforms_data.items():
            if isinstance(platform_data, dict):
                platforms[platform_name] = PlatformCredentials(**platform_data)
        
        # Extract AI config
        ai_data = data.get('ai', {})
        ai_config = AIProviderConfig(**ai_data)
        
        # Extract automation settings
        automation_data = data.get('automation', {})
        automation = AutomationSettings(**automation_data)
        
        # Extract security settings
        security_data = data.get('security', {})
        security = SecuritySettings(**security_data)
        
        # Create unified config
        config = UnifiedConfig(
            project_name=data.get('project_name', 'autopromo-project'),
            version=data.get('version', '1.0.0'),
            description=data.get('description', ''),
            platforms=platforms,
            ai=ai_config,
            automation=automation,
            security=security,
            debug=data.get('debug', False),
            verbose=data.get('verbose', False),
            dry_run=data.get('dry_run', False)
        )
        
        return config
    
    def save_config(self, config: Optional[UnifiedConfig] = None):
        """Save configuration to file."""
        if config:
            self._config = config
        
        config_file = self.config_dir / "config.yaml"
        
        # Convert config to dictionary
        config_dict = {
            "project_name": self._config.project_name,
            "version": self._config.version,
            "description": self._config.description,
            "ai": asdict(self._config.ai),
            "automation": asdict(self._config.automation),
            "security": asdict(self._config.security),
            "debug": self._config.debug,
            "verbose": self._config.verbose
        }
        
        # Save platforms to separate env file (for security)
        self._save_credentials()
        
        # Save main config
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save configuration: {str(e)}",
                error_code=ErrorCode.CONFIG_INVALID,
                suggestions=[
                    "Check file permissions",
                    "Ensure directory exists",
                    "Try running with sudo if necessary"
                ]
            )
    
    def _save_credentials(self):
        """Save platform credentials to env file."""
        env_lines = []
        
        env_lines.append("# AetherPost Platform Credentials")
        env_lines.append("# Generated automatically - do not edit manually")
        env_lines.append("")
        
        for platform_name, credentials in self._config.platforms.items():
            if credentials:
                platform_upper = platform_name.upper()
                cred_dict = credentials.to_dict()
                
                for key, value in cred_dict.items():
                    env_key = f"AUTOPROMO_{platform_upper}_{key.upper()}"
                    env_lines.append(f"{env_key}={value}")
                
                env_lines.append("")
        
        # AI credentials
        if self._config.ai.api_key:
            provider_upper = self._config.ai.provider.upper()
            env_lines.append(f"AUTOPROMO_AI_PROVIDER={self._config.ai.provider}")
            env_lines.append(f"AUTOPROMO_AI_API_KEY={self._config.ai.api_key}")
            if self._config.ai.model:
                env_lines.append(f"AUTOPROMO_AI_MODEL={self._config.ai.model}")
        
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_lines))
            
            # Set secure permissions
            os.chmod(self.env_file, 0o600)
            
        except Exception as e:
            self.logger.warning(f"Failed to save credentials: {e}")
    
    @property
    def config(self) -> UnifiedConfig:
        """Get current configuration."""
        return self._config
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        # Apply updates to current config
        updated_dict = asdict(self._config)
        self._deep_update(updated_dict, updates)
        
        # Convert back to config object
        self._config = self._dict_to_config(updated_dict)
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep update dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def validate_config(self) -> List[str]:
        """Validate current configuration."""
        return self._config.validate()
    
    def create_template(self, template_type: str = "basic") -> str:
        """Create configuration template."""
        
        templates = {
            "basic": {
                "project_name": "my-autopromo-project",
                "description": "My social media automation project",
                "ai": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.7
                },
                "automation": {
                    "auto_post": False,
                    "default_frequency": "daily"
                }
            },
            "advanced": {
                "project_name": "enterprise-autopromo",
                "description": "Enterprise social media automation",
                "ai": {
                    "provider": "both",
                    "model": "gpt-4",
                    "temperature": 0.5,
                    "max_tokens": 2000
                },
                "automation": {
                    "auto_post": True,
                    "schedule_enabled": True,
                    "default_frequency": "hourly",
                    "weekend_posting": False
                },
                "security": {
                    "encrypt_credentials": True,
                    "audit_log_enabled": True,
                    "rate_limit_strategy": "adaptive"
                }
            }
        }
        
        template = templates.get(template_type, templates["basic"])
        return yaml.dump(template, default_flow_style=False, indent=2)


# Global config manager instance
config_manager = ConfigManager()