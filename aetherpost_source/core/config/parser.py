"""Configuration file parser and validator."""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path

from .models import CampaignConfig, CredentialsConfig
from ..security.encryption import CredentialManager


class SmartConfigParser:
    """Natural language and shorthand config converter."""
    
    def __init__(self):
        self.credential_manager = CredentialManager()
    
    def parse_concept(self, concept: str) -> dict:
        """Generate AI prompt from concept automatically."""
        return {
            "ai_prompt": f"""
            Create an engaging announcement for the following service concept:
            {concept}
            
            - Keep under 140 characters
            - Use a friendly tone
            - Include moderate emoji use
            - Include clear call-to-action
            """
        }
    
    def parse_tone(self, tone: str) -> dict:
        """Convert tone specification to settings."""
        tone_map = {
            "casual": {
                "style": "friendly",
                "emoji_level": "high",
                "formality": "casual"
            },
            "professional": {
                "style": "formal",
                "emoji_level": "none",
                "formality": "business"
            },
            "technical": {
                "style": "technical",
                "emoji_level": "low",
                "formality": "professional"
            }
        }
        return tone_map.get(tone, {"style": "friendly"})
    
    def parse_when(self, when: str) -> dict:
        """Parse natural language time specification."""
        if when in ["now", "immediately"]:
            return {"type": "immediate"}
        elif "weekly" in when or "every week" in when:
            return {"type": "recurring", "interval": "weekly"}
        elif "daily" in when or "every day" in when:
            return {"type": "recurring", "interval": "daily"}
        elif "tomorrow" in when:
            return {"type": "delayed", "delay": "1_day"}
        else:
            return {"type": "immediate"}


