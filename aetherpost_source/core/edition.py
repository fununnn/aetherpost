"""Edition management for AetherPost (OSS vs Enterprise)."""

import os
import logging
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EditionType(Enum):
    """AetherPost edition types."""
    OSS = "oss"
    ENTERPRISE = "enterprise"


class EditionManager:
    """Manages edition-specific features and limitations."""
    
    def __init__(self):
        self.edition = self._detect_edition()
        self.features = self._get_edition_features()
        logger.info(f"Running AetherPost {self.edition.value.upper()} edition")
    
    def _detect_edition(self) -> EditionType:
        """Detect current edition based on environment or license."""
        # Check environment variable
        edition_env = os.getenv('AETHERPOST_EDITION', '').lower()
        if edition_env == 'enterprise':
            # In a real implementation, you'd verify license here
            return EditionType.ENTERPRISE
        
        # Check for enterprise license file
        license_file = Path('.aetherpost-enterprise')
        if license_file.exists():
            return EditionType.ENTERPRISE
        
        # Default to OSS
        return EditionType.OSS
    
    def _get_edition_features(self) -> Dict[str, Any]:
        """Get feature configuration based on edition."""
        if self.edition == EditionType.ENTERPRISE:
            return {
                # Platform limits
                'max_platforms': 50,
                'max_posts_per_day': 1000,
                'max_campaigns': 100,
                
                # AI features
                'advanced_ai': True,
                'custom_models': True,
                'ai_optimization': True,
                'viral_prediction': True,
                'autopilot': True,
                
                # Analytics
                'advanced_analytics': True,
                'real_time_monitoring': True,
                'custom_dashboards': True,
                'export_data': True,
                
                # Collaboration
                'team_management': True,
                'approval_workflows': True,
                'audit_logs': True,
                'role_based_access': True,
                
                # Integrations
                'webhook_support': True,
                'api_access': True,
                'serverless_functions': True,
                'monitoring_stack': True,
                
                # Media
                'advanced_media_generation': True,
                'video_generation': True,
                'custom_templates': True,
                
                # Support
                'priority_support': True,
                'sla': True,
            }
        else:  # OSS edition
            return {
                # Platform limits (reasonable for personal/small team use)
                'max_platforms': 3,
                'max_posts_per_day': 50,
                'max_campaigns': 5,
                
                # AI features (basic only)
                'advanced_ai': False,
                'custom_models': False,
                'ai_optimization': False,
                'viral_prediction': False,
                'autopilot': False,
                
                # Analytics (basic only)
                'advanced_analytics': False,
                'real_time_monitoring': False,
                'custom_dashboards': False,
                'export_data': False,
                
                # Collaboration (single user)
                'team_management': False,
                'approval_workflows': False,
                'audit_logs': False,
                'role_based_access': False,
                
                # Integrations (basic)
                'webhook_support': False,
                'api_access': False,
                'serverless_functions': False,
                'monitoring_stack': False,
                
                # Media (basic)
                'advanced_media_generation': False,
                'video_generation': False,
                'custom_templates': False,
                
                # Support (community)
                'priority_support': False,
                'sla': False,
            }
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled in current edition."""
        return self.features.get(feature, False)
    
    def get_limit(self, limit_name: str) -> int:
        """Get numeric limit for current edition."""
        return self.features.get(limit_name, 0)
    
    def require_enterprise(self, feature_name: str) -> None:
        """Raise exception if enterprise feature is accessed in OSS edition."""
        if not self.is_feature_enabled(feature_name):
            raise EnterpriseFeatureError(
                f"'{feature_name}' is an Enterprise feature. "
                f"Upgrade to AetherPost Enterprise to access this functionality. "
                f"Visit https://aetherpost.dev/enterprise for more information."
            )
    
    def get_upgrade_message(self, feature_name: str) -> str:
        """Get user-friendly upgrade message."""
        return (
            f"🔒 '{feature_name}' is available in AetherPost Enterprise.\n"
            f"📈 Unlock advanced features, unlimited usage, and priority support.\n"
            f"🚀 Learn more: https://aetherpost.dev/enterprise"
        )


class EnterpriseFeatureError(Exception):
    """Exception raised when enterprise feature is accessed in OSS edition."""
    pass


# Global edition manager instance
edition_manager = EditionManager()


def is_enterprise() -> bool:
    """Check if running Enterprise edition."""
    return edition_manager.edition == EditionType.ENTERPRISE


def is_feature_enabled(feature: str) -> bool:
    """Check if feature is enabled."""
    return edition_manager.is_feature_enabled(feature)


def require_enterprise(feature: str) -> None:
    """Require Enterprise edition for feature."""
    edition_manager.require_enterprise(feature)


def get_limit(limit: str) -> int:
    """Get numeric limit."""
    return edition_manager.get_limit(limit)


def get_upgrade_message(feature: str) -> str:
    """Get upgrade message."""
    return edition_manager.get_upgrade_message(feature)