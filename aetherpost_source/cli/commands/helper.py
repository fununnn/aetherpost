"""Helper functions for campaign configuration updates."""

import yaml
from pathlib import Path
from typing import Any, Dict


def update_campaign_frequency(config_file: str, frequency: str):
    """Update the posting frequency in campaign.yaml."""
    
    try:
        config_path = Path(config_file)
        
        # Load existing config
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        else:
            config_data = {}
        
        # Ensure content section exists
        if 'content' not in config_data:
            config_data['content'] = {}
        
        # Update frequency
        config_data['content']['frequency'] = frequency
        
        # Set default posting time if not exists
        if 'posting_time' not in config_data['content']:
            config_data['content']['posting_time'] = "09:00"
        
        # Set default timezone if not exists
        if 'timezone' not in config_data['content']:
            config_data['content']['timezone'] = "UTC"
        
        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return True
        
    except Exception as e:
        print(f"Error updating campaign config: {e}")
        return False


def get_campaign_setting(config_file: str, key_path: str, default: Any = None) -> Any:
    """Get a setting from campaign.yaml using dot notation (e.g., 'content.frequency')."""
    
    try:
        config_path = Path(config_file)
        
        if not config_path.exists():
            return default
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Navigate through nested keys
        keys = key_path.split('.')
        current = config_data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
        
    except Exception:
        return default


def update_campaign_setting(config_file: str, key_path: str, value: Any) -> bool:
    """Update a setting in campaign.yaml using dot notation."""
    
    try:
        config_path = Path(config_file)
        
        # Load existing config
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        else:
            config_data = {}
        
        # Navigate and create nested structure
        keys = key_path.split('.')
        current = config_data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        
        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return True
        
    except Exception as e:
        print(f"Error updating campaign setting {key_path}: {e}")
        return False