class ConfigLoader:
    """Load and validate configuration files."""
    
    def __init__(self, config_dir: str = ".aetherpost"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.parser = SmartConfigParser()
    
    def load_campaign_config(self, file_path: str = "campaign.yaml") -> CampaignConfig:
        """Load campaign configuration from YAML file."""
        config_path = Path(file_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Campaign config not found: {file_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        # Process smart configurations
        if 'concept' in raw_config and 'content' not in raw_config:
            raw_config['content'] = self.parser.parse_concept(raw_config['concept'])
        
        # Handle root-level style and action (from design spec) 
        self._normalize_config_structure(raw_config)
        
        return CampaignConfig(**raw_config)
    
    def save_campaign_config(self, config: CampaignConfig, file_path: str = "campaign.yaml"):
        """Save campaign configuration to YAML file."""
        config_dict = config.dict(exclude_none=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
    
    def load_credentials(self) -> CredentialsConfig:
        """Load encrypted credentials."""
        creds_file = self.config_dir / "credentials.enc"
        
        if not creds_file.exists():
            return CredentialsConfig()
        
        try:
            with open(creds_file, 'r') as f:
                encrypted_data = f.read()
            
            decrypted = self.parser.credential_manager.decrypt_credentials(encrypted_data)
            return CredentialsConfig(**decrypted)
        except Exception as e:
            raise ValueError(f"Failed to load credentials: {e}")
    
    def save_credentials(self, credentials: CredentialsConfig):
        """Save encrypted credentials."""
        creds_dict = credentials.dict(exclude_none=True)
        encrypted = self.parser.credential_manager.encrypt_credentials(creds_dict)
        
        creds_file = self.config_dir / "credentials.enc"
        with open(creds_file, 'w') as f:
            f.write(encrypted)
    
    def validate_config(self, config: CampaignConfig) -> List[str]:
        """Validate campaign configuration with helpful suggestions."""
        issues = []
        
        # Required fields validation
        if not config.name or len(config.name.strip()) == 0:
            issues.append("Campaign name is required. Example: 'my-awesome-app'")
        
        if not config.concept or len(config.concept.strip()) == 0:
            issues.append("Campaign concept/description is required. Example: 'AI-powered task manager that learns your habits'")
        
        if not config.platforms or len(config.platforms) == 0:
            issues.append("At least one platform must be specified. Available: twitter, bluesky, mastodon")
        
        # Validate platform names with suggestions
        valid_platforms = ["twitter", "bluesky", "mastodon", "linkedin"]
        for platform in config.platforms:
            if platform not in valid_platforms:
                # Suggest similar platform names
                suggestions = self._suggest_platform(platform, valid_platforms)
                suggestion_text = f" Did you mean: {suggestions}?" if suggestions else ""
                issues.append(f"Unknown platform: '{platform}'.{suggestion_text} Valid platforms: {', '.join(valid_platforms)}")
        
        # Content validation
        if config.content:
            if config.content.style and config.content.style not in ["casual", "professional", "technical", "humorous"]:
                issues.append(f"Invalid style: '{config.content.style}'. Use: casual, professional, technical, or humorous")
            
            if config.content.max_length and config.content.max_length > 2000:
                issues.append("Content max_length should not exceed 2000 characters")
        
        # URL validation
        if config.url and not (config.url.startswith('http://') or config.url.startswith('https://')):
            issues.append("URL should start with http:// or https://")
        
        return issues
    
    def _suggest_platform(self, invalid_platform: str, valid_platforms: List[str]) -> str:
        """Suggest similar platform names."""
        invalid_lower = invalid_platform.lower()
        
        # Simple fuzzy matching
        suggestions = []
        for platform in valid_platforms:
            if invalid_lower in platform or platform in invalid_lower:
                suggestions.append(platform)
            elif abs(len(invalid_lower) - len(platform)) <= 2:
                # Similar length platforms
                differences = sum(1 for a, b in zip(invalid_lower, platform) if a != b)
                if differences <= 2:
                    suggestions.append(platform)
        
        return ', '.join(suggestions) if suggestions else ""
    
    def _normalize_config_structure(self, raw_config: dict):
        """Normalize config structure to handle design spec root-level fields."""
        # Ensure content section exists
        if 'content' not in raw_config:
            raw_config['content'] = {}
        
        # Move root-level style and action to content section
        if 'style' in raw_config:
            raw_config['content']['style'] = raw_config.pop('style')
        
        if 'action' in raw_config:
            raw_config['content']['action'] = raw_config.pop('action')
        
        # Handle other root-level content fields from design spec
        if 'hashtags' in raw_config:
            raw_config['content']['hashtags'] = raw_config.pop('hashtags')
        
        if 'max_length' in raw_config:
            raw_config['content']['max_length'] = raw_config.pop('max_length')
    
    def generate_template(self, template_type: str = "basic") -> str:
        """Generate campaign.yaml template."""
        if template_type == "basic":
            return '''# ========================================
#  AetherPost Campaign Configuration
# ========================================
# 💡 Fill in only what you need. Delete unused lines to keep it minimal.

# Your app/service details
name: ""              # e.g. my-awesome-app
concept: ""           # e.g. AI-powered task manager that learns your habits
url: ""               # e.g. https://myapp.com

# Where to post (delete unused platforms)
platforms:
  - twitter           
  - bluesky          
  # - mastodon       # Uncomment to enable

# How to promote
style: ""            # casual / professional / technical / humorous
action: ""           # e.g. Try it free! / Learn more / Get started

# When to post (leave empty for immediate)
schedule: ""         # now / 2025-06-14 10:00 / every monday

# Visual content (leave empty for text-only)
image: ""            # generate / ./screenshot.png / none

# Advanced options (optional)
# ========================================
# hashtags: ["opensource", "AI", "productivity"]
# 
# variants:
#   - action: "Try it now!"
#   - action: "Start free"
#
# analytics: true'''
        
        elif template_type == "minimal":
            return '''# Minimum viable config (3 lines)
name: "my-app"
concept: "Brief description of your app"
platforms: [twitter]'''
        
        else:
            raise ValueError(f"Unknown template type: {template_type}")
    
    def validate_config(self, config: CampaignConfig) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check required fields
        if not config.name:
            issues.append("Campaign name is required")
        
        if not config.concept:
            issues.append("Concept description is required")
        
        if not config.platforms:
            issues.append("At least one platform must be specified")
        
        # Validate platform-specific requirements
        for platform in config.platforms:
            if platform == "twitter" and not config.content.max_length <= 280:
                issues.append("Twitter posts must be 280 characters or less")
        
        return issues